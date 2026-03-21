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
  <clipPath id="top-clip"><rect x="100" y="100" width="480" height="240"/></clipPath>
  <clipPath id="bot-clip"><rect x="100" y="340" width="480" height="240"/></clipPath>
  <clipPath id="ball-clip"><circle cx="340" cy="340" r="220"/></clipPath>
</defs>
<rect x="40" y="40" width="600" height="600" rx="120" class="bg"/>
<circle cx="340" cy="340" r="220" class="ball-top" clip-path="url(#top-clip)"/>
<circle cx="340" cy="340" r="220" class="ball-bottom" clip-path="url(#bot-clip)"/>
<line x1="120" y1="340" x2="560" y2="340" fill="none" stroke="#0d2a42" stroke-width="28"/>
<circle cx="340" cy="340" r="52" class="ball-center"/>
<circle cx="340" cy="340" r="36" class="ball-inner"/>
<text x="340" y="308" class="qmark">?</text>
<g class="wrench" clip-path="url(#ball-clip)">
  <g transform="translate(340, 430) rotate(-45)">
    <rect x="-14" y="-10" width="28" height="100" rx="8"/>
    <rect x="-22" y="-70" width="44" height="68" rx="4"/>
    <rect x="-36" y="-90" width="24" height="36" rx="6"/>
    <rect x="12" y="-90" width="24" height="36" rx="6"/>
    <rect x="-14" y="-92" width="28" height="30" rx="2" fill="#0d2a42"/>
  </g>
</g>
<path d="M 180 240 A 180 180 0 0 1 390 125" fill="none" stroke="white" stroke-width="6" stroke-linecap="round" opacity="0.15"/>
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
  <clipPath id="top-clip"><rect x="100" y="100" width="480" height="240"/></clipPath>
  <clipPath id="bot-clip"><rect x="100" y="340" width="480" height="240"/></clipPath>
  <clipPath id="ball-clip"><circle cx="340" cy="340" r="220"/></clipPath>
</defs>
<circle cx="340" cy="340" r="220" class="ball-top" clip-path="url(#top-clip)"/>
<circle cx="340" cy="340" r="220" class="ball-bottom" clip-path="url(#bot-clip)"/>
<line x1="120" y1="340" x2="560" y2="340" fill="none" stroke="#0d2a42" stroke-width="28"/>
<circle cx="340" cy="340" r="52" class="ball-center"/>
<circle cx="340" cy="340" r="36" class="ball-inner"/>
<text x="340" y="308" class="qmark">?</text>
<g class="wrench" clip-path="url(#ball-clip)">
  <g transform="translate(340, 430) rotate(-45)">
    <rect x="-14" y="-10" width="28" height="100" rx="8"/>
    <rect x="-22" y="-70" width="44" height="68" rx="4"/>
    <rect x="-36" y="-90" width="24" height="36" rx="6"/>
    <rect x="12" y="-90" width="24" height="36" rx="6"/>
    <rect x="-14" y="-92" width="28" height="30" rx="2" fill="#0d2a42"/>
  </g>
</g>
</svg>"""

out_dir = pathlib.Path("src/pogoquiz/resources")
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
