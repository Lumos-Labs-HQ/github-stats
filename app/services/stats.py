from datetime import datetime, timedelta, date, timezone
from typing import List, Dict, Optional


def _deduplicate_days(days: List[Dict]) -> List[Dict]:
    """Remove duplicate dates, keeping the entry with the higher contribution count."""
    seen: Dict[str, Dict] = {}
    for day in days:
        d = day["date"]
        if d not in seen or day["count"] > seen[d]["count"]:
            seen[d] = day
    return list(seen.values())


def merge_contribution_windows(*windows: List[Dict]) -> List[Dict]:
    """
    Merge multiple contribution day lists.
    Sums counts when the same date appears in multiple windows.
    Returns a deduplicated list sorted ascending by date.
    """
    merged: Dict[str, int] = {}
    for window in windows:
        for day in window:
            merged[day["date"]] = merged.get(day["date"], 0) + day["count"]
    return [{"date": d, "count": c} for d, c in sorted(merged.items())]


def _fmt_date(d: date, current_year: Optional[int] = None) -> str:
    """Format date as 'Jan 1, 2024' or 'Jan 1' when year matches current_year."""
    if current_year and d.year == current_year:
        return d.strftime("%b ") + str(d.day)
    return d.strftime("%b ") + str(d.day) + d.strftime(", %Y")


def calculate_streaks(
    days: List[Dict],
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> dict:
    """Calculate streak stats using the same forward-scan approach as github-readme-streak-stats."""
    empty = {
        "current_streak": 0,
        "current_streak_start": None,
        "current_streak_end": None,
        "longest_streak": 0,
        "longest_streak_start": None,
        "longest_streak_end": None,
        "total_contributions": 0,
        "first_contribution": None,
    }
    if not days:
        return empty

    days = _deduplicate_days(days)
    sorted_days = sorted(days, key=lambda x: x["date"])

    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)
    current_year = today.year

    contributions: list[tuple[date, int]] = []
    for day in sorted_days:
        d = datetime.fromisoformat(day["date"]).date()
        count = day["count"]
        include_day = d <= today or (d == tomorrow and count > 0)
        if not include_day:
            continue
        if month and year and not (d.month == month and d.year == year):
            continue
        contributions.append((d, count))

    if not contributions:
        return empty

    contributions.sort(key=lambda item: item[0])
    timeline = {d: count for d, count in contributions}
    start_date = contributions[0][0]
    end_date = contributions[-1][0]

    stats = {
        "total_contributions": 0,
        "first_contribution": None,
        "longest_streak": {"start": start_date, "end": start_date, "length": 0},
        "current_streak": {"start": end_date, "end": end_date, "length": 0},
    }

    scan_date = start_date
    while scan_date <= end_date:
        count = timeline.get(scan_date, 0)
        stats["total_contributions"] += count

        if count > 0:
            stats["current_streak"]["length"] += 1
            stats["current_streak"]["end"] = scan_date
            if stats["current_streak"]["length"] == 1:
                stats["current_streak"]["start"] = scan_date
            if stats["first_contribution"] is None:
                stats["first_contribution"] = scan_date
            if stats["current_streak"]["length"] > stats["longest_streak"]["length"]:
                stats["longest_streak"] = stats["current_streak"].copy()
        elif scan_date != today:
            stats["current_streak"] = {"start": end_date, "end": end_date, "length": 0}

        scan_date += timedelta(days=1)

    current_streak = stats["current_streak"]
    longest_streak = stats["longest_streak"]
    first_contribution = stats["first_contribution"]

    return {
        "current_streak": current_streak["length"],
        "current_streak_start": _fmt_date(current_streak["start"], current_year) if current_streak["length"] > 0 else None,
        "current_streak_end": _fmt_date(current_streak["end"], current_year) if current_streak["length"] > 0 else None,
        "longest_streak": longest_streak["length"],
        "longest_streak_start": _fmt_date(longest_streak["start"], current_year) if longest_streak["length"] > 0 else None,
        "longest_streak_end": _fmt_date(longest_streak["end"], current_year) if longest_streak["length"] > 0 else None,
        "total_contributions": stats["total_contributions"],
        "first_contribution": _fmt_date(first_contribution, current_year) if first_contribution else None,
    }
