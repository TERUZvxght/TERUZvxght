#!/usr/bin/env python3
"""Publish only aggregate language counts from owned public and private repos."""

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import math
from pathlib import Path
import re
import subprocess


QUERY = """
query($login: String!, $endCursor: String) {
  viewer { login }
  user(login: $login) {
    repositories(first: 100, after: $endCursor,
                 ownerAffiliations: [OWNER], isFork: false) {
      nodes { isPrivate primaryLanguage { name color } }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""

PALETTES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "title": "#76b7ff",
             "text": "#c9d1d9", "muted": "#8b949e", "track": "#21262d"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "title": "#0969da",
              "text": "#24292f", "muted": "#57606a", "track": "#eaeef2"},
}


def fetch_pages(owner):
    # No repository names, URLs, descriptions, source, or credentials are queried.
    result = subprocess.run(
        ["gh", "api", "graphql", "--paginate", "--slurp",
         "-f", f"query={QUERY}", "-f", f"login={owner}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        # Never echo raw API errors or private response data into public logs.
        raise RuntimeError("GitHub query failed; check the language token and its expiration.")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError("GitHub returned an invalid response.") from None


def aggregate(pages, owner):
    counts = Counter()
    colors = {}
    private_seen = False
    if not pages:
        raise ValueError("No repository pages were returned.")
    for index, page in enumerate(pages):
        if page.get("errors"):
            raise ValueError("GitHub returned incomplete data.")
        data = page["data"]
        if data["viewer"]["login"].casefold() != owner.casefold():
            raise ValueError("The language token must belong to the profile owner.")
        connection = data["user"]["repositories"]
        if connection["pageInfo"]["hasNextPage"] != (index < len(pages) - 1):
            raise ValueError("Repository pagination is incomplete.")
        for repo in connection["nodes"]:
            private_seen |= repo["isPrivate"]
            language = repo["primaryLanguage"]
            if language is None:
                continue
            name = language["name"]
            counts[name] += 1
            color = language.get("color") or "#8b949e"
            colors[name] = color if re.fullmatch(r"#[0-9a-fA-F]{6}", color) else "#8b949e"
    if not private_seen:
        raise ValueError("No private repositories were visible; keeping the previous cards.")
    if not counts:
        raise ValueError("No repository languages were detected; keeping the previous cards.")
    return counts, colors


def segments(counts, colors):
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0].casefold()))
    displayed = [(name, count, colors[name]) for name, count in ordered[:7]]
    remainder = sum(count for _, count in ordered[7:])
    if remainder:
        displayed.append(("Other", remainder, "#8b949e"))
    return displayed


def render_card(counts, colors, theme, updated):
    palette = PALETTES[theme]
    total = sum(counts.values())
    rows = segments(counts, colors)
    accessible = "; ".join(f"{name}: {count} repositories" for name, count in sorted(counts.items()))
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="340" height="200" '
        'viewBox="0 0 340 200" role="img" aria-labelledby="title desc">',
        '<title id="title">Top Languages by Repo</title>',
        '<desc id="desc">Primary languages of owned public and private non-fork repositories. '
        + escape(accessible) + '. Repositories without a detected language are omitted.</desc>',
        f'<rect x="0.5" y="0.5" width="339" height="199" rx="5" fill="{palette["bg"]}" stroke="{palette["border"]}"/>',
        '<g font-family="Segoe UI, Ubuntu, Helvetica Neue, sans-serif">',
        f'<text x="20" y="30" font-size="18" fill="{palette["title"]}">Top Languages by Repo</text>',
        f'<text x="20" y="48" font-size="10" fill="{palette["muted"]}">Public + private · non-fork repos</text>',
    ]
    cx, cy, radius = 257, 119, 54
    circumference = 2 * math.pi * radius
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{palette["track"]}" stroke-width="19"/>')
    offset = 0
    for index, (name, count, color) in enumerate(rows):
        y = 69 + index * 15
        svg.extend([
            f'<circle cx="24" cy="{y - 4}" r="4" fill="{color}"/>',
            f'<text x="34" y="{y}" font-size="11" fill="{palette["text"]}">{escape(name)}</text>',
            f'<text x="173" y="{y}" font-size="11" text-anchor="end" fill="{palette["text"]}">{count / total:.1%}</text>',
        ])
        arc = count / total * circumference
        svg.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" '
            f'stroke-width="19" stroke-dasharray="{arc:.6f} {circumference:.6f}" '
            f'stroke-dashoffset="{-offset:.6f}" transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += arc
    svg.extend([
        f'<text x="{cx}" y="{cy + 3}" font-size="23" text-anchor="middle" fill="{palette["text"]}">{total}</text>',
        f'<text x="{cx}" y="{cy + 19}" font-size="10" text-anchor="middle" fill="{palette["muted"]}">repos</text>',
        f'<text x="20" y="189" font-size="9" fill="{palette["muted"]}">Updated {escape(updated)}</text>',
        '</g></svg>\n',
    ])
    return "\n".join(svg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="TERUZvxght")
    parser.add_argument("--output-dir", type=Path, default=Path("assets"))
    args = parser.parse_args()
    counts, colors = aggregate(fetch_pages(args.owner), args.owner)
    updated = datetime.now(timezone.utc).date().isoformat()
    cards = {theme: render_card(counts, colors, theme, updated) for theme in PALETTES}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for theme, svg in cards.items():
        destination = args.output_dir / f"languages-{theme}.svg"
        temporary = destination.with_suffix(".svg.tmp")
        temporary.write_text(svg, encoding="utf-8")
        temporary.replace(destination)
    print("Updated language cards using aggregate data only.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError, TypeError) as exc:
        # These messages are controlled here and never contain API responses.
        print(f"Language update stopped: {type(exc).__name__}.")
        raise SystemExit(1) from None
