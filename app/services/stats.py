from datetime import datetime, timedelta
from typing import List, Dict

def calculate_streaks(days: List[Dict[str, any]]) -> dict:
    """Calculate current and longest contribution streaks"""
    if not days:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Sort by date
    sorted_days = sorted(days, key=lambda x: x["date"])
    
    # Convert to date objects and filter out future dates
    today = datetime.utcnow().date()
    contributions = []
    
    for day in sorted_days:
        date = datetime.fromisoformat(day["date"]).date()
        if date <= today:
            contributions.append((date, day["count"]))
    
    if not contributions:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Calculate current streak (from today backwards)
    current_streak = 0
    check_date = today
    
    # Create a dict for quick lookup
    contrib_dict = {date: count for date, count in contributions}
    
    while check_date >= contributions[0][0]:
        if contrib_dict.get(check_date, 0) > 0:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    # Calculate longest streak
    longest_streak = 0
    current = 0
    
    # Fill in missing dates with 0 contributions
    start_date = contributions[0][0]
    end_date = contributions[-1][0]
    
    check_date = start_date
    while check_date <= end_date:
        if contrib_dict.get(check_date, 0) > 0:
            current += 1
            longest_streak = max(longest_streak, current)
        else:
            current = 0
        check_date += timedelta(days=1)
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak
    }
