#!/usr/bin/env python3
"""Style the desktop contribution graph and render a readable compact card."""

import re
from copy import deepcopy
from html import escape
from math import radians, tan
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


def rounded_card(display_width):
    # SVG units scale with the image; each size needs its own clipping radius.
    radius = 8 * width / display_width
    clip = (
        '<defs id="profile-card-corners"><clipPath id="profile-card-clip">'
        f'<rect x="{x:g}" y="{y:g}" width="{width:g}" height="{height:g}" '
        f'rx="{radius:.6f}"/></clipPath></defs>'
    )
    opening = re.search(r'<svg\b[^>]*>', source).group()
    body = source[source.index(opening) + len(opening):source.rindex("</svg>")]
    return (
        opening + clip
        + '<g id="profile-card-content" clip-path="url(#profile-card-clip)">'
        + body + '</g><!--profile-card-content--></svg>'
    )


def compact_card(document):
    """Keep the original calendar geometry, with a readable native-size summary."""
    namespace = "http://www.w3.org/2000/svg"

    def tag(name):
        return f"{{{namespace}}}{name}"

    cube_class = re.compile(r"cont-(top|left|right)-\d+")

    def is_cube(group):
        return (
            group.tag == tag("g") and len(group) == 3
            and all(face.tag == tag("rect") and cube_class.fullmatch(face.get("class", "")) for face in group)
        )

    fields = [group for group in document.iter(tag("g")) if any(is_cube(child) for child in group)]
    if len(fields) != 1 or not all(is_cube(child) for child in fields[0]):
        raise ValueError("Expected one contribution calendar containing only cube groups")
    field = fields[0]
    if field.attrib:
        raise ValueError("Unexpected transform or attributes on the contribution calendar")

    # These are the transforms emitted for cube faces by the pinned upstream action.
    # Measure their actual corners so every cube fits, including unusually tall days.
    def transform(points, value):
        operations = list(re.finditer(r"(translate|scale|skewX|skewY)\(([^()]*)\)", value))
        if re.sub(r"(translate|scale|skewX|skewY)\([^()]*\)", "", value).strip(" ,\t\n"):
            raise ValueError(f"Unsupported cube transform: {value}")
        for operation in reversed(operations):
            name = operation[1]
            values = [float(part) for part in re.split(r"[\s,]+", operation[2].strip())]
            if name in {"translate", "scale"} and len(values) in {1, 2}:
                a = values[0]
                b = values[1] if len(values) == 2 else (a if name == "scale" else 0)
                points = [(x + a, y + b) if name == "translate" else (x * a, y * b) for x, y in points]
            elif name in {"skewX", "skewY"} and len(values) == 1:
                slope = tan(radians(values[0]))
                points = [(x + y * slope, y) if name == "skewX" else (x, y + x * slope) for x, y in points]
            else:
                raise ValueError(f"Invalid cube transform: {operation[0]}")
        return points

    points = []
    for cube in field:
        for face in cube:
            left, top, face_width, face_height = (float(face.get(key, "0")) for key in ("x", "y", "width", "height"))
            corners = [(left, top), (left + face_width, top), (left, top + face_height), (left + face_width, top + face_height)]
            points.extend(transform(transform(corners, face.get("transform", "")), cube.get("transform", "")))
    left, top = min(x for x, _ in points), min(y for _, y in points)
    right, bottom = max(x for x, _ in points), max(y for _, y in points)
    if right <= left or bottom <= top:
        raise ValueError("Invalid contribution calendar dimensions")

    summaries = [group for group in document.iter(tag("g")) if any(
        child.tag == tag("text") and (child.text or "").strip() == "contributions" for child in group
    )]
    if len(summaries) != 1:
        raise ValueError("Expected one contribution summary")
    labels = summaries[0].findall(tag("text"))
    if len(labels) != 5 or (labels[1].text or "").strip() != "contributions":
        raise ValueError("Expected contribution, star, fork, and date values")

    def count(element):
        # .text avoids counting a repeated nested <title> a second time.
        title = element.find(tag("title"))
        value = (title.text if title is not None else element.text) or ""
        if not re.fullmatch(r"\d[\d,]*", value.strip()):
            raise ValueError(f"Invalid activity total: {value}")
        return int(value.replace(",", ""))

    contributions, stars, forks = (count(labels[index]) for index in (0, 2, 3))
    period = (labels[4].text or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2} / \d{4}-\d{2}-\d{2}", period):
        raise ValueError(f"Invalid contribution date range: {period}")
    styles = "\n".join(element.text or "" for element in document.iter(tag("style")) if not element.get("id"))
    for name in {face.get("class") for cube in field for face in cube}:
        if not re.search(r"\." + re.escape(name) + r"\s*\{", styles):
            raise ValueError(f"Missing contribution cube color: {name}")

    ET.register_namespace("", namespace)
    calendar = ET.tostring(deepcopy(field), encoding="unicode")
    # A nested SVG isolates the old geometry from text laid out in native 384px units.
    viewbox = f"{left - 2:.3f} {top - 2:.3f} {right - left + 4:.3f} {bottom - top + 4:.3f}"
    description = f"{contributions:,} contributions; {stars:,} total stars; {forks:,} total forks. {period}."
    return f'''<svg xmlns="{namespace}" width="384" height="348" viewBox="0 0 384 348" role="img" aria-labelledby="title description">
<title id="title">Contribution activity</title>
<desc id="description">{escape(description)}</desc>
<style>{styles}
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }}
</style>
<rect width="384" height="348" rx="8" fill="#1F222E"/>
<text x="20" y="31" font-size="16" font-weight="600" fill="#53D6CA">Contribution activity</text>
<text x="20" y="54" font-size="14" fill="#A6ACCD">{escape(period.replace(" / ", " – "))}</text>
<svg x="20" y="72" width="344" height="192" viewBox="{viewbox}" preserveAspectRatio="xMidYMid meet" aria-hidden="true">{calendar}</svg>
<path d="M20 279H364" stroke="#34394D"/>
<g fill="#F3F4F6" font-size="20" font-weight="600">
  <text x="20" y="307">{contributions:,}</text>
  <text x="156" y="307">{stars:,}</text>
  <text x="270" y="307">{forks:,}</text>
</g>
<g fill="#A6ACCD" font-size="16">
  <text x="20" y="330">Contributions</text>
  <text x="156" y="330">Total stars</text>
  <text x="270" y="330">Total forks</text>
</g>
</svg>
'''


desktop = rounded_card(808)
compact = compact_card(document)
# Validate both variants before replacing either output.
ET.fromstring(desktop)
ET.fromstring(compact)
path.write_text(desktop, encoding="utf-8")
path.with_name("profile-3d-compact.svg").write_text(compact, encoding="utf-8")
