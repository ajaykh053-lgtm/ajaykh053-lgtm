import requests
import re
import os
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
USERNAME = "ajaykh053-lgtm"   # ← your GitHub username (already set)
SVG_FILE = "profile-card.svg" # ← rename this to match your actual SVG filename

# ── GitHub API ────────────────────────────────────────────────────────────────
TOKEN   = os.environ["GITHUB_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github.v3+json"}


def get_user():
    r = requests.get(f"https://api.github.com/users/{USERNAME}", headers=HEADERS)
    r.raise_for_status()
    return r.json()


def get_repos_and_stars():
    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            params={"per_page": 100, "page": page},
            headers=HEADERS,
        )
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    return len(repos), stars


def get_commit_count():
    r = requests.get(
        "https://api.github.com/search/commits",
        params={"q": f"author:{USERNAME}"},
        headers={**HEADERS, "Accept": "application/vnd.github.cloak-preview+json"},
    )
    r.raise_for_status()
    return r.json().get("total_count", 0)


def calc_uptime(created_at: str) -> str:
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    total_d = (datetime.now(timezone.utc) - created).days
    months  = total_d // 30
    days    = total_d % 30
    return f"{months} months, {days} days"


# ── SVG Patcher ───────────────────────────────────────────────────────────────
def patch(content: str, label: str, value, color: str = "#79c0ff") -> str:
    """Find the value <tspan> that follows a label in the SVG and replace its text."""
    pat = (
        rf"({re.escape(label)}: </tspan>"
        rf"<tspan[^>]*>[^<]*</tspan>"      # the dots tspan
        rf"<tspan fill=\"{color}\">)"
        rf"[^<]*"                           # ← current value, gets replaced
        rf"(</tspan>)"
    )
    new = re.sub(pat, rf"\g<1> {value}\g<2>", content)
    if new == content:
        print(f"  ⚠️  WARNING: pattern for '{label}' not found – check your SVG label text")
    return new


def update_svg(stats: dict) -> None:
    with open(SVG_FILE, encoding="utf-8") as f:
        content = f.read()

    content = patch(content, ". Uptime",    stats["uptime"],    color="#c9d1d9")
    content = patch(content, ". Repos",     stats["repos"])
    content = patch(content, ". Stars",     stats["stars"])
    content = patch(content, ". Commits",   stats["commits"])
    content = patch(content, ". Followers", stats["followers"])

    with open(SVG_FILE, "w", encoding="utf-8") as f:
        f.write(content)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("📡 Fetching GitHub stats…")

    user              = get_user()
    repo_count, stars = get_repos_and_stars()
    commits           = get_commit_count()
    uptime            = calc_uptime(user["created_at"])

    stats = {
        "uptime":    uptime,
        "repos":     repo_count,
        "stars":     stars,
        "commits":   commits,
        "followers": user["followers"],
    }

    print(f"  uptime    → {stats['uptime']}")
    print(f"  repos     → {stats['repos']}")
    print(f"  stars     → {stats['stars']}")
    print(f"  commits   → {stats['commits']}")
    print(f"  followers → {stats['followers']}")

    update_svg(stats)
    print(f"✅ {SVG_FILE} updated!")
