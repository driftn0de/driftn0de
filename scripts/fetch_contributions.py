"""Fetch the last year of contributions -> data/contributions.json.

Primary: the public calendar HTML fragment — the exact data your profile shows, including
private contributions if "Include private contributions" is enabled. No token needed.
Extra accounts: EXTRA_USERS (comma-separated, set as a repo *secret* so no username is public).
Local activity: data/local-activity.json (Claude Code prompts + off-GitHub commits, published to
the 'activity' branch by export_local_activity.py) is merged in when present.
Fallback: GraphQL API. Note the Actions GITHUB_TOKEN only sees *public* contributions, so set a
PROFILE_TOKEN secret (fine-grained PAT, no scopes) if you want the fallback to match the profile.
"""
import json
import os
import re
import sys
from datetime import date, timedelta

import requests

from theme import ROOT

USER = os.environ.get("GH_USER", "driftn0de")
OUT = ROOT / "data" / "contributions.json"
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date contributionCount contributionLevel}}}}}}"""


def via_graphql(token, user=USER):
    r = requests.post("https://api.github.com/graphql", timeout=30,
                      headers={"Authorization": f"bearer {token}"},
                      json={"query": QUERY, "variables": {"login": user}})
    r.raise_for_status()
    body = r.json()
    if "errors" in body:
        raise RuntimeError(body["errors"])
    weeks = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [{"date": d["date"], "count": d["contributionCount"], "level": LEVELS[d["contributionLevel"]]}
            for w in weeks for d in w["contributionDays"]]


def via_html(user=USER):
    from bs4 import BeautifulSoup
    r = requests.get(f"https://github.com/users/{user}/contributions", timeout=30,
                     headers={"User-Agent": "profile-heatmap"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(strip=True) for t in soup.select("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        m = re.match(r"([\d,]+)", tips.get(td.get("id"), ""))
        days.append({"date": td["data-date"], "count": int(m.group(1).replace(",", "")) if m else 0,
                     "level": int(td.get("data-level", 0))})
    if not days:
        raise RuntimeError("calendar markup changed — no day cells found")
    return sorted(days, key=lambda d: d["date"])


def stats(days):
    total = sum(d["count"] for d in days)
    active = [d for d in days if d["count"]]
    longest = cur = 0
    for d in days:
        cur = cur + 1 if d["count"] else 0
        longest = max(longest, cur)
    # current streak: allow today to be empty (the day isn't over yet)
    tail = days[:-1] if days and not days[-1]["count"] else days
    current = 0
    for d in reversed(tail):
        if not d["count"]:
            break
        current += 1
    best = max(days, key=lambda d: d["count"]) if days else None
    return {"total": total, "active_days": len(active), "longest_streak": longest,
            "current_streak": current, "best_day": best}


def github_days(user, primary):
    try:
        return via_html(user)
    except Exception as e:  # noqa: BLE001 — markup changed or blocked: fall back to the API
        print(f"html source failed for {'primary' if primary else 'extra'} user:", e, file=sys.stderr)
        token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            if primary:
                sys.exit(1)
            return []
        return via_graphql(token, user)


def levels(days):
    """GitHub-style quartile levels over the non-zero days of the merged series."""
    nz = sorted(d["count"] for d in days if d["count"])
    if not nz:
        return
    q = [nz[int(len(nz) * f)] for f in (0.25, 0.5, 0.75)]
    for d in days:
        c = d["count"]
        d["level"] = 0 if not c else 1 if c <= q[0] else 2 if c <= q[1] else 3 if c <= q[2] else 4


def main():
    days = github_days(USER, True)
    for d in days:
        d["src"] = {"github": d["count"]}
    index = {d["date"]: d for d in days}

    for extra in filter(None, (u.strip() for u in os.environ.get("EXTRA_USERS", "").split(","))):
        for e in github_days(extra, False):
            if e["date"] in index:
                index[e["date"]]["src"]["github"] += e["count"]

    local = ROOT / "data" / "local-activity.json"
    if local.exists():
        for day, src in json.loads(local.read_text())["days"].items():
            if day in index:
                for k, v in src.items():
                    index[day]["src"][k] = index[day]["src"].get(k, 0) + v

    for d in days:
        d["count"] = sum(d["src"].values())
    levels(days)

    st = stats(days)
    st["by_source"] = {k: sum(d["src"].get(k, 0) for d in days) for k in ("github", "git", "claude")}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"user": USER, "generated": date.today().isoformat(),
                               "stats": st, "days": days}, indent=1))
    print(f"{len(days)} days, {st['total']} total, by source {st['by_source']} -> {OUT}")


if __name__ == "__main__":
    main()
