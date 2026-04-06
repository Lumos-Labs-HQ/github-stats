import asyncio
import logging
import os
import re
from typing import Optional
from dotenv import load_dotenv

import httpx

load_dotenv()
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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

_EVENT_LABELS = {
    "PushEvent": "Pushes",
    "PullRequestEvent": "Pull Requests",
    "IssuesEvent": "Issues",
    "IssueCommentEvent": "Comments",
    "CommitCommentEvent": "Comments",
    "CreateEvent": "Creates",
    "WatchEvent": "Stars",
    "ReleaseEvent": "Releases",
    "ForkEvent": "Forks",
    "PullRequestReviewEvent": "Reviews",
    "PullRequestReviewCommentEvent": "Comments",
}


def _auth_headers(accept: str = "application/json") -> dict:
    headers = {
        "User-Agent": _HEADERS["User-Agent"],
        "Accept": accept,
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def _safe_int(value) -> int:
    return int(value or 0)


def _iso_date(value: Optional[str]) -> str:
    return value[:10] if value else ""


def _event_label(event_type: Optional[str]) -> str:
    if not event_type:
        return "Activity"
    return _EVENT_LABELS.get(event_type, event_type.replace("Event", ""))


def _normalize_repo(repo: dict) -> dict:
    return {
        "name": repo.get("name") or "unknown",
        "full_name": repo.get("full_name") or repo.get("name") or "unknown",
        "description": repo.get("description") or "",
        "language": repo.get("language") or "Unspecified",
        "stars": _safe_int(repo.get("stargazers_count")),
        "forks": _safe_int(repo.get("forks_count")),
        "url": repo.get("html_url") or "",
        "updated_at": _iso_date(repo.get("pushed_at") or repo.get("updated_at")),
    }


def _summarize_languages(repos: list[dict], limit: int = 5) -> list[dict]:
    aggregates: dict[str, dict] = {}

    for repo in repos:
        if repo.get("fork") or not repo.get("language"):
            continue

        language = repo["language"]
        item = aggregates.setdefault(
            language,
            {
                "name": language,
                "repos": 0,
                "stars": 0,
                "forks": 0,
            },
        )
        item["repos"] += 1
        item["stars"] += _safe_int(repo.get("stargazers_count"))
        item["forks"] += _safe_int(repo.get("forks_count"))

    total_repos = sum(item["repos"] for item in aggregates.values())
    ranked = sorted(
        aggregates.values(),
        key=lambda item: (item["repos"], item["stars"], item["name"].lower()),
        reverse=True,
    )

    for item in ranked:
        item["share"] = (
            round((item["repos"] / total_repos) * 100, 1) if total_repos else 0.0
        )

    return ranked[:limit]


def _summarize_featured_repositories(repos: list[dict], limit: int = 4) -> list[dict]:
    candidates = [
        _normalize_repo(repo)
        for repo in repos
        if not repo.get("fork") and not repo.get("archived")
    ]

    candidates.sort(
        key=lambda repo: (
            repo["stars"],
            repo["forks"],
            repo["updated_at"],
            repo["name"].lower(),
        ),
        reverse=True,
    )
    return candidates[:limit]


def _summarize_recent_activity(events: list[dict], limit: int = 4) -> dict:
    type_counts: dict[str, int] = {}
    repo_counts: dict[str, dict] = {}

    for event in events:
        label = _event_label(event.get("type"))
        type_counts[label] = type_counts.get(label, 0) + 1

        repo_name = ((event.get("repo") or {}).get("name") or "").strip()
        if not repo_name:
            continue

        repo_entry = repo_counts.setdefault(
            repo_name,
            {
                "name": repo_name.split("/")[-1],
                "full_name": repo_name,
                "count": 0,
                "types": set(),
                "last_seen": "",
                "url": f"https://github.com/{repo_name}",
            },
        )
        repo_entry["count"] += 1
        repo_entry["types"].add(label)
        last_seen = _iso_date(event.get("created_at"))
        if last_seen > repo_entry["last_seen"]:
            repo_entry["last_seen"] = last_seen

    activity_types = [
        {"name": name, "count": count}
        for name, count in sorted(
            type_counts.items(),
        key=lambda item: (item[1], item[0].lower()),
        reverse=True,
    )[:5]
    ]

    activity_repositories = []
    for repo in sorted(
        repo_counts.values(),
        key=lambda item: (item["count"], item["last_seen"], item["full_name"].lower()),
        reverse=True,
    )[:limit]:
        activity_repositories.append(
            {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "count": repo["count"],
                "types": ", ".join(sorted(repo["types"])),
                "last_seen": repo["last_seen"],
                "url": repo["url"],
            }
        )

    return {
        "recent_events": len(events),
        "active_repos": len(repo_counts),
        "dominant_event": activity_types[0]["name"] if activity_types else None,
        "activity_types": activity_types,
        "activity_counts": type_counts,
        "activity_repositories": activity_repositories,
    }


# ---------------------------------------------------------------------------
# HTTP helper with retry + backoff
# ---------------------------------------------------------------------------


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
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
                headers=headers or _HEADERS,
                timeout=15.0,
                follow_redirects=True,
            )

            if response.status_code >= 500:
                logger.warning(
                    "HTTP %s from %s, retrying in %.0fs (attempt %d/%d)",
                    response.status_code,
                    url,
                    delay,
                    attempt + 1,
                    max_attempts,
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
                attempt + 1,
                max_attempts,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
            delay *= 2

    raise last_exc or RuntimeError(f"All retry attempts failed for {url}")


# ---------------------------------------------------------------------------
# Contribution data
# ---------------------------------------------------------------------------


async def _fetch_contributions_from_graphql(username: str) -> Optional[dict]:
    """Optional primary source when token exists: includes restricted/private counts."""
    if not GITHUB_TOKEN:
        return None

    query = """
    query($login: String!) {
        user(login: $login) {
            contributionsCollection {
                restrictedContributionsCount
                contributionCalendar {
                    totalContributions
                    weeks {
                        contributionDays {
                            date
                            contributionCount
                        }
                    }
                }
            }
        }
    }
    """

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": {"login": username}},
                headers=_auth_headers("application/json"),
                timeout=15.0,
            )

        if response.status_code != 200:
            return None

        body = response.json()
        user = (body.get("data") or {}).get("user") or {}
        if not user:
            return None

        collection = user.get("contributionsCollection") or {}
        calendar = collection.get("contributionCalendar") or {}

        days = []
        for week in calendar.get("weeks", []):
            for day in week.get("contributionDays", []):
                days.append(
                    {
                        "date": day.get("date"),
                        "count": _safe_int(day.get("contributionCount")),
                    }
                )

        return {
            "total_contributions": _safe_int(calendar.get("totalContributions")),
            "restricted_count": _safe_int(
                collection.get("restrictedContributionsCount")
            ),
            "days": [day for day in days if day["date"]],
        }
    except Exception as exc:
        logger.warning("GraphQL contributions failed: %s", exc)
        return None


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
            {"date": contribution["date"], "count": contribution["count"]}
            for contribution in data.get("contributions", [])
        ]
    except Exception as exc:
        logger.warning("Contributions API failed: %s", exc)
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
            days.append(
                {
                    "date": date_m.group(1),
                    "count": int(count_m.group(1)),
                }
            )
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
    except Exception as exc:
        logger.warning("GitHub contribution SVG fallback failed: %s", exc)
        return None


