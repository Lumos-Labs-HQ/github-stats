from fastapi import FastAPI, Response
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.github import fetch_github_stats
from app.services.stats import calculate_streaks
from app.services.cache import CacheService
from app.services.svg import generate_stats_svg, generate_error_svg

load_dotenv()

cache_service = CacheService(os.getenv("REDIS_URL", "redis://localhost:6379"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache_service.connect()
    yield
    await cache_service.close()

app = FastAPI(title="GitHub Stats Service", lifespan=lifespan)

@app.get("/stats")
async def get_stats(username: str, month: int = None, year: int = None):
    """Generate GitHub stats SVG card"""
    
    # Build cache key with month/year if provided
    cache_key = f"{username}"
    if month and year:
        cache_key = f"{username}_{year}_{month}"
    
    # Check cache first
    cached = await cache_service.get_stats(cache_key)
    if cached:
        return Response(content=cached["svg"], media_type="image/svg+xml")
    
    # Fetch from GitHub
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        svg = generate_error_svg("GitHub token not configured")
        return Response(content=svg, media_type="image/svg+xml")
    
    try:
        # Calculate date range based on month/year
        from_date = None
        to_date = None
        
        if month and year:
            # Get first and last day of the month
            from datetime import datetime
            first_day = datetime(year, month, 1)
            if month == 12:
                last_day = datetime(year + 1, 1, 1)
            else:
                last_day = datetime(year, month + 1, 1)
            
            from_date = first_day.isoformat() + "Z"
            to_date = last_day.isoformat() + "Z"
        
        stats_data = await fetch_github_stats(username, github_token, from_date=from_date, to_date=to_date)
        
        if not stats_data:
            svg = generate_error_svg(f"User '{username}' not found")
            return Response(content=svg, media_type="image/svg+xml")
        
        # Calculate streaks with optional month/year filter
        # When month/year is specified, we already fetched that range from GitHub
        # So don't filter again in calculate_streaks
        if month and year:
            streaks = calculate_streaks(stats_data["days"], month=None, year=None)
            total_contributions = stats_data["total_contributions"]
        else:
            streaks = calculate_streaks(stats_data["days"], month=None, year=None)
            total_contributions = stats_data["total_contributions"]
        
        # Generate SVG
        period_label = f" ({year}-{month:02d})" if month and year else ""
        svg = generate_stats_svg(
            username=username + period_label,
            total_contributions=total_contributions,
            current_streak=streaks["current_streak"],
            longest_streak=streaks["longest_streak"]
        )
        
        # Cache the result
        await cache_service.set_stats(cache_key, {"svg": svg}, ttl=900)
        
        return Response(content=svg, media_type="image/svg+xml")
        
    except Exception as e:
        # Try to return cached data if available
        cached = await cache_service.get_stats(cache_key)
        if cached:
            return Response(content=cached["svg"], media_type="image/svg+xml")
        
        svg = generate_error_svg("Failed to fetch GitHub data")
        return Response(content=svg, media_type="image/svg+xml")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/debug")
async def debug_stats(username: str, month: int = None, year: int = None):
    """Debug endpoint to see what GitHub returns"""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return {"error": "No token"}
    
    from datetime import datetime
    from_date = None
    to_date = None
    
    if month and year:
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1)
        else:
            last_day = datetime(year, month + 1, 1)
        
        from_date = first_day.isoformat() + "Z"
        to_date = last_day.isoformat() + "Z"
    
    try:
        stats_data = await fetch_github_stats(username, github_token, from_date=from_date, to_date=to_date)
        
        # Show all days with contributions
        days_with_contribs = [d for d in stats_data["days"] if d["count"] > 0]
        
        return {
            "total_contributions": stats_data["total_contributions"],
            "total_days": len(stats_data["days"]),
            "days_with_contributions": len(days_with_contribs),
            "contributions_by_day": days_with_contribs,
            "date_range": {"from": from_date, "to": to_date}
        }
    except Exception as e:
        return {"error": str(e)}
