import httpx
from datetime import datetime
from typing import Optional

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
REST_ENDPOINT = "https://api.github.com"

GRAPHQL_QUERY = """
query($username: String!) {
  user(login: $username) {
    contributionsCollection {
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

async def fetch_github_stats(username: str, token: str) -> Optional[dict]:
    """Fetch GitHub stats using GraphQL (primary) or REST (fallback)"""
    try:
        return await _fetch_graphql(username, token)
    except Exception:
        return await _fetch_rest(username, token)

async def _fetch_graphql(username: str, token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GRAPHQL_ENDPOINT,
            json={"query": GRAPHQL_QUERY, "variables": {"username": username}},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        
        if "errors" in data:
            raise Exception(data["errors"])
        
        calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        
        days = []
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                days.append({
                    "date": day["date"],
                    "count": day["contributionCount"]
                })
        
        return {
            "total_contributions": calendar["totalContributions"],
            "days": days
        }

async def _fetch_rest(username: str, token: str) -> dict:
    """Fallback to REST API - limited data"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{REST_ENDPOINT}/users/{username}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        response.raise_for_status()
        
        return {
            "total_contributions": 0,
            "days": []
        }
