#!/usr/bin/env python3
"""Apply profile typography and 8px display corners to contribution cards."""

import re
from pathlib import Path
from xml.etree import ElementTree as ET


path = Path(__file__).resolve().parents[2] / "profile-3d-contrib/profile-3d.svg"
source = path.read_text(encoding="utf-8")
document = ET.fromstring(source)
x, y, width, height = map(float, document.get("viewBox").split())
style = """<style id="profile-typography">
text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
text[style*="font-size: 32px;"] { font-size: 26px !important; font-weight: 600 !important; }
text[style*="font-size: 24px;"] { font-size: 22px !important; }
</style>"""
source = re.sub(r'<style id="profile-typography">.*?</style>', "", source, flags=re.S)
source = re.sub(r'<defs id="profile-card-corners">.*?</defs>', "", source, flags=re.S)
source = source.replace(' clip-path="url(#profile-card-clip)"', "")
source = source.replace('<g id="profile-card-content">', "")
source = source.replace('</g><!--profile-card-content-->', "")
source = source.replace("</svg>", style + "</svg>")


def rounded_card(display_width, compact=False):
    # SVG units scale with the image; each size needs its own clipping radius.
    radius = 8 * width / display_width
    clip = (
        '<defs id="profile-card-corners"><clipPath id="profile-card-clip">'
        f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
        f'rx="{radius:.6f}"/></clipPath></defs>'
    )
    opening = re.search(r'<svg\b[^>]*>', source).group()
    replacement = opening
    if compact:
        replacement = re.sub(r'\bwidth="[^"]+"', f'width="{display_width}"', replacement)
        replacement = re.sub(r'\bheight="[^"]+"', f'height="{height * display_width / width:g}"', replacement)
    body = source[source.index(opening) + len(opening):source.rindex("</svg>")]
    return (
        replacement + clip
        + '<g id="profile-card-content" clip-path="url(#profile-card-clip)">'
        + body + '</g><!--profile-card-content--></svg>'
    )


path.write_text(rounded_card(808), encoding="utf-8")
path.with_name("profile-3d-compact.svg").write_text(rounded_card(384, compact=True), encoding="utf-8")
