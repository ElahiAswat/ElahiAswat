#!/usr/bin/env python3
"""
Generates a single markdown table of language usage across ALL of your
GitHub repos, aggregated by total bytes:

    Language | Usage (bar) | %

Requires: GITHUB_TOKEN (repo read access) and GITHUB_USER env vars.
Writes the table between <!--LANG-STATS:START--> / <!--LANG-STATS:END-->
markers in README.md.
"""

import os
import sys
import requests
from collections import defaultdict

API = "https://api.github.com"
TOKEN = os.environ["GITHUB_TOKEN"]
USER = os.environ["GITHUB_USER"]
INCLUDE_FORKS = os.environ.get("INCLUDE_FORKS", "false").lower() == "true"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

BAR_LENGTH = 20
FILLED_CHAR = "█"
EMPTY_CHAR = "░"


def get_repos():
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"{API}/users/{USER}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    if not INCLUDE_FORKS:
        repos = [r for r in repos if not r["fork"]]
    return repos


def get_languages(repo_full_name):
    resp = requests.get(f"{API}/repos/{repo_full_name}/languages", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()  # {"Python": 12345, "HTML": 456, ...}


def render_bar(pct, length=BAR_LENGTH):
    filled = round((pct / 100) * length)
    filled = max(0, min(length, filled))
    return FILLED_CHAR * filled + EMPTY_CHAR * (length - filled)


def build_language_table(repos):
    totals = defaultdict(int)
    for repo in repos:
        langs = get_languages(repo["full_name"])
        for lang, b in langs.items():
            totals[lang] += b

    grand_total = sum(totals.values())
    rows = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)

    if not rows:
        return "No language data found."

    name_width = max(len(lang) for lang, _ in rows)

    lines = []
    for lang, b in rows:
        pct = (b / grand_total) * 100 if grand_total else 0
        bar = render_bar(pct)
        lines.append(f"{lang.ljust(name_width)}  {bar}  {pct:5.1f}%")
    return "```\n" + "\n".join(lines) + "\n```"


def inject_into_readme(table_md, readme_path="README.md"):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!--LANG-STATS:START-->"
    end_marker = "<!--LANG-STATS:END-->"

    block = f"{start_marker}\n\n{table_md}\n\n{end_marker}"

    if start_marker in content and end_marker in content:
        pre = content.split(start_marker)[0]
        post = content.split(end_marker)[1]
        new_content = pre + block + post
    else:
        new_content = content.rstrip() + "\n\n" + block + "\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    repos = get_repos()
    if not repos:
        print("No repos found (or all were filtered out).", file=sys.stderr)

    table_md = build_language_table(repos)
    inject_into_readme(table_md)
    print("README.md updated.")


if __name__ == "__main__":
    main()
