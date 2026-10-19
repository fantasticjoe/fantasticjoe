#!/usr/bin/env python3
"""Refresh the star counts embedded in the profile's project cards."""

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
SVG = "http://www.w3.org/2000/svg"
STAR_GROUP = re.compile(
    r"<g\b(?P<attributes>(?=[^>]*\bid=[\"']project-stars[\"'])[^>]*)>"
    r"(?P<body>.*?)</g>",
    re.S,
)
STAR_TEXT = re.compile(r"(<text\b[^>]*>)[^<]*(</text>)", re.S)
ARIA_LABEL = re.compile(r"\baria-label=([\"']).*?\1", re.S)


def read_cards(directory):
    cards = []
    for path in sorted(directory.glob("*.svg")):
        source = path.read_text(encoding="utf-8")
        document = ET.fromstring(source)
        groups = document.findall(f".//{{{SVG}}}g[@id='project-stars']")
        if not groups:
            continue
        if len(groups) != 1:
            raise ValueError(f"{path.name}: expected one project-stars group")
        group = groups[0]
        repository = group.get("data-repository", "")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError(f"{path.name}: invalid data-repository")
        if len(group.findall(f".//{{{SVG}}}text")) != 1 or group.findall(f".//{{{SVG}}}g"):
            raise ValueError(f"{path.name}: expected one star count and no nested groups")
        cards.append((path, source, repository))
    if not cards:
        raise ValueError("No project cards contain star counts")
    return cards


def fetch_stars(repository):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "fantasticjoe-profile-stars",
    }
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/repos/{repository}", headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            data = json.load(response)
    except HTTPError as error:
        raise ValueError(f"{repository}: GitHub API returned HTTP {error.code}") from error
    except URLError as error:
        raise ValueError(f"{repository}: could not reach the GitHub API") from error
    count = data.get("stargazers_count") if isinstance(data, dict) else None
    if type(count) is not int or count < 0:
        raise ValueError(f"{repository}: missing or invalid stargazers_count")
    if data.get("full_name", "").casefold() != repository.casefold():
        raise ValueError(f"{repository}: API response names a different repository")
    return count


def render_count(source, count):
    matches = list(STAR_GROUP.finditer(source))
    if len(matches) != 1:
        raise ValueError("Expected one editable project-stars group")
    group = matches[0]
    label = f"{count:,} GitHub stars"
    attributes = group["attributes"]
    if ARIA_LABEL.search(attributes):
        attributes = ARIA_LABEL.sub(f'aria-label="{label}"', attributes)
    else:
        attributes += f' aria-label="{label}"'
    body, replacements = STAR_TEXT.subn(lambda match: f"{match[1]}{count:,}{match[2]}", group["body"])
    if replacements != 1:
        raise ValueError("Expected one editable star-count text element")
    updated = source[:group.start()] + f"<g{attributes}>{body}</g>" + source[group.end():]
    ET.fromstring(updated)
    return updated


def main():
    cards = read_cards(ROOT / "assets/projects")
    # Validate every response and rendered card before changing any files.
    counts = {repository: fetch_stars(repository) for repository in sorted({card[2] for card in cards})}
    updates = [(path, source, render_count(source, counts[repository])) for path, source, repository in cards]
    changed = 0
    for path, source, updated in updates:
        if source != updated:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    print("; ".join(f"{repository}: {count:,} stars" for repository, count in counts.items()))
    print(f"Updated {changed} of {len(cards)} project cards.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, ET.ParseError) as error:
        print(f"Star update failed: {error}", file=sys.stderr)
        sys.exit(1)
