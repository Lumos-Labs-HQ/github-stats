from datetime import datetime, timedelta
from typing import List, Dict, Optional

def calculate_streaks(days: List[Dict[str, any]], month: Optional[int] = None, year: Optional[int] = None) -> dict:
    """Calculate current and longest contribution streaks"""
    if not days:
        return {"current_streak": 0, "longest_streak": 0, "total_contributions": 0}
    
    # Sort by date
    sorted_days = sorted(days, key=lambda x: x["date"])
    
    # Convert to date objects and filter
    today = datetime.utcnow().date()
    contributions = []
    total_contributions = 0
    
    for day in sorted_days:
        date = datetime.fromisoformat(day["date"]).date()
        if date <= today:
            # Filter by month/year if specified
            if month and year:
                if date.month == month and date.year == year:
                    contributions.append((date, day["count"]))
                    total_contributions += day["count"]
            else:
                contributions.append((date, day["count"]))
                total_contributions += day["count"]
    
    if not contributions:
        return {"current_streak": 0, "longest_streak": 0, "total_contributions": 0}
    
    # Calculate current streak (from today or end of month backwards)
    current_streak = 0
    if month and year:
        # For specific month, start from last day of that month or today
        check_date = min(today, contributions[-1][0])
    else:
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
        "longest_streak": longest_streak,
        "total_contributions": total_contributions
    }
