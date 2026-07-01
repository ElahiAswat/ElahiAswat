#!/usr/bin/env python3
"""
Builds a self-hosted SVG contribution heatmap -- no third-party image service.
Pulls your own contribution calendar via the GraphQL API and draws the grid.

Requires: GITHUB_TOKEN, GITHUB_USER
Writes to: assets/contributions.svg
"""

import os
import requests
from datetime import datetime

GRAPHQL_URL = "https://api.github.com/graphql"
TOKEN = os.environ["GITHUB_TOKEN"]
USER = os.environ["GITHUB_USER"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

CELL = 11
GAP = 3
LEVELS = [0, 1, 3, 6, 10]  # thresholds for shading buckets
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def get_calendar():
    resp = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": QUERY, "variables": {"login": USER}},
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def bucket(count):
    level = 0
    for i, threshold in enumerate(LEVELS):
        if count >= threshold:
            level = i
    return level


def build_svg(calendar):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]

    width = len(weeks) * (CELL + GAP) + GAP
    height = 7 * (CELL + GAP) + GAP + 24  # extra row for the total label

    cells = []
    for w, week in enumerate(weeks):
        for d, day in enumerate(week["contributionDays"]):
            count = day["contributionCount"]
            color = COLORS[bucket(count)]
            x = GAP + w * (CELL + GAP)
            y = GAP + d * (CELL + GAP)
            cells.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}"><title>{day["date"]}: {count} contributions</title></rect>'
            )

    label_y = height - 6
    label = f'<text x="{GAP}" y="{label_y}" font-family="Segoe UI, Helvetica, sans-serif" ' \
            f'font-size="12" fill="#8b949e">{total} contributions in the last year</text>'

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  {''.join(cells)}
  {label}
</svg>"""


def main():
    calendar = get_calendar()
    svg = build_svg(calendar)
    os.makedirs("assets", exist_ok=True)
    with open("assets/contributions.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("Wrote assets/contributions.svg")


if __name__ == "__main__":
    main()
