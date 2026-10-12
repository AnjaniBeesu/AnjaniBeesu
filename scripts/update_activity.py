#!/usr/bin/env python3
"""Generate a self-hosted SVG dashboard from GitHub's public Events API."""
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from xml.sax.saxutils import escape
import json
import os

USER = "AnjaniBeesu"
OUT = "assets/activity.svg"
BG = "#111111"
YELLOW = "#F3E7A3"
IVORY = "#F7F5EC"
MUTED = "#A9A79B"
LINE = "#38372F"
WIDTH, HEIGHT = 960, 330

def fetch_events():
    url = f"https://api.github.com/users/{USER}/events/public?per_page=100"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "AnjaniBeesu-Activity-Widget"}
    token = os.environ.get("GH_ACTIVITY_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def esc(value):
    return escape(str(value))

def text(x, y, value, size=14, fill=IVORY, weight=400, anchor="start", extra=""):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" {extra}>{esc(value)}</text>'

def main():
    try:
        events = fetch_events()
        error = None
    except (URLError, HTTPError, TimeoutError, ValueError) as exc:
        events = []
        error = str(exc)[:100]

    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=13)).date()
    days = [start + timedelta(days=i) for i in range(14)]
    counts = {day: 0 for day in days}
    recent = []
    seen = set()

    for event in events:
        try:
            when = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
            day = when.date()
            if day in counts:
                counts[day] += 1
            repo = event.get("repo", {}).get("name", "GitHub")
            kind = event.get("type", "Activity").replace("Event", "")
            labels = {
                "Push": "Pushed code",
                "PullRequest": "Pull request activity",
                "Issues": "Issue activity",
                "Create": "Created a branch or repository",
                "Watch": "Starred a repository",
                "Fork": "Forked a repository",
                "Release": "Published a release",
                "IssueComment": "Commented on an issue",
                "PullRequestReview": "Reviewed a pull request",
                "CommitComment": "Commented on a commit",
                "Public": "Made a repository public",
            }
            label = labels.get(kind, kind + " activity")
            key = (repo, label, when.date())
            if key not in seen:
                recent.append((when, label, repo))
                seen.add(key)
        except (KeyError, TypeError, ValueError):
            continue

    total = sum(counts.values())
    max_count = max(counts.values()) if counts else 1
    if max_count == 0:
        max_count = 1
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">',
        '<title id="title">Anjani Beesu public GitHub activity</title>',
        '<desc id="desc">A self-hosted activity dashboard based on recent public GitHub events. Private contributions are not included.</desc>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="18" fill="{BG}"/>',
        f'<rect x="0" y="0" width="7" height="{HEIGHT}" rx="3" fill="{YELLOW}"/>',
        text(32, 40, "GITHUB / ACTIVITY", 12, YELLOW, 700, extra='letter-spacing="2.5"'),
        text(32, 77, "Public work, in motion.", 27, IVORY, 700),
        text(32, 101, "SELF-HOSTED · GITHUB PUBLIC EVENTS API · 14-DAY WINDOW", 10, MUTED, 600, extra='letter-spacing="1.1"'),
        f'<line x1="32" y1="120" x2="928" y2="120" stroke="{LINE}"/>',
        text(34, 157, str(total), 31, YELLOW, 700),
        text(34, 178, "PUBLIC EVENTS", 10, MUTED, 700, extra='letter-spacing="1.2"'),
        text(34, 201, "LAST 14 DAYS", 10, MUTED, 600, extra='letter-spacing="1.2"'),
    ]
    # 14-day bar chart
    chart_x, chart_y, chart_w, chart_h = 215, 139, 420, 74
    gap = 8
    bar_w = (chart_w - gap * 13) / 14
    for i, day in enumerate(days):
        count = counts[day]
        bar_h = max(5, (count / max_count) * 49)
        x = chart_x + i * (bar_w + gap)
        y = chart_y + 49 - bar_h
        fill = YELLOW if count else LINE
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="3" fill="{fill}"/>')
        if i in (0, 6, 13):
            parts.append(text(x + bar_w/2, chart_y + 69, day.strftime("%b %d"), 9, MUTED, 400, "middle"))
    parts.append(f'<line x1="665" y1="137" x2="665" y2="215" stroke="{LINE}"/>')
    parts.append(text(690, 157, "LATEST PUBLIC SIGNAL", 10, YELLOW, 700, extra='letter-spacing="1.2"'))
    latest = sorted(recent, key=lambda item: item[0], reverse=True)[:3]
    if error:
        parts.append(text(690, 183, "Activity refresh failed; retry scheduled.", 11, MUTED))
    elif not latest:
        parts.append(text(690, 183, "No recent public events found.", 11, MUTED))
    else:
        for i, (when, label, repo) in enumerate(latest):
            repo_short = repo.split("/")[-1]
            parts.append(text(690, 183 + i * 19, f"{label} · {repo_short}"[:38], 11, IVORY if i == 0 else MUTED))
    parts.extend([
        f'<line x1="32" y1="235" x2="928" y2="235" stroke="{LINE}"/>',
        text(32, 263, "BUILT IN-REPO", 10, YELLOW, 700, extra='letter-spacing="1.2"'),
        text(32, 285, "No third-party widget or badge service.", 13, IVORY, 400),
        text(928, 263, "DATA SCOPE", 10, YELLOW, 700, "end", extra='letter-spacing="1.2"'),
        text(928, 285, "Public events only · not a full contribution count", 12, MUTED, 400, "end"),
        text(32, 313, f"LAST GENERATED · {now.strftime('%Y-%m-%d %H:%M UTC')}", 9, MUTED, 400, extra='letter-spacing="0.8"'),
        '</svg>'
    ])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as file:
        file.write("\n".join(parts) + "\n")

if __name__ == "__main__":
    main()
