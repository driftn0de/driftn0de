"""Fetch the last year of contributions -> data/contributions.json.

Primary: GitHub GraphQL API (stable schema). In Actions the built-in GITHUB_TOKEN is enough.
Fallback: the public calendar HTML fragment, used only when no token is set (local runs).
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


def via_graphql(token):
    r = requests.post("https://api.github.com/graphql", timeout=30,
                      headers={"Authorization": f"bearer {token}"},
                      json={"query": QUERY, "variables": {"login": USER}})
    r.raise_for_status()
    body = r.json()
    if "errors" in body:
        raise RuntimeError(body["errors"])
    weeks = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [{"date": d["date"], "count": d["contributionCount"], "level": LEVELS[d["contributionLevel"]]}
            for w in weeks for d in w["contributionDays"]]


def via_html():
    from bs4 import BeautifulSoup
    r = requests.get(f"https://github.com/users/{USER}/contributions", timeout=30,
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


def main():
    token = os.environ.get("GITHUB_TOKEN")
    try:
        days = via_graphql(token) if token else via_html()
    except Exception as e:  # noqa: BLE001 — try the other source before giving up
        print("primary source failed:", e, file=sys.stderr)
        days = via_html() if token else sys.exit(1)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"user": USER, "generated": date.today().isoformat(),
                               "stats": stats(days), "days": days}, indent=1))
    print(f"{len(days)} days, {stats(days)['total']} contributions -> {OUT}")


if __name__ == "__main__":
    main()
