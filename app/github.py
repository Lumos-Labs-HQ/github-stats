import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

REST_ENDPOINT = "https://api.github.com"

# No-auth contribution data — open-source scraper that reads GitHub profiles
# https://github.com/grubersjoe/github-contributions-api
CONTRIB_API = "https://github-contributions-api.jogruber.de/v4/{username}"

# Fallback: GitHub's own contribution SVG endpoint
GITHUB_CONTRIB_SVG = "https://github.com/users/{username}/contributions"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; github-stats-bot/1.0)",
    "Accept": "application/json, text/html",
}

# ---------------------------------------------------------------------------
# HTTP helper with retry + backoff
# ---------------------------------------------------------------------------

async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: Optional[dict] = None,
    max_attempts: int = 3,
) -> httpx.Response:
    """GET with exponential backoff retry on 5xx and network errors."""
    delay = 1.0
    last_exc: Optional[Exception] = None

    for attempt in range(max_attempts):
        try:
            response = await client.get(
                url,
                params=params,
                headers=_HEADERS,
                timeout=15.0,
                follow_redirects=True,
            )

            if response.status_code >= 500:
                logger.warning(
                    "HTTP %s from %s, retrying in %.0fs (attempt %d/%d)",
                    response.status_code, url, delay, attempt + 1, max_attempts,
                )
                await asyncio.sleep(delay)
                delay *= 2
                continue

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", str(int(delay))))
                logger.warning("Rate limited, retrying in %ds", retry_after)
                await asyncio.sleep(retry_after)
                continue

            return response

        except (httpx.NetworkError, httpx.TimeoutException) as exc:
            last_exc = exc
            logger.warning(
                "Network error attempt %d/%d: %s — retrying in %.0fs",
                attempt + 1, max_attempts, exc, delay,
            )
            await asyncio.sleep(delay)
            delay *= 2

    raise last_exc or RuntimeError(f"All retry attempts failed for {url}")


# ---------------------------------------------------------------------------
# Contribution data
# ---------------------------------------------------------------------------

async def _fetch_contributions_from_api(username: str) -> Optional[list]:
    """
    Primary: fetch from github-contributions-api.jogruber.de
    Returns: list of {"date": "YYYY-MM-DD", "count": N} or None on failure.
    """
    url = CONTRIB_API.format(username=username)
    try:
        async with httpx.AsyncClient() as client:
            response = await _get_with_retry(client, url, params={"y": "all"})
        if response.status_code != 200:
            return None
        data = response.json()
        return [
            {"date": c["date"], "count": c["count"]}
            for c in data.get("contributions", [])
        ]
    except Exception as e:
        logger.warning("Contributions API failed: %s", e)
        return None


def _parse_contributions_svg(html: str) -> list:
    """
    Fallback: parse GitHub's contribution SVG HTML fragment.
    Handles both <rect ... data-date="..." data-count="..." /> and </rect> forms.
    """
    rect_re = re.compile(r"<rect\b([^>]*?)(?:/>|></rect>|>)", re.DOTALL)
    date_re = re.compile(r'data-date="([0-9]{4}-[0-9]{2}-[0-9]{2})"')
    count_re = re.compile(r'data-count="(\d+)"')

    days = []
    for attrs in rect_re.findall(html):
        date_m = date_re.search(attrs)
        count_m = count_re.search(attrs)
        if date_m and count_m:
            days.append({
                "date": date_m.group(1),
                "count": int(count_m.group(1)),
            })
    return days


async def _fetch_contributions_from_github(username: str) -> Optional[list]:
    """
    Fallback: fetch GitHub's contribution SVG directly and parse it.
    Returns: list of {"date": "YYYY-MM-DD", "count": N} or None on failure.
    """
    url = GITHUB_CONTRIB_SVG.format(username=username)
    try:
        async with httpx.AsyncClient() as client:
            response = await _get_with_retry(client, url)
        if response.status_code == 404:
            raise ValueError(f"GitHub user '{username}' not found")
        if response.status_code != 200:
            return None
        days = _parse_contributions_svg(response.text)
        return days if days else None
    except ValueError:
        raise
    except Exception as e:
        logger.warning("GitHub contribution SVG fallback failed: %s", e)
        return None


async def _fetch_contributions(username: str) -> dict:
    """
    Fetch contribution calendar. Tries the contributions API first,
    falls back to parsing GitHub's SVG endpoint directly.
    """
    days = await _fetch_contributions_from_api(username)

    if not days:
        logger.info("Contributions API returned no data, trying GitHub SVG fallback")
        days = await _fetch_contributions_from_github(username)

    if not days:
        logger.error("All contribution sources failed for %s", username)
        days = []

    total = sum(d["count"] for d in days)
    return {
        "total_contributions": total,
        "restricted_count": 0,
        "days": days,
    }


# ---------------------------------------------------------------------------
# Profile stats (REST API — unauthenticated, 60 req/hr)
# ---------------------------------------------------------------------------

async def _fetch_profile(username: str) -> dict:
    """Fetch user profile and repo stats via GitHub REST API (no auth required)."""
    async with httpx.AsyncClient() as client:
        user_task = asyncio.create_task(
            _get_with_retry(client, f"{REST_ENDPOINT}/users/{username}")
        )
        repos_task = asyncio.create_task(
            _get_with_retry(
                client,
                f"{REST_ENDPOINT}/users/{username}/repos",
                params={"per_page": 100, "type": "owner", "sort": "updated"},
            )
        )
        user_resp, repos_resp = await asyncio.gather(user_task, repos_task)

    user_resp.raise_for_status()
    repos_resp.raise_for_status()

    user = user_resp.json()
    repos = repos_resp.json()

    total_stars = sum(r.get("stargazers_count", 0) for r in repos if not r.get("fork"))

    lang_counts: dict = {}
    for repo in repos:
        if not repo.get("fork") and repo.get("language"):
            lang = repo["language"]
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    top_language = max(lang_counts, key=lang_counts.get) if lang_counts else None

    return {
        "public_repos": user.get("public_repos", 0),
        "total_stars": total_stars,
        "followers": user.get("followers", 0),
        "top_language": top_language,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_github_stats(
    username: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    two_year: bool = False,
) -> dict:
    """
    Fetch GitHub stats for a user — no authentication token required.

    Data sources (all public, no token):
    - github-contributions-api.jogruber.de  → contribution calendar (primary)
    - github.com/users/{username}/contributions → contribution SVG (fallback)
    - api.github.com/users/{username}        → profile info
    - api.github.com/users/{username}/repos  → repos/stars/languages

    from_date / to_date filtering is applied in Python after fetching all data.
    """
    contrib_task = asyncio.create_task(_fetch_contributions(username))
    profile_task = asyncio.create_task(_fetch_profile(username))
    contrib_data, profile_data = await asyncio.gather(contrib_task, profile_task)

    # Apply date range filter if requested
    if from_date or to_date:
        filtered_days = _filter_days(contrib_data["days"], from_date, to_date)
        contrib_data = {
            "total_contributions": sum(d["count"] for d in filtered_days),
            "restricted_count": 0,
            "days": filtered_days,
        }

    return {**contrib_data, **profile_data}


def _filter_days(days: list, from_date: Optional[str], to_date: Optional[str]) -> list:
    """Filter contribution days to the given date range."""
    from_d = from_date[:10] if from_date else None  # "YYYY-MM-DD"
    to_d = to_date[:10] if to_date else None
    return [
        d for d in days
        if (from_d is None or d["date"] >= from_d)
        and (to_d is None or d["date"] < to_d)
    ]
