#!/usr/bin/env python3

import os
import sys
import requests
from collections import defaultdict

API = "https://api.github.com"

TOKEN = os.environ.get("GITHUB_TOKEN")
USER = os.environ.get("GITHUB_USER")
INCLUDE_FORKS = os.environ.get("INCLUDE_FORKS", "false").lower() == "true"

if not TOKEN:
    print("❌ GITHUB_TOKEN environment variable is missing.")
    sys.exit(1)

if not USER:
    print("❌ GITHUB_USER environment variable is missing.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

BAR_LENGTH = 20
FILLED_CHAR = "█"
EMPTY_CHAR = "░"


def api_get(url, **kwargs):
    r = requests.get(url, headers=HEADERS, **kwargs)

    print("\n========================================")
    print("GET:", r.url)
    print("Status:", r.status_code)

    if r.status_code != 200:
        print("Response:")
        print(r.text)

    r.raise_for_status()
    return r


def test_auth():
    print("\nTesting authentication...")

    user = api_get(f"{API}/user").json()

    print("✅ Authenticated as:", user["login"])


def get_repos():
    repos = []
    page = 1

    while True:
        resp = api_get(
            f"{API}/users/{USER}/repos",
            params={
                "per_page": 100,
                "page": page,
                "type": "owner",
            },
        )

        batch = resp.json()

        print(f"Fetched {len(batch)} repositories from page {page}")

        if not batch:
            break

        repos.extend(batch)
        page += 1

    if not INCLUDE_FORKS:
        repos = [r for r in repos if not r["fork"]]

    print(f"Total repositories used: {len(repos)}")

    return repos


def get_languages(repo_full_name):
    print(f"Getting languages for {repo_full_name}")

    resp = api_get(f"{API}/repos/{repo_full_name}/languages")

    return resp.json()


def render_bar(pct):
    filled = round((pct / 100) * BAR_LENGTH)
    filled = max(0, min(BAR_LENGTH, filled))
    return FILLED_CHAR * filled + EMPTY_CHAR * (BAR_LENGTH - filled)


def build_language_table(repos):
    totals = defaultdict(int)

    for repo in repos:
        langs = get_languages(repo["full_name"])

        for lang, bytes_used in langs.items():
            totals[lang] += bytes_used

    grand_total = sum(totals.values())

    rows = sorted(
        totals.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    lines = []

    for lang, bytes_used in rows:
        pct = (bytes_used / grand_total * 100) if grand_total else 0
        bar = render_bar(pct)

        lines.append(
            f"| {lang} | `{bar}` | {pct:.1f}% |"
        )

    return "\n".join(lines)


def inject_into_readme(table_md, readme_path="README.md"):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    start = "<!--LANG-STATS:START-->"
    end = "<!--LANG-STATS:END-->"

    block = f"{start}\n\n{table_md}\n\n{end}"

    if start in content and end in content:
        pre = content.split(start)[0]
        post = content.split(end)[1]
        new_content = pre + block + post
    else:
        new_content = content.rstrip() + "\n\n" + block + "\n"

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    test_auth()

    repos = get_repos()

    if not repos:
        print("No repositories found.")

    table = build_language_table(repos)

    inject_into_readme(table)

    print("\n✅ README updated successfully.")


if __name__ == "__main__":
    main()
