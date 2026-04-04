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
async def get_stats(username: str):
    """Generate GitHub stats SVG card"""
    
    # Check cache first
    cached = await cache_service.get_stats(username)
    if cached:
        return Response(content=cached["svg"], media_type="image/svg+xml")
    
    # Fetch from GitHub
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        svg = generate_error_svg("GitHub token not configured")
        return Response(content=svg, media_type="image/svg+xml")
    
    try:
        stats_data = await fetch_github_stats(username, github_token)
        
        if not stats_data:
            svg = generate_error_svg(f"User '{username}' not found")
            return Response(content=svg, media_type="image/svg+xml")
        
        # Calculate streaks
        streaks = calculate_streaks(stats_data["days"])
        
        # Generate SVG
        svg = generate_stats_svg(
            username=username,
            total_contributions=stats_data["total_contributions"],
            current_streak=streaks["current_streak"],
            longest_streak=streaks["longest_streak"]
        )
        
        # Cache the result
        await cache_service.set_stats(username, {"svg": svg}, ttl=900)
        
        return Response(content=svg, media_type="image/svg+xml")
        
    except Exception as e:
        # Try to return cached data if available
        cached = await cache_service.get_stats(username)
        if cached:
            return Response(content=cached["svg"], media_type="image/svg+xml")
        
        svg = generate_error_svg("Failed to fetch GitHub data")
        return Response(content=svg, media_type="image/svg+xml")

@app.get("/health")
async def health():
    return {"status": "ok"}
