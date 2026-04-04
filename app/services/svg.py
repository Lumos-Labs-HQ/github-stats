def generate_stats_svg(username: str, total_contributions: int, current_streak: int, longest_streak: int) -> str:
    """Generate SVG card for GitHub stats"""
    
    svg = f'''<svg width="495" height="195" viewBox="0 0 495 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e1e4e8; }}
      .stat-label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: #8b949e; }}
      .stat-value {{ font: 600 25px 'Segoe UI', Ubuntu, Sans-Serif; fill: #e1e4e8; }}
      .streak-highlight {{ font: 600 25px 'Segoe UI', Ubuntu, Sans-Serif; fill: #fb8500; }}
    </style>
  </defs>
  
  <rect width="495" height="195" rx="4.5" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  
  <text x="25" y="35" class="header">{username}'s GitHub Stats</text>
  
  <g transform="translate(0, 70)">
    <g transform="translate(40, 0)">
      <text x="0" y="0" class="stat-label">Total Contributions</text>
      <text x="0" y="30" class="stat-value">{total_contributions:,}</text>
    </g>
    
    <g transform="translate(220, 0)">
      <circle cx="15" cy="15" r="40" fill="#fb850020" stroke="#fb8500" stroke-width="2"/>
      <text x="15" y="-30" class="stat-label" text-anchor="middle">Current Streak</text>
      <text x="15" y="5" class="streak-highlight" text-anchor="middle">{current_streak}</text>
      <text x="15" y="25" class="stat-label" text-anchor="middle">days</text>
    </g>
    
    <g transform="translate(360, 0)">
      <text x="0" y="0" class="stat-label">Longest Streak</text>
      <text x="0" y="30" class="stat-value">{longest_streak}</text>
      <text x="0" y="50" class="stat-label">days</text>
    </g>
  </g>
</svg>'''
    
    return svg

def generate_error_svg(message: str) -> str:
    """Generate error SVG"""
    
    svg = f'''<svg width="495" height="195" viewBox="0 0 495 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .error-text {{ font: 400 16px 'Segoe UI', Ubuntu, Sans-Serif; fill: #f85149; }}
    </style>
  </defs>
  
  <rect width="495" height="195" rx="4.5" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  
  <text x="247.5" y="100" class="error-text" text-anchor="middle">{message}</text>
</svg>'''
    
    return svg
