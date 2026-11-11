import json
import os
import urllib.parse
import urllib.request
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
    return github_get(
        f"https://api.github.com/search/issues?q={encoded}&per_page=1"
    )["total_count"]


total_prs = search_count(f"is:pr author:{USERNAME}")
merged_prs = search_count(f"is:pr is:merged author:{USERNAME}")
open_prs = search_count(f"is:pr is:open author:{USERNAME}")

section = f"""<p align="center">
  <img src="https://img.shields.io/badge/PULL_REQUESTS-{total_prs}-FFFFFF?style=for-the-badge&labelColor=111111&color=FFFFFF" alt="{total_prs} authored pull requests" />
  <img src="https://img.shields.io/badge/MERGED-{merged_prs}-FFFFFF?style=for-the-badge&labelColor=111111&color=FFFFFF" alt="{merged_prs} merged pull requests" />
  <img src="https://img.shields.io/badge/OPEN-{open_prs}-FFFFFF?style=for-the-badge&labelColor=111111&color=FFFFFF" alt="{open_prs} open pull requests" />
</p>

### GitHub statistics

<p align="center">
  <img height="165" src="https://github-readme-stats.vercel.app/api?username=AnjaniBeesu&show_icons=true&hide_rank=true&hide_border=true&include_all_commits=true&bg_color=111111&title_color=FFFFFF&text_color=DDDDDD&icon_color=FFFFFF" alt="GitHub statistics" />
  <img height="165" src="https://github-readme-stats.vercel.app/api/top-langs/?username=AnjaniBeesu&layout=compact&langs_count=20&hide_border=true&bg_color=111111&title_color=FFFFFF&text_color=DDDDDD" alt="Most-used programming languages" />
</p>

<sub>PR counts refresh automatically through GitHub Actions. Repository and language cards are provided by github-readme-stats.</sub>"""

readme = README.read_text(encoding="utf-8")
start = "<!-- BEGIN GITHUB METRICS -->"
end = "<!-- END GITHUB METRICS -->"
if start not in readme or end not in readme:
    raise RuntimeError("GitHub metrics markers are missing from README.md")
before, remainder = readme.split(start, 1)
_, after = remainder.split(end, 1)
README.write_text(f"{before}{start}\n{section}\n{end}{after}", encoding="utf-8")
print(f"Updated PR metrics: {total_prs} total, {merged_prs} merged, {open_prs} open.")
