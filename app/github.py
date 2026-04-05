import httpx
from datetime import datetime, timedelta
from typing import Optional

GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
REST_ENDPOINT = "https://api.github.com"

GRAPHQL_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
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

# Query for authenticated user (includes private contributions)
GRAPHQL_QUERY_WITH_PRIVATE = """
query($from: DateTime!, $to: DateTime!) {
  viewer {
    contributionsCollection(from: $from, to: $to) {
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

async def fetch_github_stats(username: str, token: str, include_private: bool = True, from_date: str = None, to_date: str = None) -> Optional[dict]:
    """Fetch GitHub stats using GraphQL (primary) or REST (fallback)"""
    try:
        return await _fetch_graphql(username, token, include_private, from_date, to_date)
    except Exception:
        return await _fetch_rest(username, token)

async def _fetch_graphql(username: str, token: str, include_private: bool = True, from_date: str = None, to_date: str = None) -> dict:
    # Default to last year if no dates provided
    if not from_date or not to_date:
        to_date = datetime.utcnow().isoformat() + "Z"
        from_date = (datetime.utcnow() - timedelta(days=365)).isoformat() + "Z"
    
    async with httpx.AsyncClient() as client:
        # Always try to get viewer info first
        viewer_response = await client.post(
            GRAPHQL_ENDPOINT,
            json={"query": "query { viewer { login } }"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0
        )
        viewer_data = viewer_response.json()
        viewer_login = viewer_data.get("data", {}).get("viewer", {}).get("login", "")
        
        # If viewer matches username, use viewer query (includes private)
        if viewer_login.lower() == username.lower():
            response = await client.post(
                GRAPHQL_ENDPOINT,
                json={"query": GRAPHQL_QUERY_WITH_PRIVATE, "variables": {"from": from_date, "to": to_date}},
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                raise Exception(data["errors"])
            
            calendar = data["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
        else:
            # Different user, use public query
            response = await client.post(
                GRAPHQL_ENDPOINT,
                json={"query": GRAPHQL_QUERY, "variables": {"username": username, "from": from_date, "to": to_date}},
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