async def _fetch_contributions(username: str) -> dict:
    """
    Fetch contribution calendar. Tries the contributions API first,
    falls back to parsing GitHub's SVG endpoint directly.
    """
    graphql_data = await _fetch_contributions_from_graphql(username)
    if graphql_data:
        return graphql_data

    days = await _fetch_contributions_from_api(username)

    if not days:
        logger.info("Contributions API returned no data, trying GitHub SVG fallback")
        days = await _fetch_contributions_from_github(username)

    if not days:
        logger.error("All contribution sources failed for %s", username)
        days = []

    total = sum(day["count"] for day in days)
    return {
        "total_contributions": total,
        "restricted_count": 0,
        "days": days,
    }


# ---------------------------------------------------------------------------
# Profile stats (REST API — unauthenticated, 60 req/hr)
# ---------------------------------------------------------------------------


async def _fetch_profile(username: str) -> dict:
    """Fetch user profile and repo stats via GitHub REST API."""
    async with httpx.AsyncClient() as client:
        user_task = asyncio.create_task(
            _get_with_retry(
                client,
                f"{REST_ENDPOINT}/users/{username}",
                headers=_auth_headers(),
            )
        )
        repos_task = asyncio.create_task(
            _get_with_retry(
                client,
                f"{REST_ENDPOINT}/users/{username}/repos",
                params={"per_page": 100, "type": "owner", "sort": "updated"},
                headers=_auth_headers(),
            )
        )
        prs_task = asyncio.create_task(
            _get_with_retry(
                client,
                f"{REST_ENDPOINT}/search/issues",
                params={"q": f"author:{username} type:pr", "per_page": 1},
                headers=_auth_headers(),
            )
        )
        issues_task = asyncio.create_task(
            _get_with_retry(
                client,
                f"{REST_ENDPOINT}/search/issues",
                params={"q": f"author:{username} type:issue", "per_page": 1},
                headers=_auth_headers(),
            )
        )
        events_task = asyncio.create_task(
            _get_with_retry(
                client,
                f"{REST_ENDPOINT}/users/{username}/events/public",
                params={"per_page": 100},
                headers=_auth_headers(),
            )
        )

        (
            user_resp,
            repos_resp,
            prs_resp,
            issues_resp,
            events_resp,
        ) = await asyncio.gather(
            user_task,
            repos_task,
            prs_task,
            issues_task,
            events_task,
        )

    user_resp.raise_for_status()
    repos_resp.raise_for_status()

    user = user_resp.json()
    repos = repos_resp.json() if isinstance(repos_resp.json(), list) else []

    total_prs = (
        _safe_int(prs_resp.json().get("total_count"))
        if prs_resp.status_code == 200
        else 0
    )
    total_issues = (
        _safe_int(issues_resp.json().get("total_count"))
        if issues_resp.status_code == 200
        else 0
    )
    total_stars = sum(
        _safe_int(repo.get("stargazers_count"))
        for repo in repos
        if not repo.get("fork")
    )

    language_breakdown = _summarize_languages(repos)
    featured_repositories = _summarize_featured_repositories(repos)
    top_language = language_breakdown[0]["name"] if language_breakdown else None

    events = (
        events_resp.json()
        if events_resp.status_code == 200 and isinstance(events_resp.json(), list)
        else []
    )
    activity_summary = _summarize_recent_activity(events)

    contributed_to = 0
    if GITHUB_TOKEN:
        gql_query = """
        query($login: String!) {
          user(login: $login) {
            repositoriesContributedTo(
              contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]
              includeUserRepositories: false
            ) {
              totalCount
            }
          }
        }
        """
        try:
            async with httpx.AsyncClient() as gql_client:
                gql_resp = await gql_client.post(
                    "https://api.github.com/graphql",
                    json={"query": gql_query, "variables": {"login": username}},
                    headers=_auth_headers("application/json"),
                    timeout=15.0,
                )
            if gql_resp.status_code == 200:
                body = gql_resp.json()
                contributed_to = _safe_int(
                    (
                        ((body.get("data") or {}).get("user") or {}).get(
                            "repositoriesContributedTo"
                        )
                        or {}
                    ).get("totalCount")
                )
        except Exception as exc:
            logger.warning("GraphQL contributed_to failed: %s", exc)

    if contributed_to == 0:
        contributed_to = activity_summary["active_repos"]

    return {
        "public_repos": _safe_int(user.get("public_repos")),
        "total_stars": total_stars,
        "followers": _safe_int(user.get("followers")),
        "top_language": top_language,
        "total_prs": total_prs,
        "total_issues": total_issues,
        "contributed_to": contributed_to,
        "language_breakdown": language_breakdown,
        "featured_repositories": featured_repositories,
        "recent_events": activity_summary["recent_events"],
        "active_repos": activity_summary["active_repos"],
        "dominant_event": activity_summary["dominant_event"],
        "activity_types": activity_summary["activity_types"],
        "activity_counts": activity_summary["activity_counts"],
        "activity_repositories": activity_summary["activity_repositories"],
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
    _ = two_year
    contrib_task = asyncio.create_task(_fetch_contributions(username))
    profile_task = asyncio.create_task(_fetch_profile(username))
    contrib_data, profile_data = await asyncio.gather(contrib_task, profile_task)

    if from_date or to_date:
        filtered_days = _filter_days(contrib_data["days"], from_date, to_date)
        contrib_data = {
            "total_contributions": sum(day["count"] for day in filtered_days),
            "restricted_count": 0,
            "days": filtered_days,
        }

    return {**contrib_data, **profile_data}


def _filter_days(days: list, from_date: Optional[str], to_date: Optional[str]) -> list:
    """Filter contribution days to the given date range."""
    from_d = from_date[:10] if from_date else None
    to_d = to_date[:10] if to_date else None
    return [
        day
        for day in days
        if (from_d is None or day["date"] >= from_d)
        and (to_d is None or day["date"] < to_d)
    ]
