#!/usr/bin/env python
"""Generate all required iOS icon and splash screen sizes from the SVG source."""
import cairosvg
import pathlib

SVG = """<svg width="1024" height="1024" viewBox="0 0 680 680" xmlns="http://www.w3.org/2000/svg">
<style>
  .bg { fill: #1a3a5c; }
  .ball-top { fill: #00BCD4; }
  .ball-bottom { fill: #0d2a42; }
  .ball-center { fill: #0d2a42; stroke: #00BCD4; stroke-width: 10; }
  .ball-inner { fill: #1a3a5c; }
  .qmark { fill: #FFCC00; font-family: sans-serif; font-weight: 500; font-size: 180px; text-anchor: middle; }
  .wrench { fill: #FFCC00; }
</style>
<defs>
  <clipPath id="top-clip"><rect x="0" y="0" width="680" height="340"/></clipPath>
  <clipPath id="bot-clip"><rect x="0" y="340" width="680" height="340"/></clipPath>
  <clipPath id="ball-clip"><circle cx="340" cy="340" r="260"/></clipPath>
</defs>
<rect x="0" y="0" width="680" height="680" fill="#1a3a5c"/>
<circle cx="340" cy="340" r="260" class="ball-top" clip-path="url(#top-clip)"/>
<circle cx="340" cy="340" r="260" class="ball-bottom" clip-path="url(#bot-clip)"/>
<line x1="80" y1="340" x2="600" y2="340" fill="none" stroke="#0d2a42" stroke-width="32"/>
<circle cx="340" cy="340" r="60" class="ball-center"/>
<circle cx="340" cy="340" r="42" class="ball-inner"/>
<text x="340" y="295" class="qmark">?</text>
<g class="wrench" clip-path="url(#ball-clip)">
  <g transform="translate(340, 390) rotate(-45)">
    <rect x="-18" y="-15" width="36" height="130" rx="10"/>
    <rect x="-28" y="-90" width="56" height="85" rx="5"/>
    <rect x="-46" y="-116" width="30" height="46" rx="8"/>
    <rect x="16" y="-116" width="30" height="46" rx="8"/>
  </g>
</g>
<path d="M 160 220 A 210 210 0 0 1 420 110" fill="none" stroke="white" stroke-width="6" stroke-linecap="round" opacity="0.15"/>
</svg>"""

SVG_TRANSPARENT = """<svg width="1024" height="1024" viewBox="0 0 680 680" xmlns="http://www.w3.org/2000/svg">
<style>
  .ball-top { fill: #00BCD4; }
  .ball-bottom { fill: #0d2a42; }
  .ball-center { fill: #0d2a42; stroke: #00BCD4; stroke-width: 10; }
  .ball-inner { fill: #1a3a5c; }
  .qmark { fill: #FFCC00; font-family: sans-serif; font-weight: 500; font-size: 180px; text-anchor: middle; }
  .wrench { fill: #FFCC00; }
</style>
<defs>
  <clipPath id="top-clip"><rect x="0" y="0" width="680" height="340"/></clipPath>
  <clipPath id="bot-clip"><rect x="0" y="340" width="680" height="340"/></clipPath>
  <clipPath id="ball-clip"><circle cx="340" cy="340" r="260"/></clipPath>
</defs>
<circle cx="340" cy="340" r="260" class="ball-top" clip-path="url(#top-clip)"/>
<circle cx="340" cy="340" r="260" class="ball-bottom" clip-path="url(#bot-clip)"/>
<line x1="80" y1="340" x2="600" y2="340" fill="none" stroke="#0d2a42" stroke-width="32"/>
<circle cx="340" cy="340" r="60" class="ball-center"/>
<circle cx="340" cy="340" r="42" class="ball-inner"/>
<text x="340" y="295" class="qmark">?</text>
<g class="wrench" clip-path="url(#ball-clip)">
  <g transform="translate(340, 390) rotate(-45)">
    <rect x="-18" y="-15" width="36" height="130" rx="10"/>
    <rect x="-28" y="-90" width="56" height="85" rx="5"/>
    <rect x="-46" y="-116" width="30" height="46" rx="8"/>
    <rect x="16" y="-116" width="30" height="46" rx="8"/>
  </g>
</g>
<path d="M 160 220 A 210 210 0 0 1 420 110" fill="none" stroke="white" stroke-width="6" stroke-linecap="round" opacity="0.15"/>
</svg>"""

out_dir = pathlib.Path("src/gobattlekit/resources")
out_dir.mkdir(exist_ok=True)

icon_bytes = SVG.encode("utf-8")
splash_bytes = SVG_TRANSPARENT.encode("utf-8")

# iOS icon sizes required by briefcase
ICON_SIZES = [20, 29, 40, 58, 60, 76, 80, 87, 120, 152, 167, 180, 640, 1024, 1280, 1920]
for size in ICON_SIZES:
    out_path = out_dir / f"icon-{size}.png"
    cairosvg.svg2png(bytestring=icon_bytes, write_to=str(out_path),
                     output_width=size, output_height=size)
    print(f"Generated {out_path} ({size}x{size})")

# iOS splash sizes required by briefcase
SPLASH_SIZES = [640, 800, 1280, 1600, 1920, 2400]
for size in SPLASH_SIZES:
    out_path = out_dir / f"splash-{size}.png"
    cairosvg.svg2png(bytestring=splash_bytes, write_to=str(out_path),
                     output_width=size, output_height=size)
    print(f"Generated {out_path} ({size}x{size})")

print("Done!")
