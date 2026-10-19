#!/usr/bin/env python3
"""Keep the generated contribution card's summary close to body text size."""

import re
from pathlib import Path
from xml.etree import ElementTree as ET


path = Path(__file__).resolve().parents[2] / "profile-3d-contrib/profile-3d.svg"
source = path.read_text(encoding="utf-8")
ET.fromstring(source)
style = """<style id="profile-typography">
text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
text[style*="font-size: 32px;"] { font-size: 26px !important; font-weight: 600 !important; }
text[style*="font-size: 24px;"] { font-size: 22px !important; }
</style>"""
source = re.sub(r'<style id="profile-typography">.*?</style>', "", source, flags=re.S)
source = source.replace("</svg>", style + "</svg>")
path.write_text(source, encoding="utf-8")
