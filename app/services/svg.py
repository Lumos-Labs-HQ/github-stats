from typing import Optional


def _compact_number(n: int) -> str:
    """Format large numbers compactly: 1234 → '1.2k', 1234567 → '1.2M'."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def _esc(s: str) -> str:
    """Escape special XML characters for safe SVG embedding."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;")


def generate_stats_svg(
    username: str,
    total_contributions: int,
    current_streak: int,
    longest_streak: int,
    public_repos: int = 0,
    total_stars: int = 0,
    top_language: Optional[str] = None,
    first_contribution: Optional[str] = None,
    current_streak_start: Optional[str] = None,
    current_streak_end: Optional[str] = None,
    longest_streak_start: Optional[str] = None,
    longest_streak_end: Optional[str] = None,
) -> str:
    """Generate a 495x265 SVG stats card with streak date ranges."""

    lang_display = _esc(top_language) if top_language else "\u2014"

    # Date range labels shown under each stat
    contrib_range = f"Since {_esc(first_contribution)}" if first_contribution else ""
    cur_range = (
        f"{_esc(current_streak_start)} \u2013 {_esc(current_streak_end)}"
        if current_streak_start and current_streak_end else ""
    )
    long_range = (
        f"{_esc(longest_streak_start)} \u2013 {_esc(longest_streak_end)}"
        if longest_streak_start and longest_streak_end else ""
    )

    svg = f'''<svg width="495" height="265" viewBox="0 0 495 265" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e1e4e8; }}
      .stat-label {{ font: 400 13px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
      .stat-value {{ font: 700 28px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e1e4e8; }}
      .streak-highlight {{ font: 700 28px 'Segoe UI', Ubuntu, Sans-Serif; fill: #fb8500; }}
      .date-range {{ font: 400 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
      .secondary-label {{ font: 400 12px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
      .secondary-value {{ font: 600 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e1e4e8; }}
    </style>
  </defs>

  <rect width="495" height="265" rx="4.5" fill="#0d1117" stroke="#30363d" stroke-width="1"/>

  <!-- Header -->
  <text x="25" y="35" class="header">{_esc(username)}&apos;s GitHub Stats</text>

  <!-- Vertical dividers for row 1 -->
  <line x1="185" y1="58" x2="185" y2="155" stroke="#30363d" stroke-width="1"/>
  <line x1="330" y1="58" x2="330" y2="155" stroke="#30363d" stroke-width="1"/>

  <!-- Row 1: Total Contributions -->
  <g transform="translate(0, 65)">
    <text x="92" y="16" class="stat-label" text-anchor="middle">Total Contributions</text>
    <text x="92" y="52" class="stat-value" text-anchor="middle">{total_contributions:,}</text>
    <text x="92" y="68" class="date-range" text-anchor="middle">{contrib_range}</text>
  </g>

  <!-- Row 1: Current Streak -->
  <g transform="translate(185, 65)">
    <text x="72" y="16" class="stat-label" text-anchor="middle">Current Streak</text>
    <circle cx="72" cy="65" r="38" fill="#fb850015" stroke="#fb8500" stroke-width="2"/>
    <text x="72" y="55" class="streak-highlight" text-anchor="middle">{current_streak}</text>
    <text x="72" y="72" class="stat-label" text-anchor="middle">days</text>
    <text x="72" y="92" class="date-range" text-anchor="middle">{cur_range}</text>
  </g>

  <!-- Row 1: Longest Streak -->
  <g transform="translate(330, 65)">
    <text x="82" y="16" class="stat-label" text-anchor="middle">Longest Streak</text>
    <text x="82" y="52" class="stat-value" text-anchor="middle">{longest_streak}</text>
    <text x="82" y="68" class="stat-label" text-anchor="middle">days</text>
    <text x="82" y="84" class="date-range" text-anchor="middle">{long_range}</text>
  </g>

  <!-- Separator -->
  <line x1="25" y1="168" x2="470" y2="168" stroke="#30363d" stroke-width="1"/>

  <!-- Row 2: Public Repos / Stars / Top Language -->
  <g transform="translate(0, 188)">
    <g transform="translate(40, 0)">
      <text x="0" y="0" class="secondary-label">Public Repos</text>
      <text x="0" y="25" class="secondary-value">{public_repos}</text>
    </g>
    <g transform="translate(200, 0)">
      <text x="0" y="0" class="secondary-label">Total Stars</text>
      <text x="0" y="25" class="secondary-value">&#9733; {_compact_number(total_stars)}</text>
    </g>
    <g transform="translate(360, 0)">
      <text x="0" y="0" class="secondary-label">Top Language</text>
      <text x="0" y="25" class="secondary-value">{lang_display}</text>
    </g>
  </g>
</svg>'''

    return svg


def generate_error_svg(message: str) -> str:
    """Generate a 495x265 error SVG."""
    svg = f'''<svg width="495" height="265" viewBox="0 0 495 265" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .error-text {{ font: 400 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #f85149; }}
    </style>
  </defs>
  <rect width="495" height="265" rx="4.5" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="247.5" y="132" class="error-text" text-anchor="middle">{_esc(message)}</text>
</svg>'''
    return svg
