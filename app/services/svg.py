import re
from typing import Optional


def _esc(s: str) -> str:
    """Escape special XML characters for safe SVG embedding."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;")


_THEMES = {
  "default": {
    "background": "#1f2437",
    "stroke": "#ff7a70",
    "ring": "#ff7a70",
    "fire": "#ff7a70",
    "currStreakNum": "#ff7a70",
    "currStreakLabel": "#ff7a70",
    "sideNums": "#ff7a70",
    "sideLabels": "#ff7a70",
    "dates": "#ff7a70",
  },
  "github-dark": {
    "background": "#0d1117",
    "stroke": "#30363d",
    "ring": "#f78166",
    "fire": "#f78166",
    "currStreakNum": "#f78166",
    "currStreakLabel": "#8b949e",
    "sideNums": "#e6edf3",
    "sideLabels": "#8b949e",
    "dates": "#8b949e",
  },
  "ocean": {
    "background": "#0d1b2a",
    "stroke": "#415a77",
    "ring": "#00b4d8",
    "fire": "#00b4d8",
    "currStreakNum": "#90e0ef",
    "currStreakLabel": "#caf0f8",
    "sideNums": "#90e0ef",
    "sideLabels": "#caf0f8",
    "dates": "#7fd4e6",
  },
  "sunset": {
    "background": "#231942",
    "stroke": "#5e548e",
    "ring": "#f15bb5",
    "fire": "#f15bb5",
    "currStreakNum": "#fee440",
    "currStreakLabel": "#f15bb5",
    "sideNums": "#fee440",
    "sideLabels": "#f15bb5",
    "dates": "#f7b6e5",
  },
}


def _sanitize_color(value: Optional[str], default: str) -> str:
  if not value:
    return default
  raw = value.strip()
  if raw.startswith("#"):
    raw = raw[1:]
  if re.fullmatch(r"[0-9a-fA-F]{3}([0-9a-fA-F]{3})?", raw):
    return f"#{raw}"
  lowered = value.strip().lower()
  if lowered in {"none", "transparent"}:
    return lowered
  return default


def resolve_theme(
  theme: Optional[str] = None,
  stroke: Optional[str] = None,
  background: Optional[str] = None,
  ring: Optional[str] = None,
  fire: Optional[str] = None,
  curr_streak_num: Optional[str] = None,
  curr_streak_label: Optional[str] = None,
  side_nums: Optional[str] = None,
  side_labels: Optional[str] = None,
  dates: Optional[str] = None,
) -> dict:
  base = _THEMES.get((theme or "default").lower(), _THEMES["default"]).copy()
  base["stroke"] = _sanitize_color(stroke, base["stroke"])
  base["background"] = _sanitize_color(background, base["background"])
  base["ring"] = _sanitize_color(ring, base["ring"])
  base["fire"] = _sanitize_color(fire, base["fire"])
  base["currStreakNum"] = _sanitize_color(curr_streak_num, base["currStreakNum"])
  base["currStreakLabel"] = _sanitize_color(curr_streak_label, base["currStreakLabel"])
  base["sideNums"] = _sanitize_color(side_nums, base["sideNums"])
  base["sideLabels"] = _sanitize_color(side_labels, base["sideLabels"])
  base["dates"] = _sanitize_color(dates, base["dates"])
  return base


def get_available_themes() -> list[str]:
  return sorted(_THEMES.keys())


def _rank_from_metrics(
    total_commits: int,
    total_prs: int,
    total_issues: int,
    total_stars: int,
    contributed_to: int,
) -> tuple[str, int]:
    """Return (grade, ring_percent) based on weighted public activity metrics."""
    score = (
        (total_commits * 0.08)
        + (total_prs * 1.8)
        + (total_issues * 0.9)
        + (total_stars * 2.0)
        + (contributed_to * 1.4)
    )

    if score >= 900:
        grade = "S"
    elif score >= 700:
        grade = "A+"
    elif score >= 500:
        grade = "A"
    elif score >= 320:
        grade = "B+"
    elif score >= 220:
        grade = "B"
    elif score >= 140:
        grade = "C+"
    elif score >= 80:
        grade = "C"
    else:
        grade = "D"

    ring_percent = max(12, min(100, int(score / 9) if score > 0 else 12))
    return grade, ring_percent


def generate_stats_svg(
    username: str,
    total_stars: int,
    total_commits: int,
    total_prs: int,
    total_issues: int,
    contributed_to: int,
    private_contributions: int = 0,
    commits_year: Optional[int] = None,
    colors: Optional[dict] = None,
    hide_border: bool = False,
) -> str:
    """Generate a compact all-stats SVG card with icons and rank ring."""

    colors = colors or _THEMES["default"]
    grade, ring_percent = _rank_from_metrics(
        total_commits=total_commits,
        total_prs=total_prs,
        total_issues=total_issues,
        total_stars=total_stars,
        contributed_to=contributed_to,
    )

    commits_label = f"Total Commits ({commits_year})" if commits_year else "Total Commits"
    private_label = f"(+{private_contributions} private)" if private_contributions > 0 else ""

    circumference = 2 * 3.14159 * 52
    filled = round((ring_percent / 100) * circumference, 2)
    remaining = round(circumference - filled, 2)

    border = "none" if hide_border else colors["stroke"]

    svg = f'''<svg width="632" height="251" viewBox="0 0 632 251" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title">
  <title id="title">{_esc(username)} GitHub stats</title>
  <defs>
    <style>
      .title {{ font: 700 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["currStreakNum"]}; }}
      .label {{ font: 700 10px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["sideLabels"]}; }}
      .value {{ font: 700 10px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["sideNums"]}; }}
      .subtle {{ font: 400 8px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["dates"]}; }}
      .icon {{ fill: none; stroke: {colors["fire"]}; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }}
      .ring-grade {{ font: 700 26px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["currStreakNum"]}; }}
    </style>
  </defs>

  <rect x="1" y="1" width="630" height="249" rx="4" fill="{colors["background"]}" stroke="{border}" stroke-width="2"/>

  <text x="26" y="40" class="title">{_esc(username)}'s GitHub Stats</text>

  <g transform="translate(26, 66)">
    <g transform="translate(0, 0)">
      <path class="icon" d="M10 1.5l2.1 4.3 4.8.7-3.5 3.4.8 4.9L10 12.5 5.8 14.8l.8-4.9L3.1 6.5l4.8-.7L10 1.5z"/>
      <text x="24" y="11" class="label">Total Stars Earned:</text>
      <text x="276" y="11" class="value" text-anchor="end">{total_stars:,}</text>
    </g>

    <g transform="translate(0, 27)">
      <circle class="icon" cx="10" cy="8" r="7"/>
      <path class="icon" d="M10 8V4.5M10 8l3.2 1.8"/>
      <path class="icon" d="M2 2.2h2.8M14.8 2.2h2.8"/>
      <text x="24" y="11" class="label">{_esc(commits_label)}:</text>
      <text x="276" y="11" class="value" text-anchor="end">{total_commits:,}</text>
      <text x="24" y="23" class="subtle">{_esc(private_label)}</text>
    </g>

    <g transform="translate(0, 54)">
      <circle class="icon" cx="4" cy="5" r="2"/>
      <circle class="icon" cx="16" cy="2" r="2"/>
      <circle class="icon" cx="16" cy="14" r="2"/>
      <path class="icon" d="M6 5h5a3 3 0 0 0 3-3M6 5h5a3 3 0 0 1 3 3"/>
      <text x="24" y="11" class="label">Total PRs:</text>
      <text x="276" y="11" class="value" text-anchor="end">{total_prs:,}</text>
    </g>

    <g transform="translate(0, 81)">
      <circle class="icon" cx="10" cy="8" r="7"/>
      <path class="icon" d="M10 4.2v4.7M10 11.8h.01"/>
      <text x="24" y="11" class="label">Total Issues:</text>
      <text x="276" y="11" class="value" text-anchor="end">{total_issues:,}</text>
    </g>

    <g transform="translate(0, 108)">
      <rect class="icon" x="3" y="2" width="14" height="12" rx="1.5"/>
      <path class="icon" d="M3 6h14M7 14v3M13 14v3"/>
      <text x="24" y="11" class="label">Contributed to:</text>
      <text x="276" y="11" class="value" text-anchor="end">{contributed_to:,}</text>
    </g>
  </g>

  <g transform="translate(500, 126)">
    <circle cx="0" cy="0" r="52" fill="none" stroke="{colors["stroke"]}" stroke-opacity="0.35" stroke-width="8"/>
    <circle
      cx="0"
      cy="0"
      r="52"
      fill="none"
      stroke="{colors["ring"]}"
      stroke-width="8"
      stroke-linecap="round"
      transform="rotate(-90)"
      stroke-dasharray="{filled} {remaining}"
    />
    <text x="0" y="10" class="ring-grade" text-anchor="middle">{grade}</text>
  </g>
</svg>'''

    return svg


def generate_streak_svg(
    username: str,
    total_contributions: int,
    current_streak: int,
    longest_streak: int,
    first_contribution: Optional[str] = None,
    current_streak_start: Optional[str] = None,
    current_streak_end: Optional[str] = None,
    longest_streak_start: Optional[str] = None,
    longest_streak_end: Optional[str] = None,
    colors: Optional[dict] = None,
    hide_border: bool = False,
) -> str:
    """Generate a streak-style SVG card with date ranges."""

    colors = colors or _THEMES["default"]

    # Date range labels shown under each stat
    contrib_range = f"{_esc(first_contribution)} - Present" if first_contribution else ""
    cur_range = (
        f"{_esc(current_streak_start)} - {_esc(current_streak_end)}"
        if current_streak_start and current_streak_end else ""
    )
    long_range = (
        f"{_esc(longest_streak_start)} - {_esc(longest_streak_end)}"
        if longest_streak_start and longest_streak_end else ""
    )

    border = "none" if hide_border else colors["stroke"]

    svg = f'''<svg width="632" height="251" viewBox="0 0 632 251" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title">
  <title id="title">{_esc(username)} GitHub streak stats</title>
  <defs>
    <style>
      .value {{ font: 700 38px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["sideNums"]}; }}
      .label {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["sideLabels"]}; }}
      .date {{ font: 400 10px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["dates"]}; }}
      .ring-number {{ font: 700 38px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["currStreakNum"]}; }}
      .ring-label {{ font: 700 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["currStreakLabel"]}; }}
    </style>
  </defs>

  <rect x="1" y="1" width="630" height="249" rx="4" fill="{colors["background"]}" stroke="{border}" stroke-width="2"/>

  <line x1="224" y1="34" x2="224" y2="216" stroke="{colors["stroke"]}" stroke-width="2"/>
  <line x1="408" y1="34" x2="408" y2="216" stroke="{colors["stroke"]}" stroke-width="2"/>

  <g transform="translate(112, 116)">
    <text x="0" y="0" class="value" text-anchor="middle">{total_contributions:,}</text>
    <text x="0" y="30" class="label" text-anchor="middle">Total Contributions</text>
    <text x="0" y="58" class="date" text-anchor="middle">{contrib_range}</text>
  </g>

  <g transform="translate(316, 30)">
    <path d="M 0 18 C -6 10 -7 -1 1 -10 C 0 -2 8 2 8 11 C 8 17 4 21 0 21 C -5 21 -9 17 -9 11 C -9 7 -7 3 -4 0 C -5 6 -3 12 0 18 Z" fill="{colors["fire"]}"/>
    <circle cx="0" cy="70" r="46" fill="none" stroke="{colors["ring"]}" stroke-width="5"/>
    <text x="0" y="85" class="ring-number" text-anchor="middle">{current_streak}</text>
    <text x="0" y="160" class="ring-label" text-anchor="middle">Current Streak</text>
    <text x="0" y="186" class="date" text-anchor="middle">{cur_range}</text>
  </g>

  <g transform="translate(520, 116)">
    <text x="0" y="0" class="value" text-anchor="middle">{longest_streak}</text>
    <text x="0" y="30" class="label" text-anchor="middle">Longest Streak</text>
    <text x="0" y="58" class="date" text-anchor="middle">{long_range}</text>
  </g>
</svg>'''

    return svg


def generate_error_svg(message: str) -> str:
    """Generate a 632x251 error SVG."""
    svg = f'''<svg width="632" height="251" viewBox="0 0 632 251" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .error-text {{ font: 400 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #f85149; }}
    </style>
  </defs>
  <rect width="632" height="251" rx="4" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="316" y="126" class="error-text" text-anchor="middle">{_esc(message)}</text>
</svg>'''
    return svg
