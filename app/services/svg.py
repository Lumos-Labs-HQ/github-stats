import re
from typing import Optional


def _esc(s: str) -> str:
    """Escape special XML characters for safe SVG embedding."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&apos;")
    )


_THEMES = {
    "default": {
        "background": "#212438",
        "stroke": "#de7872",
        "ring": "#de7872",
        "fire": "#de7872",
        "currStreakNum": "#de7872",
        "currStreakLabel": "#de7872",
        "sideNums": "#de7872",
        "sideLabels": "#de7872",
        "dates": "#c98781",
    },
    "tokyonight": {
        "background": "#1a1b27",
        "stroke": "#414868",
        "ring": "#fe428e",
        "fire": "#e3b341",
        "currStreakNum": "#fe428e",
        "currStreakLabel": "#fe428e",
        "sideNums": "#a9fef7",
        "sideLabels": "#a9fef7",
        "dates": "#a9fef7",
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
    "paper": {
        "background": "#f4f1ea",
        "stroke": "#d2cbc0",
        "ring": "#305f72",
        "fire": "#c06c4b",
        "currStreakNum": "#1a1d22",
        "currStreakLabel": "#305f72",
        "sideNums": "#1a1d22",
        "sideLabels": "#4d5560",
        "dates": "#7d837f",
    },
    "studio-light": {
        "background": "#f7f7f2",
        "stroke": "#d6d7cf",
        "ring": "#1b6b5f",
        "fire": "#987246",
        "currStreakNum": "#11151a",
        "currStreakLabel": "#1b6b5f",
        "sideNums": "#11151a",
        "sideLabels": "#45515b",
        "dates": "#74818b",
    },
    "graphite": {
        "background": "#171b20",
        "stroke": "#303842",
        "ring": "#67c6b7",
        "fire": "#f09a61",
        "currStreakNum": "#f3f5f7",
        "currStreakLabel": "#67c6b7",
        "sideNums": "#f3f5f7",
        "sideLabels": "#b2bcc5",
        "dates": "#7e8b96",
    },
}

_CARD_SPECS = {
    "stats": {"width": 520, "height": 228, "radius": 18},
    "languages": {"width": 640, "height": 320, "radius": 18},
    "repositories": {"width": 640, "height": 292, "radius": 18},
    "activity": {"width": 640, "height": 292, "radius": 18},
}

_CARD_LAYOUTS = {
    "languages": {
        "divider_x": 424,
        "summary_x": 450,
        "left_x": 24,
        "left_icon_x": 8,
        "name_x": 24,
        "name_limit": 10,
        "bar_start_x": 112,
        "bar_end_x": 284,
        "percent_x": 336,
        "row_start_y": 84,
        "row_gap": 40,
        "summary_y": 44,
    },
    "repositories": {
        "divider_x": 452,
        "summary_x": 478,
    },
    "activity": {
        "divider_x": 430,
        "title_x": 24,
        "title_y": 36,
        "left_x": 24,
        "row_name_x": 0,
        "row_count_x": 348,
        "row_start_y": 84,
        "row_gap": 44,
        "row_name_limit": 24,
        "row_divider_x2": 404,
        "metric_x": 462,
        "metric_label_x": 0,
        "metric_value_x": 0,
        "metric_start_y": 58,
        "metric_gap": 52,
        "metric_count": 4,
    },
}

_DEFAULT_CARD_THEMES = {
    "stats": "default",
    "streak": "default",
    "languages": "default",
    "repositories": "default",
    "activity": "default",
}

_ACTIVITY_METRIC_ORDER = [
    "Pushes",
    "Pull Requests",
    "Issues",
    "Stars",
    "Comments",
    "Creates",
    "Forks",
    "Reviews",
    "Releases",
]


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
    base["currStreakLabel"] = _sanitize_color(
        curr_streak_label, base["currStreakLabel"]
    )
    base["sideNums"] = _sanitize_color(side_nums, base["sideNums"])
    base["sideLabels"] = _sanitize_color(side_labels, base["sideLabels"])
    base["dates"] = _sanitize_color(dates, base["dates"])
    return base


def resolve_card_theme(
    card_type: str,
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
    return resolve_theme(
        theme=theme or get_default_theme_name(card_type),
        stroke=stroke,
        background=background,
        ring=ring,
        fire=fire,
        curr_streak_num=curr_streak_num,
        curr_streak_label=curr_streak_label,
        side_nums=side_nums,
        side_labels=side_labels,
        dates=dates,
    )


def get_available_themes() -> list[str]:
    return sorted(_THEMES.keys())


def get_default_theme_name(card_type: str) -> str:
    return _DEFAULT_CARD_THEMES.get(card_type, "default")


def get_card_spec(card_type: str) -> dict:
    return _CARD_SPECS[card_type].copy()


def get_card_layout(card_type: str) -> dict:
    return _CARD_LAYOUTS.get(card_type, {}).copy()


def _truncate(text: Optional[str], limit: int) -> str:
    if not text:
        return ""
    text = " ".join(text.split())
    return text if len(text) <= limit else f"{text[: limit - 1].rstrip()}…"


def _short_username(username: str, limit: int = 18) -> str:
    return _truncate(username, limit)


def _radius(card_type: str, rounded: bool) -> int:
    return get_card_spec(card_type)["radius"] if rounded else 0


def _icon(name: str, x: int, y: int, colors: dict, size: int = 14) -> str:
    half = size / 2
    if name == "star":
        path = (
            "M 0 -6 L 1.8 -1.8 L 6 -1.4 L 2.8 1.3 "
            "L 3.9 5.8 L 0 3.5 L -3.9 5.8 L -2.8 1.3 "
            "L -6 -1.4 L -1.8 -1.8 Z"
        )
        return (
            f'<g transform="translate({x},{y}) scale({size/14})">'
            f'<path d="{path}" fill="none" stroke="{colors["fire"]}" '
            'stroke-width="1.4" stroke-linejoin="round"/>'
            "</g>"
        )
    if name == "commit":
        return (
            f'<g transform="translate({x},{y})">'
            f'<circle cx="0" cy="0" r="{half - 2}" fill="none" '
            f'stroke="{colors["fire"]}" stroke-width="1.4"/>'
            f'<path d="M {-half} 0 H {half}" stroke="{colors["fire"]}" '
            'stroke-width="1.4" stroke-linecap="round"/>'
            "</g>"
        )
    if name == "pr":
        return (
            f'<g transform="translate({x},{y})">'
            f'<circle cx="-4" cy="-4" r="2.3" fill="none" stroke="{colors["fire"]}" stroke-width="1.3"/>'
            f'<circle cx="4" cy="-7" r="2.3" fill="none" stroke="{colors["fire"]}" stroke-width="1.3"/>'
            f'<circle cx="4" cy="5" r="2.3" fill="none" stroke="{colors["fire"]}" stroke-width="1.3"/>'
            f'<path d="M -1 -4 H 1 A 4 4 0 0 0 4 -7" stroke="{colors["fire"]}" stroke-width="1.3" fill="none"/>'
            f'<path d="M -1 -4 H 1 A 4 4 0 0 1 4 5" stroke="{colors["fire"]}" stroke-width="1.3" fill="none"/>'
            "</g>"
        )
    if name == "issue":
        return (
            f'<g transform="translate({x},{y})">'
            f'<circle cx="0" cy="0" r="{half - 1.5}" fill="none" stroke="{colors["fire"]}" stroke-width="1.3"/>'
            f'<path d="M 0 -4 V 1" stroke="{colors["fire"]}" stroke-width="1.3" stroke-linecap="round"/>'
            f'<circle cx="0" cy="4" r="0.9" fill="{colors["fire"]}"/>'
            "</g>"
        )
    if name == "followers":
        return (
            f'<g transform="translate({x},{y})">'
            f'<circle cx="-2" cy="-2" r="2.2" fill="none" stroke="{colors["fire"]}" stroke-width="1.2"/>'
            f'<path d="M -6 5 C -6 1, 2 1, 2 5" fill="none" stroke="{colors["fire"]}" stroke-width="1.2"/>'
            f'<circle cx="5" cy="-4" r="1.7" fill="none" stroke="{colors["fire"]}" stroke-width="1.1"/>'
            f'<path d="M 2 4 C 2 1, 8 1, 8 4" fill="none" stroke="{colors["fire"]}" stroke-width="1.1"/>'
            "</g>"
        )
    if name == "language":
        return (
            f'<g transform="translate({x},{y})">'
            f'<path d="M -5 -4 L -8 0 L -5 4" fill="none" stroke="{colors["fire"]}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M 5 -4 L 8 0 L 5 4" fill="none" stroke="{colors["fire"]}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M 1 -6 L -1 6" stroke="{colors["fire"]}" stroke-width="1.3" stroke-linecap="round"/>'
            "</g>"
        )
    if name == "repo":
        return (
            f'<g transform="translate({x},{y})">'
            f'<rect x="-7" y="-5" width="14" height="10" rx="1.5" fill="none" stroke="{colors["fire"]}" stroke-width="1.2"/>'
            f'<path d="M -3 -7 H 2 L 4 -5" fill="none" stroke="{colors["fire"]}" stroke-width="1.2" stroke-linecap="round"/>'
            "</g>"
        )
    if name == "fork":
        return (
            f'<g transform="translate({x},{y})">'
            f'<circle cx="-4" cy="-5" r="2" fill="none" stroke="{colors["fire"]}" stroke-width="1.2"/>'
            f'<circle cx="4" cy="0" r="2" fill="none" stroke="{colors["fire"]}" stroke-width="1.2"/>'
            f'<circle cx="-4" cy="5" r="2" fill="none" stroke="{colors["fire"]}" stroke-width="1.2"/>'
            f'<path d="M -2 -5 H 0 V 5 H -2" fill="none" stroke="{colors["fire"]}" stroke-width="1.2"/>'
            f'<path d="M 0 0 H 2" fill="none" stroke="{colors["fire"]}" stroke-width="1.2"/>'
            "</g>"
        )
    if name == "push":
        return (
            f'<g transform="translate({x},{y})">'
            f'<path d="M 0 6 V -4" stroke="{colors["fire"]}" stroke-width="1.3" stroke-linecap="round"/>'
            f'<path d="M -4 -1 L 0 -5 L 4 -1" fill="none" stroke="{colors["fire"]}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M -5 6 H 5" stroke="{colors["fire"]}" stroke-width="1.3" stroke-linecap="round"/>'
            "</g>"
        )
    return (
        f'<circle cx="{x}" cy="{y}" r="2.5" fill="{colors["fire"]}" opacity="0.95"/>'
    )


def _svg_card(
    *,
    card_type: str,
    title: str,
    colors: dict,
    hide_border: bool,
    rounded: bool,
    body: str,
    extra_styles: str = "",
) -> str:
    spec = get_card_spec(card_type)
    width = spec["width"]
    height = spec["height"]
    border = "none" if hide_border else colors["stroke"]
    radius = _radius(card_type, rounded)
    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title">
  <title id="title">{_esc(title)}</title>
  <defs>
    <style>
      .title {{ font: 700 18px 'Aptos', 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["currStreakNum"]}; letter-spacing: 0.2px; }}
      .label {{ font: 600 12px 'Aptos', 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["sideLabels"]}; }}
      .value {{ font: 700 14px 'Aptos', 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["sideNums"]}; }}
      .muted {{ font: 400 11px 'Aptos', 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["dates"]}; }}
      .hero {{ font: 700 22px 'Aptos', 'Segoe UI', Ubuntu, Sans-Serif; fill: {colors["currStreakNum"]}; }}
      .divider {{ stroke: {colors["stroke"]}; stroke-width: 1; }}
      .track {{ stroke: {colors["stroke"]}; stroke-width: 2.2; stroke-linecap: round; opacity: 0.32; }}
      .fill {{ stroke: {colors["ring"]}; stroke-width: 3; stroke-linecap: round; }}
      {extra_styles}
    </style>
  </defs>

  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="{radius}" fill="{colors["background"]}" stroke="{border}" stroke-width="1.5"/>
  {body}
</svg>'''


def _rank_from_metrics(
    total_commits: int,
    total_prs: int,
    total_issues: int,
    total_stars: int,
    followers: int,
) -> tuple[str, int]:
    score = (
        (total_commits * 0.07)
        + (total_prs * 2.0)
        + (total_issues * 1.0)
        + (total_stars * 2.2)
        + (followers * 1.2)
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

    ring_percent = max(12, min(100, int(score / 8.8) if score > 0 else 12))
    return grade, ring_percent


def generate_stats_svg(
    username: str,
    total_stars: int,
    total_commits: int,
    total_prs: int,
    total_issues: int,
    followers: int,
    commits_year: Optional[int] = None,
    colors: Optional[dict] = None,
    hide_border: bool = False,
    rounded: bool = False,
) -> str:
    colors = colors or _THEMES["default"]
    spec = get_card_spec("stats")
    width = spec["width"]
    height = spec["height"]
    divider_x = 368
    value_x = 328
    ring_x = 440
    ring_y = 110

    grade, ring_percent = _rank_from_metrics(
        total_commits=total_commits,
        total_prs=total_prs,
        total_issues=total_issues,
        total_stars=total_stars,
        followers=followers,
    )

    circumference = 2 * 3.14159 * 47
    filled = round((ring_percent / 100) * circumference, 2)
    remaining = round(circumference - filled, 2)
    heading = f"{_short_username(username)} Overview"
    commits_label = f"Total Commits ({commits_year})" if commits_year else "Total Commits"

    body = f'''
  <text x="24" y="36" class="title">{_esc(heading)}</text>

  <line x1="{divider_x}" y1="24" x2="{divider_x}" y2="{height - 24}" class="divider"/>

  <g transform="translate(24, 78)">
    <g transform="translate(0, 0)">
      {_icon("star", 7, -4, colors)}
      <text x="24" y="0" class="label">Stars Earned</text>
      <text x="{value_x}" y="0" class="value" text-anchor="end">{total_stars:,}</text>
    </g>
    <g transform="translate(0, 32)">
      {_icon("commit", 7, -4, colors)}
      <text x="24" y="0" class="label">{_esc(commits_label)}</text>
      <text x="{value_x}" y="0" class="value" text-anchor="end">{total_commits:,}</text>
    </g>
    <g transform="translate(0, 64)">
      {_icon("pr", 7, -4, colors)}
      <text x="24" y="0" class="label">Pull Requests Made</text>
      <text x="{value_x}" y="0" class="value" text-anchor="end">{total_prs:,}</text>
    </g>
    <g transform="translate(0, 96)">
      {_icon("issue", 7, -4, colors)}
      <text x="24" y="0" class="label">Issues Made</text>
      <text x="{value_x}" y="0" class="value" text-anchor="end">{total_issues:,}</text>
    </g>
    <g transform="translate(0, 128)">
      {_icon("followers", 7, -4, colors)}
      <text x="24" y="0" class="label">Followers</text>
      <text x="{value_x}" y="0" class="value" text-anchor="end">{followers:,}</text>
    </g>
  </g>

  <g transform="translate({ring_x}, {ring_y})">
    <circle cx="0" cy="0" r="47" fill="none" stroke="{colors["stroke"]}" stroke-opacity="0.35" stroke-width="7"/>
    <circle
      cx="0"
      cy="0"
      r="47"
      fill="none"
      stroke="{colors["ring"]}"
      stroke-width="7"
      stroke-linecap="round"
      transform="rotate(-90)"
      stroke-dasharray="{filled} {remaining}"
    />
    <text x="0" y="10" class="hero" text-anchor="middle">{grade}</text>
    <text x="0" y="78" class="label" text-anchor="middle">Activity Grade</text>
  </g>'''

    return _svg_card(
        card_type="stats",
        title=f"{username} GitHub stats",
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
        body=body,
    )


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
    rounded: bool = False,
) -> str:
    colors = colors or _THEMES["default"]
    border = "none" if hide_border else colors["stroke"]
    radius = 18 if rounded else 0
    contrib_range = f"{_esc(first_contribution)} - Present" if first_contribution else ""
    cur_range = (
        f"{_esc(current_streak_start)} - {_esc(current_streak_end)}"
        if current_streak_start and current_streak_end
        else ""
    )
    long_range = (
        f"{_esc(longest_streak_start)} - {_esc(longest_streak_end)}"
        if longest_streak_start and longest_streak_end
        else ""
    )

    return f'''<svg width="632" height="251" viewBox="0 0 632 251" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title">
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

  <rect x="1" y="1" width="630" height="249" rx="{radius}" fill="{colors["background"]}" stroke="{border}" stroke-width="2"/>

  <line x1="224" y1="38" x2="224" y2="208" stroke="{colors["stroke"]}" stroke-width="2"/>
  <line x1="408" y1="38" x2="408" y2="208" stroke="{colors["stroke"]}" stroke-width="2"/>

  <g transform="translate(112, 112)">
    <text x="0" y="0" class="value" text-anchor="middle">{total_contributions:,}</text>
    <text x="0" y="30" class="label" text-anchor="middle">Total Contributions</text>
    <text x="0" y="58" class="date" text-anchor="middle">{contrib_range}</text>
  </g>

  <g transform="translate(316, 26)">
    <path d="M 0 18 C -6 10 -7 -1 1 -10 C 0 -2 8 2 8 11 C 8 17 4 21 0 21 C -5 21 -9 17 -9 11 C -9 7 -7 3 -4 0 C -5 6 -3 12 0 18 Z" fill="{colors["fire"]}"/>
    <circle cx="0" cy="70" r="46" fill="none" stroke="{colors["ring"]}" stroke-width="5"/>
    <text x="0" y="85" class="ring-number" text-anchor="middle">{current_streak}</text>
    <text x="0" y="160" class="ring-label" text-anchor="middle">Current Streak</text>
    <text x="0" y="186" class="date" text-anchor="middle">{cur_range}</text>
  </g>

  <g transform="translate(520, 112)">
    <text x="0" y="0" class="value" text-anchor="middle">{longest_streak}</text>
    <text x="0" y="30" class="label" text-anchor="middle">Longest Streak</text>
    <text x="0" y="58" class="date" text-anchor="middle">{long_range}</text>
  </g>
</svg>'''


def generate_languages_svg(
    username: str,
    languages: list[dict],
    total_repos: int,
    total_stars: int,
    colors: Optional[dict] = None,
    hide_border: bool = False,
    rounded: bool = False,
) -> str:
    colors = colors or _THEMES["default"]
    spec = get_card_spec("languages")
    layout = get_card_layout("languages")
    shown_languages = languages[:5]
    divider_x = layout["divider_x"]
    summary_x = layout["summary_x"]
    bar_start_x = layout["bar_start_x"]
    bar_end_x = layout["bar_end_x"]
    bar_width_max = bar_end_x - bar_start_x
    rows = []

    for index, language in enumerate(shown_languages):
        y = layout["row_start_y"] + (index * layout["row_gap"])
        bar_width = max(
            18,
            min(bar_width_max, int((language.get("share", 0) / 100) * bar_width_max)),
        )
        rows.append(
            f'''
  <g transform="translate({layout["left_x"]}, {y})">
    {_icon("language", layout["left_icon_x"], -6, colors)}
    <text x="{layout["name_x"]}" y="0" class="label">{_esc(_truncate(language["name"], layout["name_limit"]))}</text>
    <line x1="{bar_start_x}" y1="-5" x2="{bar_end_x}" y2="-5" class="track"/>
    <line x1="{bar_start_x}" y1="-5" x2="{bar_start_x + bar_width}" y2="-5" class="fill"/>
    <text x="{layout["percent_x"]}" y="0" class="value" text-anchor="end">{language["share"]:.1f}%</text>
    <text x="{bar_start_x}" y="16" class="muted">{language["repos"]} repos</text>
    <text x="{bar_end_x}" y="16" class="muted" text-anchor="end">{language["stars"]} stars</text>
  </g>'''
        )

    if not rows:
        rows.append(
            '''
  <text x="24" y="112" class="label">No public language data yet</text>
  <text x="24" y="136" class="muted">This card needs public repositories with detected primary languages.</text>'''
        )

    primary = _truncate(shown_languages[0]["name"], 14) if shown_languages else "No data"
    body = f'''
  <text x="24" y="36" class="title">{_esc(_short_username(username))} Languages</text>

  <line x1="{divider_x}" y1="24" x2="{divider_x}" y2="{spec["height"] - 24}" class="divider"/>

  {"".join(rows)}

  <g transform="translate({summary_x}, {layout["summary_y"]})">
    {_icon("language", 8, -6, colors)}
    <text x="24" y="0" class="label">Top language</text>
    <text x="0" y="30" class="hero">{_esc(_truncate(primary, 10))}</text>
    {_icon("repo", 8, 92, colors)}
    <text x="24" y="98" class="label">Repos</text>
    <text x="0" y="128" class="hero">{total_repos}</text>
    {_icon("star", 8, 184, colors)}
    <text x="24" y="190" class="label">Total Stars</text>
    <text x="0" y="220" class="hero">{total_stars}</text>
  </g>'''

    return _svg_card(
        card_type="languages",
        title=f"{username} languages",
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
        body=body,
    )


def generate_repository_svg(
    username: str,
    repositories: list[dict],
    total_stars: int,
    colors: Optional[dict] = None,
    hide_border: bool = False,
    rounded: bool = False,
) -> str:
    colors = colors or _THEMES["default"]
    spec = get_card_spec("repositories")
    divider_x = 452
    summary_x = 478
    rows = []
    top_repo = repositories[0] if repositories else None

    for index, repo in enumerate(repositories[:4]):
        y = 82 + (index * 46)
        divider = (
            ""
            if index == 0
            else f'<line x1="24" y1="{y - 20}" x2="{divider_x - 18}" y2="{y - 20}" class="divider"/>'
        )
        rows.append(
            f'''
  {divider}
  <g transform="translate(24, {y})">
    {_icon("repo", 8, -6, colors)}
    <text x="24" y="0" class="value">{_esc(_truncate(repo["name"], 24))}</text>
    {_icon("star", 286, -6, colors, size=12)}
    <text x="302" y="0" class="muted">{repo["stars"]}</text>
    {_icon("fork", 346, -6, colors, size=12)}
    <text x="362" y="0" class="muted">{repo["forks"]}</text>
    <text x="24" y="20" class="label">{_esc(_truncate(repo.get("language"), 18) or "Unspecified")}</text>
  </g>'''
        )

    if not rows:
        rows.append(
            '''
  <text x="24" y="112" class="label">No featured repositories yet</text>
  <text x="24" y="136" class="muted">Public repositories will appear here once GitHub exposes them.</text>'''
        )

    top_repo_name = _truncate(top_repo["name"], 14) if top_repo else "No data"
    top_repo_stars = top_repo["stars"] if top_repo else 0
    body = f'''
  <text x="24" y="36" class="title">{_esc(_short_username(username))} Repositories</text>
  <line x1="{divider_x}" y1="24" x2="{divider_x}" y2="{spec["height"] - 24}" class="divider"/>
  {"".join(rows)}

  <g transform="translate({summary_x}, 52)">
    {_icon("repo", 8, -6, colors)}
    <text x="24" y="0" class="label">Top repo</text>
    <text x="0" y="34" class="hero">{_esc(top_repo_name)}</text>
    {_icon("star", 8, 98, colors)}
    <text x="24" y="104" class="label">Top Stars</text>
    <text x="0" y="138" class="hero">{top_repo_stars}</text>
    {_icon("star", 8, 202, colors)}
    <text x="24" y="208" class="label">Total Stars</text>
    <text x="0" y="242" class="hero">{total_stars}</text>
  </g>'''

    return _svg_card(
        card_type="repositories",
        title=f"{username} repositories",
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
        body=body,
    )


def _activity_metrics(activity_counts: dict) -> list[tuple[str, int]]:
    metrics = [
        (label, int(activity_counts.get(label, 0) or 0))
        for label in _ACTIVITY_METRIC_ORDER
    ]
    primary = metrics[:4]
    if sum(value for _, value in primary) > 0:
        return primary
    return metrics[:4]


def _fixed_activity_row(
    *,
    repo: dict,
    x: int,
    y: int,
    name_limit: int,
    count_x: int,
    colors: dict,
) -> str:
    return f'''
  <g transform="translate({x}, {y})">
    <text x="0" y="0" class="value">{_esc(_truncate(repo["full_name"], name_limit))}</text>
    <text x="{count_x}" y="0" class="label" text-anchor="end">{repo["count"]} events</text>
  </g>'''


def generate_activity_svg(
    username: str,
    recent_events: int,
    active_repos: int,
    activity_counts: Optional[dict],
    activity_repositories: list[dict],
    colors: Optional[dict] = None,
    hide_border: bool = False,
    rounded: bool = False,
) -> str:
    colors = colors or _THEMES["default"]
    spec = get_card_spec("activity")
    layout = get_card_layout("activity")
    divider_x = layout["divider_x"]
    rows = []
    metrics = _activity_metrics(activity_counts or {})

    for index, repo in enumerate(activity_repositories[:4]):
        y = layout["row_start_y"] + (index * layout["row_gap"])
        divider = (
            ""
            if index == 0
            else f'<line x1="{layout["left_x"]}" y1="{y - 20}" x2="{layout["row_divider_x2"]}" y2="{y - 20}" class="divider"/>'
        )
        rows.append(
            divider
            + _fixed_activity_row(
                repo=repo,
                x=layout["left_x"],
                y=y,
                name_limit=layout["row_name_limit"],
                count_x=layout["row_count_x"],
                colors=colors,
            )
        )

    if not rows:
        rows.append(
            '''
  <text x="24" y="112" class="label">No public activity available</text>'''
        )

    primary_metrics = metrics[: layout["metric_count"]]
    metric_rows = []
    for index, (label, value) in enumerate(primary_metrics):
        y = layout["metric_start_y"] + (index * layout["metric_gap"])
        metric_rows.append(
            f'''
  <g transform="translate({layout["metric_x"]}, {y})">
    <text x="{layout["metric_label_x"]}" y="0" class="label">{_esc(label)}</text>
    <text x="{layout["metric_value_x"]}" y="30" class="hero">{value}</text>
  </g>'''
        )

    body = f'''
  <text x="{layout["title_x"]}" y="{layout["title_y"]}" class="title">{_esc(_short_username(username))} Activity</text>
  <line x1="{divider_x}" y1="24" x2="{divider_x}" y2="{spec["height"] - 24}" class="divider"/>
  {"".join(rows)}
  {"".join(metric_rows)}'''

    return _svg_card(
        card_type="activity",
        title=f"{username} activity",
        colors=colors,
        hide_border=hide_border,
        rounded=rounded,
        body=body,
    )


def generate_error_svg(message: str) -> str:
    """Generate a 632x251 error SVG."""
    return f'''<svg width="632" height="251" viewBox="0 0 632 251" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .error-text {{ font: 400 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #f85149; }}
    </style>
  </defs>
  <rect width="632" height="251" rx="0" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="316" y="126" class="error-text" text-anchor="middle">{_esc(message)}</text>
</svg>'''
