from datetime import datetime, timedelta, date
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
    """
    Calculate current streak, longest streak, and totals.

    Returns dict with keys:
        current_streak, current_streak_start, current_streak_end,
        longest_streak, longest_streak_start, longest_streak_end,
        total_contributions, first_contribution
    """
    if not days:
        return {
            "current_streak": 0, "current_streak_start": None, "current_streak_end": None,
            "longest_streak": 0, "longest_streak_start": None, "longest_streak_end": None,
            "total_contributions": 0, "first_contribution": None,
        }

    days = _deduplicate_days(days)
    sorted_days = sorted(days, key=lambda x: x["date"])

    today = datetime.utcnow().date()
    current_year = today.year
    contributions = []
    total_contributions = 0

    for day in sorted_days:
        d = datetime.fromisoformat(day["date"]).date()
        if d <= today:
            if month and year:
                if d.month == month and d.year == year:
                    contributions.append((d, day["count"]))
                    total_contributions += day["count"]
            else:
                contributions.append((d, day["count"]))
                total_contributions += day["count"]

    if not contributions:
        return {
            "current_streak": 0, "current_streak_start": None, "current_streak_end": None,
            "longest_streak": 0, "longest_streak_start": None, "longest_streak_end": None,
            "total_contributions": 0, "first_contribution": None,
        }

    contrib_dict = {d: c for d, c in contributions}
    first_contribution_date = contributions[0][0]

    # ------------------------------------------------------------------
    # Current streak: count backwards from today, or yesterday if today is 0
    # ------------------------------------------------------------------
    check_date = today if contrib_dict.get(today, 0) > 0 else today - timedelta(days=1)
    current_streak = 0
    current_streak_end: Optional[date] = None
    current_streak_start: Optional[date] = None

    while check_date >= first_contribution_date:
        if contrib_dict.get(check_date, 0) > 0:
            if current_streak_end is None:
                current_streak_end = check_date
            current_streak += 1
            current_streak_start = check_date
            check_date -= timedelta(days=1)
        else:
            break

    # ------------------------------------------------------------------
    # Longest streak: scan full date range
    # ------------------------------------------------------------------
    longest_streak = 0
    longest_streak_start: Optional[date] = None
    longest_streak_end: Optional[date] = None

    current_run = 0
    run_start: Optional[date] = None
    run_end: Optional[date] = None

    scan_date = first_contribution_date
    last_date = contributions[-1][0]

    while scan_date <= last_date:
        if contrib_dict.get(scan_date, 0) > 0:
            if current_run == 0:
                run_start = scan_date
            run_end = scan_date
            current_run += 1
            if current_run > longest_streak:
                longest_streak = current_run
                longest_streak_start = run_start
                longest_streak_end = run_end
        else:
            current_run = 0
            run_start = None
            run_end = None
        scan_date += timedelta(days=1)

    return {
        "current_streak": current_streak,
        "current_streak_start": _fmt_date(current_streak_start, current_year) if current_streak_start else None,
        "current_streak_end": _fmt_date(current_streak_end, current_year) if current_streak_end else None,
        "longest_streak": longest_streak,
        "longest_streak_start": _fmt_date(longest_streak_start, current_year) if longest_streak_start else None,
        "longest_streak_end": _fmt_date(longest_streak_end, current_year) if longest_streak_end else None,
        "total_contributions": total_contributions,
        "first_contribution": _fmt_date(first_contribution_date, current_year),
    }
