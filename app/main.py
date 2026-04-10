from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
import os

from fastapi import FastAPI, Response
from dotenv import load_dotenv

from app.github import fetch_github_stats
from app.services.stats import calculate_streaks
from app.services.cache import CacheService
from app.services.svg import (
    generate_stats_svg,
    generate_streak_svg,
    generate_languages_svg,
    generate_repository_svg,
    generate_activity_svg,
    generate_error_svg,
    resolve_card_theme,
    get_available_themes,
)

load_dotenv()

cache_service = CacheService(os.getenv("REDIS_URL", "redis://localhost:6379"))
CARD_VERSION = "v11"


def _month_year_range(month: int, year: int) -> tuple:
    """Return (from_date, to_date) ISO 8601 UTC strings for a calendar month."""
    first_day = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        last_day = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        last_day = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    fmt = lambda dt: dt.isoformat().replace("+00:00", "Z")
    return fmt(first_day), fmt(last_day)


def _cache_key(*parts: object) -> str:
    return "|".join([CARD_VERSION, *[str(part or "") for part in parts]])


def _resolve_colors(
    card_type: str,
    theme: Optional[str],
    stroke: Optional[str],
    background: Optional[str],
    ring: Optional[str],
    fire: Optional[str],
    curr_streak_num: Optional[str],
    curr_streak_label: Optional[str],
    side_nums: Optional[str],
    side_labels: Optional[str],
    dates: Optional[str],
) -> dict:
    return resolve_card_theme(
        card_type=card_type,
        theme=theme,
        stroke=stroke,
        background=background,
        ring=ring,
        fire=fire,
        curr_streak_num=curr_streak_num,
        curr_streak_label=curr_streak_label,
        side_nums=side_nums,
        side_labels=side_labels,
        dates=dates,
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await cache_service.connect()
    yield
    await cache_service.close()


app = FastAPI(
    title="GitHub Stats Service",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/streak")
async def get_streak(
    username: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
    theme: Optional[str] = None,
    stroke: Optional[str] = None,
    background: Optional[str] = None,
    ring: Optional[str] = None,
    fire: Optional[str] = None,
    currStreakNum: Optional[str] = None,
    currStreakLabel: Optional[str] = None,
    sideNums: Optional[str] = None,
    sideLabels: Optional[str] = None,
    dates: Optional[str] = None,
    hide_border: bool = False,
    rounded: bool = False,
):
    """Generate GitHub stats SVG card."""
    cache_key = _cache_key(
        "streak",
        username,
        year,
        month,
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
        hide_border,
        rounded,
    )

    cached = await cache_service.get_stats(cache_key)
    if cached:
        return Response(content=cached["svg"], media_type="image/svg+xml")

    from_date, to_date = None, None
    two_year = True

    if month and year:
        from_date, to_date = _month_year_range(month, year)
        two_year = False  # month view doesn't need cross-year streak

    try:
        stats_data = await fetch_github_stats(
            username, from_date=from_date, to_date=to_date, two_year=two_year
        )
    except Exception:
        cached = await cache_service.get_stats(cache_key)
        if cached:
            return Response(content=cached["svg"], media_type="image/svg+xml")
        return Response(
            content=generate_error_svg("Failed to fetch GitHub data"),
            media_type="image/svg+xml",
        )

    if not stats_data:
        return Response(
            content=generate_error_svg(f"User '{username}' not found"),
            media_type="image/svg+xml",
        )

    streaks = calculate_streaks(stats_data["days"])
    colors = _resolve_colors(
        "streak",
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
    )

    svg = generate_streak_svg(
        username=username,
        total_contributions=stats_data["total_contributions"],
        current_streak=streaks["current_streak"],
        longest_streak=streaks["longest_streak"],
        first_contribution=streaks.get("first_contribution"),
        current_streak_start=streaks.get("current_streak_start"),
        current_streak_end=streaks.get("current_streak_end"),
        longest_streak_start=streaks.get("longest_streak_start"),
        longest_streak_end=streaks.get("longest_streak_end"),
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
    )

    await cache_service.set_stats(cache_key, {"svg": svg}, ttl=1800)  # 30 min
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/stats")
async def get_stats(
    username: str,
    year: Optional[int] = None,
    theme: Optional[str] = None,
    stroke: Optional[str] = None,
    background: Optional[str] = None,
    ring: Optional[str] = None,
    fire: Optional[str] = None,
    currStreakNum: Optional[str] = None,
    currStreakLabel: Optional[str] = None,
    sideNums: Optional[str] = None,
    sideLabels: Optional[str] = None,
    dates: Optional[str] = None,
    hide_border: bool = False,
    rounded: bool = False,
):
    """Generate all GitHub stats SVG card."""
    cache_key = _cache_key(
        "stats",
        username,
        year,
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
        hide_border,
        rounded,
    )

    cached = await cache_service.get_stats(cache_key)
    if cached:
        return Response(content=cached["svg"], media_type="image/svg+xml")

    from_date, to_date = None, None
    if year:
        from_date = f"{year:04d}-01-01T00:00:00Z"
        to_date = f"{year + 1:04d}-01-01T00:00:00Z"

    try:
        stats_data = await fetch_github_stats(
            username,
            from_date=from_date,
            to_date=to_date,
            two_year=False,
        )
    except Exception:
        cached = await cache_service.get_stats(cache_key)
        if cached:
            return Response(content=cached["svg"], media_type="image/svg+xml")
        return Response(
            content=generate_error_svg("Failed to fetch GitHub data"),
            media_type="image/svg+xml",
        )

    if not stats_data:
        return Response(
            content=generate_error_svg(f"User '{username}' not found"),
            media_type="image/svg+xml",
        )

    colors = _resolve_colors(
        "stats",
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
    )

    private_contributions = int(stats_data.get("restricted_count", 0) or 0)
    total_commits = (
        int(stats_data.get("total_contributions", 0) or 0) + private_contributions
    )

    svg = generate_stats_svg(
        username=username,
        total_stars=int(stats_data.get("total_stars", 0) or 0),
        total_commits=total_commits,
        total_prs=int(stats_data.get("total_prs", 0) or 0),
        total_issues=int(stats_data.get("total_issues", 0) or 0),
        followers=int(stats_data.get("followers", 0) or 0),
        commits_year=year,
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
    )

    await cache_service.set_stats(cache_key, {"svg": svg}, ttl=1800)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/languages")
async def get_languages(
    username: str,
    theme: Optional[str] = None,
    stroke: Optional[str] = None,
    background: Optional[str] = None,
    ring: Optional[str] = None,
    fire: Optional[str] = None,
    currStreakNum: Optional[str] = None,
    currStreakLabel: Optional[str] = None,
    sideNums: Optional[str] = None,
    sideLabels: Optional[str] = None,
    dates: Optional[str] = None,
    hide_border: bool = False,
    rounded: bool = False,
):
    """Generate language distribution SVG card."""
    cache_key = _cache_key(
        "languages",
        username,
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
        hide_border,
        rounded,
    )

    cached = await cache_service.get_stats(cache_key)
    if cached:
        return Response(content=cached["svg"], media_type="image/svg+xml")

    try:
        stats_data = await fetch_github_stats(username, two_year=False)
    except Exception:
        cached = await cache_service.get_stats(cache_key)
        if cached:
            return Response(content=cached["svg"], media_type="image/svg+xml")
        return Response(
            content=generate_error_svg("Failed to fetch GitHub data"),
            media_type="image/svg+xml",
        )

    if not stats_data:
        return Response(
            content=generate_error_svg(f"User '{username}' not found"),
            media_type="image/svg+xml",
        )

    colors = _resolve_colors(
        "languages",
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
    )
    svg = generate_languages_svg(
        username=username,
        languages=stats_data.get("language_breakdown", []),
        total_repos=int(stats_data.get("public_repos", 0) or 0),
        total_stars=int(stats_data.get("total_stars", 0) or 0),
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
    )

    await cache_service.set_stats(cache_key, {"svg": svg}, ttl=1800)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/repositories")
@app.get("/repos")
async def get_repositories(
    username: str,
    theme: Optional[str] = None,
    stroke: Optional[str] = None,
    background: Optional[str] = None,
    ring: Optional[str] = None,
    fire: Optional[str] = None,
    currStreakNum: Optional[str] = None,
    currStreakLabel: Optional[str] = None,
    sideNums: Optional[str] = None,
    sideLabels: Optional[str] = None,
    dates: Optional[str] = None,
    hide_border: bool = False,
    rounded: bool = False,
):
    """Generate featured repositories SVG card."""
    cache_key = _cache_key(
        "repositories",
        username,
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
        hide_border,
        rounded,
    )

    cached = await cache_service.get_stats(cache_key)
    if cached:
        return Response(content=cached["svg"], media_type="image/svg+xml")

    try:
        stats_data = await fetch_github_stats(username, two_year=False)
    except Exception:
        cached = await cache_service.get_stats(cache_key)
        if cached:
            return Response(content=cached["svg"], media_type="image/svg+xml")
        return Response(
            content=generate_error_svg("Failed to fetch GitHub data"),
            media_type="image/svg+xml",
        )

    if not stats_data:
        return Response(
            content=generate_error_svg(f"User '{username}' not found"),
            media_type="image/svg+xml",
        )

    colors = _resolve_colors(
        "repositories",
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
    )
    svg = generate_repository_svg(
        username=username,
        repositories=stats_data.get("featured_repositories", []),
        total_stars=int(stats_data.get("total_stars", 0) or 0),
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
    )

    await cache_service.set_stats(cache_key, {"svg": svg}, ttl=1800)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/activity")
async def get_activity(
    username: str,
    theme: Optional[str] = None,
    stroke: Optional[str] = None,
    background: Optional[str] = None,
    ring: Optional[str] = None,
    fire: Optional[str] = None,
    currStreakNum: Optional[str] = None,
    currStreakLabel: Optional[str] = None,
    sideNums: Optional[str] = None,
    sideLabels: Optional[str] = None,
    dates: Optional[str] = None,
    hide_border: bool = False,
    rounded: bool = False,
):
    """Generate recent public activity SVG card."""
    cache_key = _cache_key(
        "activity",
        username,
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
        hide_border,
        rounded,
    )

    cached = await cache_service.get_stats(cache_key)
    if cached:
        return Response(content=cached["svg"], media_type="image/svg+xml")

    try:
        stats_data = await fetch_github_stats(username, two_year=False)
    except Exception:
        cached = await cache_service.get_stats(cache_key)
        if cached:
            return Response(content=cached["svg"], media_type="image/svg+xml")
        return Response(
            content=generate_error_svg("Failed to fetch GitHub data"),
            media_type="image/svg+xml",
        )

    if not stats_data:
        return Response(
            content=generate_error_svg(f"User '{username}' not found"),
            media_type="image/svg+xml",
        )

    colors = _resolve_colors(
        "activity",
        theme,
        stroke,
        background,
        ring,
        fire,
        currStreakNum,
        currStreakLabel,
        sideNums,
        sideLabels,
        dates,
    )
    svg = generate_activity_svg(
        username=username,
        recent_events=int(stats_data.get("recent_events", 0) or 0),
        active_repos=int(stats_data.get("active_repos", 0) or 0),
        activity_counts=stats_data.get("activity_counts", {}),
        activity_repositories=stats_data.get("activity_repositories", []),
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
    )

    await cache_service.set_stats(cache_key, {"svg": svg}, ttl=1800)
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/themes")
async def themes():
    return {
        "themes": get_available_themes(),
        "usage": "/stats?username=username&theme=default",
        "custom_colors_example": (
            "/stats?username=username&stroke=FF6F61&background=1E1E2E&ring=FF6F61&"
            "fire=FF6F61&currStreakNum=FF6F61&currStreakLabel=FF6F61&"
            "sideNums=FF6F61&sideLabels=FF6F61&dates=FF6F61&hide_border=true"
        ),
    }


@app.get("/debug")
async def debug_stats(
    username: str, month: Optional[int] = None, year: Optional[int] = None
):
    """Return raw stats data as JSON for debugging."""
    from_date, to_date = None, None
    two_year = True

    if month and year:
        from_date, to_date = _month_year_range(month, year)
        two_year = False

    try:
        stats_data = await fetch_github_stats(
            username, from_date=from_date, to_date=to_date, two_year=two_year
        )
    except Exception as e:
        return {"error": str(e)}

    streaks = calculate_streaks(stats_data["days"])
    days_with_contribs = [d for d in stats_data["days"] if d["count"] > 0]

    return {
        "total_contributions": stats_data["total_contributions"],
        "restricted_contributions": stats_data.get("restricted_count", 0),
        "total_days": len(stats_data["days"]),
        "days_with_contributions": len(days_with_contribs),
        "contributions_by_day": days_with_contribs,
        "date_range": {"from": from_date, "to": to_date},
        "streaks": streaks,
        "profile": {
            "public_repos": stats_data.get("public_repos"),
            "total_stars": stats_data.get("total_stars"),
            "followers": stats_data.get("followers"),
            "top_language": stats_data.get("top_language"),
            "total_prs": stats_data.get("total_prs"),
            "total_issues": stats_data.get("total_issues"),
            "contributed_to": stats_data.get("contributed_to"),
            "language_breakdown": stats_data.get("language_breakdown"),
            "featured_repositories": stats_data.get("featured_repositories"),
            "recent_events": stats_data.get("recent_events"),
            "active_repos": stats_data.get("active_repos"),
            "dominant_event": stats_data.get("dominant_event"),
            "activity_types": stats_data.get("activity_types"),
            "activity_counts": stats_data.get("activity_counts"),
            "activity_repositories": stats_data.get("activity_repositories"),
        },
        "rate_limit_remaining": stats_data.get("rate_limit_remaining"),
    }
