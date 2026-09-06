#!/usr/bin/env python3
"""Generate aggregate Stats cards, including accessible private contributions."""

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import subprocess

from update_languages import PALETTES


SUMMARY_QUERY = """
query($login: String!, $endCursor: String) {
  viewer { login }
  user(login: $login) {
    pullRequests(first: 1) { totalCount }
    issues(first: 1) { totalCount }
    repositoriesContributedTo(first: 1, includeUserRepositories: true,
      contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) { totalCount }
    contributionsCollection { contributionYears }
    repositories(first: 100, after: $endCursor,
      ownerAffiliations: [OWNER], isFork: false) {
      nodes { isPrivate stargazerCount }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""

COMMITS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
"""

ROWS = (("stars", "Total Stars"), ("commits", "Total Commits"),
        ("prs", "Total PRs"), ("issues", "Total Issues"),
        ("contributed_to", "Contributed to"))


def run_gh(arguments):
    result = subprocess.run(["gh", "api", "graphql", *arguments],
                            capture_output=True, text=True, check=False, timeout=120)
    if result.returncode:
        raise RuntimeError("GitHub query failed; keeping previous Stats cards.")
    return result.stdout


def require_owner(data, owner):
    if data["viewer"]["login"].casefold() != owner.casefold():
        raise ValueError("The Stats token must belong to the profile owner.")


def validate_token_response(response, owner):
    headers, separator, body = response.replace("\r\n", "\n").partition("\n\n")
    if not separator:
        raise ValueError("Missing token scope information.")
    fields = dict(line.lower().split(":", 1) for line in headers.splitlines() if ":" in line)
    scopes = {scope.strip() for scope in fields.get("x-oauth-scopes", "").split(",")}
    if "repo" not in scopes or not scopes.intersection({"read:user", "user"}):
        raise ValueError("Private Stats requires repo and read:user scopes.")
    page = json.loads(body)
    if page.get("errors"):
        raise ValueError("GitHub returned incomplete data.")
    require_owner(page["data"], owner)


def nonnegative_int(value):
    if type(value) is not int or value < 0:
        raise ValueError("Invalid aggregate count.")
    return value


def aggregate_summary(pages, owner, current_year):
    if not pages:
        raise ValueError("No repository pages were returned.")
    stats = {"stars": 0}
    private_seen = False
    years = None
    for index, page in enumerate(pages):
        if page.get("errors"):
            raise ValueError("GitHub returned incomplete data.")
        data = page["data"]
        require_owner(data, owner)
        user = data["user"]
        if index == 0:
            stats.update(prs=nonnegative_int(user["pullRequests"]["totalCount"]),
                         issues=nonnegative_int(user["issues"]["totalCount"]),
                         contributed_to=nonnegative_int(user["repositoriesContributedTo"]["totalCount"]))
            years = user["contributionsCollection"]["contributionYears"]
            if (not years or len(set(years)) != len(years)
                    or any(type(year) is not int or not 2008 <= year <= current_year for year in years)):
                raise ValueError("Invalid contribution years.")
        connection = user["repositories"]
        if connection["pageInfo"]["hasNextPage"] != (index < len(pages) - 1):
            raise ValueError("Repository pagination is incomplete.")
        for repo in connection["nodes"]:
            private_seen |= repo["isPrivate"]
            stats["stars"] += nonnegative_int(repo["stargazerCount"])
    if not private_seen:
        raise ValueError("No private repositories were visible.")
    return stats, sorted(years)


def year_bounds(year, now):
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = min(datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc), now)
    if start > end:
        raise ValueError("Contribution year is in the future.")
    return start.isoformat(), end.isoformat()


def commit_count(page):
    if page.get("errors"):
        raise ValueError("GitHub returned incomplete data.")
    collection = page["data"]["user"]["contributionsCollection"]
    # Restricted contributions mix commits, PRs, issues, and other activity.
    # Never add them to commits or publish a silently incomplete result.
    if nonnegative_int(collection["restrictedContributionsCount"]):
        raise ValueError("Some contribution details remain inaccessible.")
    return nonnegative_int(collection["totalCommitContributions"])


def fetch_stats(owner, now):
    validate_token_response(run_gh(["--include", "-f", "query=query { viewer { login } }"]), owner)
    pages = json.loads(run_gh(["--paginate", "--slurp", "-f", f"query={SUMMARY_QUERY}",
                              "-f", f"login={owner}"]))
    stats, years = aggregate_summary(pages, owner, now.year)
    stats["commits"] = 0
    for year in years:
        start, end = year_bounds(year, now)
        page = json.loads(run_gh(["-f", f"query={COMMITS_QUERY}", "-f", f"login={owner}",
                                  "-f", f"from={start}", "-f", f"to={end}"]))
        stats["commits"] += commit_count(page)
    return stats


def render_card(stats, theme, updated):
    palette = PALETTES[theme]
    description = "; ".join(f"{label}: {nonnegative_int(stats[key]):,}" for key, label in ROWS)
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="340" height="200" '
        'viewBox="0 0 340 200" role="img" aria-labelledby="title desc">',
        '<title id="title">GitHub Stats</title>',
        '<desc id="desc">Public and accessible private statistics. ' + escape(description)
        + '. Commits follow GitHub contribution rules, summed across all contribution years.</desc>',
        f'<rect x="0.5" y="0.5" width="339" height="199" rx="5" fill="{palette["bg"]}" stroke="{palette["border"]}"/>',
        '<g font-family="Segoe UI, Ubuntu, Helvetica Neue, sans-serif">',
        f'<text x="20" y="30" font-size="18" fill="{palette["title"]}">Stats</text>',
        f'<text x="20" y="48" font-size="10" fill="{palette["muted"]}">Public + private</text>',
    ]
    for index, (key, label) in enumerate(ROWS):
        y = 73 + index * 24
        svg.extend([
            f'<circle cx="24" cy="{y - 4}" r="3" fill="{palette["title"]}"/>',
            f'<text x="37" y="{y}" font-size="13" fill="{palette["text"]}">{label}</text>',
            f'<text x="314" y="{y}" font-size="13" text-anchor="end" font-weight="600" fill="{palette["text"]}">{stats[key]:,}</text>',
        ])
    svg.extend([
        f'<text x="20" y="189" font-size="9" fill="{palette["muted"]}">Updated {escape(updated)}</text>',
        '</g></svg>\n',
    ])
    return "\n".join(svg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="TERUZvxght")
    parser.add_argument("--output-dir", type=Path, default=Path("assets"))
    args = parser.parse_args()
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stats = fetch_stats(args.owner, now)
    cards = {theme: render_card(stats, theme, now.date().isoformat()) for theme in PALETTES}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for theme, svg in cards.items():
        destination = args.output_dir / f"stats-{theme}.svg"
        temporary = destination.with_suffix(".svg.tmp")
        temporary.write_text(svg, encoding="utf-8")
        temporary.replace(destination)
    print("Updated Stats cards using aggregate data only.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(f"Stats update stopped: {type(exc).__name__}.")
        raise SystemExit(1) from None
