from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
import os

from fastapi import FastAPI, Response
from dotenv import load_dotenv

from app.github import fetch_github_stats
from app.services.stats import calculate_streaks
from app.services.cache import CacheService
from app.services.svg import generate_stats_svg, generate_error_svg

load_dotenv()

cache_service = CacheService(os.getenv("REDIS_URL", "redis://localhost:6379"))


def _month_year_range(month: int, year: int) -> tuple:
    """Return (from_date, to_date) ISO 8601 UTC strings for a calendar month."""
    first_day = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        last_day = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        last_day = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    fmt = lambda dt: dt.isoformat().replace("+00:00", "Z")
    return fmt(first_day), fmt(last_day)


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


@app.get("/stats")
async def get_stats(username: str, month: Optional[int] = None, year: Optional[int] = None):
    """Generate GitHub stats SVG card."""
    cache_key = f"{username}_{year}_{month}" if (month and year) else username

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
    period_label = f" ({year}-{month:02d})" if (month and year) else ""

    svg = generate_stats_svg(
        username=username + period_label,
        total_contributions=stats_data["total_contributions"],
        current_streak=streaks["current_streak"],
        longest_streak=streaks["longest_streak"],
        public_repos=stats_data.get("public_repos", 0),
        total_stars=stats_data.get("total_stars", 0),
        top_language=stats_data.get("top_language"),
        first_contribution=streaks.get("first_contribution"),
        current_streak_start=streaks.get("current_streak_start"),
        current_streak_end=streaks.get("current_streak_end"),
        longest_streak_start=streaks.get("longest_streak_start"),
        longest_streak_end=streaks.get("longest_streak_end"),
    )

    await cache_service.set_stats(cache_key, {"svg": svg}, ttl=1800)  # 30 min
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/debug")
async def debug_stats(username: str, month: Optional[int] = None, year: Optional[int] = None):
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
        },
        "rate_limit_remaining": stats_data.get("rate_limit_remaining"),
    }
