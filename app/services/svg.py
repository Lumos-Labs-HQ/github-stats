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


def generate_stats_svg(
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
