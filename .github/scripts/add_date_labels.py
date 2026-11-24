#!/usr/bin/env python3
"""Inject month and weekday labels into the snake contribution SVGs.

Fetches the user's contribution calendar page to learn which grid column
each month starts at (GitHub renders the label row with colspan values),
then adds <text> elements matching GitHub's own label placement.
"""

import re
import sys
import urllib.request
from pathlib import Path

CELL = 16          # grid pitch in the snk svg
GRID_X = 2         # x of first column
GRID_Y = 2         # y of first row (Sunday)
MONTH_Y = -8       # baseline for month labels
LABEL_PAD = 24     # extra left margin for weekday labels

WEEKDAYS = [(1, "Mon"), (3, "Wed"), (5, "Fri")]  # GitHub shows these rows
FONT = "font-family='-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif' font-size='10'"


def month_columns(user: str) -> list[tuple[int, str]]:
    url = f"https://github.com/users/{user}/contributions"
    html = urllib.request.urlopen(url).read().decode()
    labels = []
    col = 0
    for m in re.finditer(
        r'ContributionCalendar-label" colspan="(\d+)"[^>]*>(.*?)</td>', html, re.S
    ):
        spans = re.findall(r"<span[^>]*>([^<]+)</span>", m.group(2))
        if spans:
            labels.append((col, spans[-1].strip()))
        col += int(m.group(1))
    return labels


def annotate(svg_path: Path, labels: list[tuple[int, str]]) -> None:
    svg = svg_path.read_text()
    dark = "dark" in svg_path.name
    color = "#8b949e" if dark else "#57606a"

    texts = [
        f"<text x='{GRID_X + col * CELL}' y='{MONTH_Y}' {FONT} fill='{color}'>{name}</text>"
        for col, name in labels
    ]
    for row, name in WEEKDAYS:
        y = GRID_Y + row * CELL + 10
        texts.append(
            f"<text x='{GRID_X - 4}' y='{y}' {FONT} fill='{color}' text-anchor='end'>{name}</text>"
        )

    svg = re.sub(
        r'viewBox="(-?[\d.]+) (-?[\d.]+) ([\d.]+) ([\d.]+)" width="([\d.]+)"',
        lambda m: (
            f'viewBox="{float(m.group(1)) - LABEL_PAD:g} {m.group(2)} '
            f'{float(m.group(3)) + LABEL_PAD:g} {m.group(4)}" '
            f'width="{float(m.group(5)) + LABEL_PAD:g}"'
        ),
        svg,
        count=1,
    )
    svg = svg.replace("</svg>", "<g>" + "".join(texts) + "</g></svg>")
    svg_path.write_text(svg)


if __name__ == "__main__":
    user, dist = sys.argv[1], Path(sys.argv[2])
    labels = month_columns(user)
    for svg in dist.glob("*.svg"):
        annotate(svg, labels)
        print(f"annotated {svg}")
