#!/usr/bin/env python3
"""
Builds a self-hosted SVG of repo cards -- no third-party image service.
Pulls your own repos via the REST API and draws simple cards.

Requires: GITHUB_TOKEN, GITHUB_USER
Writes to: assets/repo-cards.svg
"""

import os
import requests

API = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
USER = os.environ["GITHUB_USER"]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

CARD_WIDTH = 280
CARD_HEIGHT = 100
CARDS_PER_ROW = 2
PADDING = 16
MAX_REPOS = 6  # how many cards to show


def get_repos():
    resp = requests.get(
        f"{API}/user/repos",
        headers=HEADERS,
        params={"per_page": 100, "affiliation": "owner", "sort": "updated"},
    )
    resp.raise_for_status()
    repos = [r for r in resp.json() if not r["fork"]]
    return repos[:MAX_REPOS]


def escape(text):
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def truncate(text, length):
    if not text:
        return ""
    return text if len(text) <= length else text[: length - 1] + "…"


def build_card(repo, x, y):
    name = escape(repo["name"])
    desc = escape(truncate(repo.get("description") or "No description", 42))
    lang = escape(repo.get("language") or "—")
    stars = repo.get("stargazers_count", 0)

    return f"""
    <g transform="translate({x},{y})">
      <rect width="{CARD_WIDTH}" height="{CARD_HEIGHT}" rx="8"
            fill="var(--card-bg, #0d1117)" stroke="var(--card-border, #30363d)" stroke-width="1"/>
      <text x="16" y="26" font-family="Segoe UI, Helvetica, sans-serif" font-size="15"
            font-weight="600" fill="var(--link-color, #58a6ff)">{name}</text>
      <text x="16" y="48" font-family="Segoe UI, Helvetica, sans-serif" font-size="12"
            fill="var(--text-color, #8b949e)">{desc}</text>
      <circle cx="20" cy="78" r="5" fill="var(--lang-dot, #f1e05a)"/>
      <text x="32" y="82" font-family="Segoe UI, Helvetica, sans-serif" font-size="11"
            fill="var(--text-color, #8b949e)">{lang}</text>
      <text x="{CARD_WIDTH - 16}" y="82" font-family="Segoe UI, Helvetica, sans-serif" font-size="11"
            fill="var(--text-color, #8b949e)" text-anchor="end">★ {stars}</text>
    </g>"""


def build_svg(repos):
    rows = (len(repos) + CARDS_PER_ROW - 1) // CARDS_PER_ROW
    width = CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW + 1) * PADDING
    height = rows * CARD_HEIGHT + (rows + 1) * PADDING

    cards = []
    for i, repo in enumerate(repos):
        col = i % CARDS_PER_ROW
        row = i // CARDS_PER_ROW
        x = PADDING + col * (CARD_WIDTH + PADDING)
        y = PADDING + row * (CARD_HEIGHT + PADDING)
        cards.append(build_card(repo, x, y))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}" font-family="Segoe UI, Helvetica, sans-serif">
  <style>
    :root {{ --card-bg: #0d1117; --card-border: #30363d; --text-color: #8b949e; --link-color: #58a6ff; --lang-dot: #f1e05a; }}
  </style>
  {''.join(cards)}
</svg>"""


def main():
    repos = get_repos()
    svg = build_svg(repos)
    os.makedirs("assets", exist_ok=True)
    with open("assets/repo-cards.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote assets/repo-cards.svg with {len(repos)} repo cards.")


if __name__ == "__main__":
    main()
