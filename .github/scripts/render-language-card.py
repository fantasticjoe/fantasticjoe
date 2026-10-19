#!/usr/bin/env python3
"""Render profile-sized language cards from the Metrics action's SVG data."""

import argparse
import re
from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET


SVG = "http://www.w3.org/2000/svg"
HTML = "http://www.w3.org/1999/xhtml"
ROOT = Path(__file__).resolve().parents[2]


def read_languages(source):
    document = ET.parse(source).getroot()
    entries = []
    for field in document.findall(f".//{{{HTML}}}div"):
        if set(field.get("class", "").split()) != {"field", "language", "details"}:
            continue
        label = field.find(f"{{{HTML}}}div")
        details = field.find(f"{{{HTML}}}small")
        if label is None or details is None:
            raise ValueError("Language name or percentage is missing")
        name = " ".join(" ".join(label.itertext()).split())
        percent = re.search(r"(\d+(?:\.\d+)?)%", " ".join(details.itertext()))
        dot = label.find(f".//{{{SVG}}}path")
        color = dot.get("fill", "") if dot is not None else ""
        if not name or percent is None or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ValueError(f"Invalid language entry: {name}")
        entries.append((name, percent.group(1), color))
    if not entries or sum(float(entry[1]) for entry in entries) < 98:
        raise ValueError("Expected a complete language distribution including Other")
    headings = " ".join(" ".join(node.itertext()) for node in document.findall(f".//{{{HTML}}}h2"))
    count = re.search(r"(\d+)\s+Languages", headings, re.IGNORECASE)
    entries.sort(key=lambda entry: (entry[0].casefold() == "other", -float(entry[1])))
    return entries, int(count.group(1)) if count else None


def render(entries, count, compact=False):
    width, padding, columns = (384, 20, 1) if compact else (808, 24, 2)
    label_size, percent_size, row_gap = (16, 14, 26) if compact else (14, 13, 24)
    rows = (len(entries) + columns - 1) // columns
    height = 82 + (rows - 1) * row_gap + 22
    inner = width - padding * 2
    column_gap = 32
    cell = (inner - column_gap * (columns - 1)) / columns
    description = "; ".join(f"{name}: {percent}%" for name, percent, _ in entries)
    parts = [
        f'<svg xmlns="{SVG}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
        '<title id="title">Languages across my repositories</title>',
        f'<desc id="description">{escape(description)}</desc>',
        '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;fill:#F3F4F6}.muted{fill:#A6ACCD}</style>',
        f'<rect width="{width}" height="{height}" rx="8" fill="#1F222E"/>',
        f'<text x="{padding}" y="30" font-size="{label_size}" font-weight="600" style="fill:#53D6CA">Languages</text>',
    ]
    if count is not None:
        parts.append(f'<text x="{width - padding}" y="30" text-anchor="end" font-size="12" class="muted">{count} languages</text>')
    parts.append(f'<defs><clipPath id="bar"><rect x="{padding}" y="46" width="{inner}" height="6" rx="3"/></clipPath></defs>')
    parts.append('<g clip-path="url(#bar)">')
    total = sum(float(entry[1]) for entry in entries)
    position = float(padding)
    for _, percent, color in entries:
        length = float(percent) / total * inner
        parts.append(f'<rect x="{position:.3f}" y="46" width="{length + 0.05:.3f}" height="6" fill="{color}"/>')
        position += length
    parts.append('</g>')
    for index, (name, percent, color) in enumerate(entries):
        x = padding + (index % columns) * (cell + column_gap)
        y = 82 + (index // columns) * row_gap
        parts.extend([
            f'<circle cx="{x + 4:g}" cy="{y - 5}" r="3" fill="{color}"/>',
            f'<text x="{x + 16:g}" y="{y}" font-size="{label_size}">{escape(name)}</text>',
            f'<text x="{x + cell:g}" y="{y}" text-anchor="end" font-size="{percent_size}" class="muted">{percent}%</text>',
        ])
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    languages, count = read_languages(args.source)
    for name, compact in [("metrics-languages.svg", False), ("metrics-languages-compact.svg", True)]:
        (ROOT / name).write_text(render(languages, count, compact), encoding="utf-8")
