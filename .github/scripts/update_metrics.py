import json
import os
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

USERNAME = "AnjaniBeesu"
README = Path("README.md")
TOKEN = os.environ["GITHUB_TOKEN"]


def github_get(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "profile-metrics-workflow",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def search_count(query):
    encoded = urllib.parse.quote(query, safe=":+")
    return github_get(f"https://api.github.com/search/issues?q={encoded}&per_page=1")["total_count"]


def collect_languages():
    totals = defaultdict(int)
    page = 1
    while True:
        repos = github_get(
            f"https://api.github.com/users/{USERNAME}/repos?type=owner&per_page=100&page={page}"
        )
        if not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo.get("archived"):
                continue
            languages = github_get(repo["languages_url"])
            for language, byte_count in languages.items():
                totals[language] += byte_count
        if len(repos) < 100:
            break
        page += 1
    return totals


def render_languages(totals):
    total = sum(totals.values())
    if not total:
        return "_No public repository language data found yet._"
    rows = [
        "| Language | Share of code |",
        "|:--|--:|",
    ]
    for language, byte_count in sorted(totals.items(), key=lambda item: item[1], reverse=True):
        percentage = byte_count / total * 100
        rows.append(f"| {language} | {percentage:.1f}% |")
    return "\n".join(rows)


total_prs = search_count(f"type:pr author:{USERNAME}")
merged_prs = search_count(f"type:pr is:merged author:{USERNAME}")
open_prs = search_count(f"type:pr is:open author:{USERNAME}")
languages = collect_languages()

section = f"""<p align="center">
  <img src="https://img.shields.io/badge/PULL_REQUESTS-{total_prs}-FFFFFF?style=for-the-badge&labelColor=111111&color=FFFFFF" alt="{total_prs} authored pull requests" />
  <img src="https://img.shields.io/badge/MERGED-{merged_prs}-FFFFFF?style=for-the-badge&labelColor=111111&color=FFFFFF" alt="{merged_prs} merged pull requests" />
  <img src="https://img.shields.io/badge/OPEN-{open_prs}-FFFFFF?style=for-the-badge&labelColor=111111&color=FFFFFF" alt="{open_prs} open pull requests" />
</p>

### All repository languages

{render_languages(languages)}

<sub>Automatically refreshed by GitHub Actions · Language percentages are weighted by bytes across non-fork, non-archived public repositories.</sub>"""

readme = README.read_text(encoding="utf-8")
start = "<!-- BEGIN GITHUB METRICS -->"
end = "<!-- END GITHUB METRICS -->"
if start not in readme or end not in readme:
    raise RuntimeError("GitHub metrics markers are missing from README.md")
before, remainder = readme.split(start, 1)
_, after = remainder.split(end, 1)
README.write_text(f"{before}{start}\n{section}\n{end}{after}", encoding="utf-8")
print(f"Updated metrics: {total_prs} PRs, {merged_prs} merged, {len(languages)} languages.")
