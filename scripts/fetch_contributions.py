#!/usr/bin/env python
"""Fetch a GitHub user's public contribution calendar without a token.

GitHub serves the calendar as an HTML fragment at
https://github.com/users/<username>/contributions — the same markup the
profile page itself embeds. This parses that fragment and writes
data/contributions.json with raw days plus derived stats.

Usage: python fetch_contributions.py [username]
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "arv1ndofficial"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = "data/contributions.json"


def fetch_days(username: str) -> list[dict]:
    resp = requests.get(
        f"https://github.com/users/{username}/contributions",
        headers={"User-Agent": f"profile-readme-bot (+https://github.com/{username})"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Counts live in sibling <tool-tip for="<cell-id>"> elements, e.g.
    # "3 contributions on August 20th." / "No contributions on August 13th.",
    # not on the <td> itself.
    tooltip_by_cell_id = {
        tip.get("for"): tip.get_text(strip=True)
        for tip in soup.select("tool-tip[for]")
    }

    days = []
    cells = soup.select("td.ContributionCalendar-day") or soup.select("[data-date]")
    for cell in cells:
        d = cell.get("data-date")
        if not d:
            continue
        level_attr = cell.get("data-level")
        level = int(level_attr) if level_attr is not None else 0
        raw_label = tooltip_by_cell_id.get(cell.get("id"), "")
        match = re.match(r"\s*(\d+|No)\b", raw_label, re.IGNORECASE)
        count = 0 if not match or match.group(1).lower() == "no" else int(match.group(1))
        days.append({"date": d, "level": level, "count": count, "raw_label": raw_label})

    days.sort(key=lambda x: x["date"])
    return days


def derive_stats(days: list[dict]) -> dict:
    if not days:
        return {}

    current_streak = 0
    longest_streak = 0
    running = 0
    for day in days:
        if day["level"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    for day in reversed(days):
        if day["level"] > 0:
            current_streak += 1
        else:
            break

    best_day = max(days, key=lambda x: x["count"])

    monthly = {}
    for day in days:
        month = day["date"][:7]
        monthly[month] = monthly.get(month, 0) + day["count"]

    total_active_days = sum(1 for d in days if d["level"] > 0)
    total_contributions = sum(d["count"] for d in days)

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day["date"],
        "active_days": total_active_days,
        "total_contributions": total_contributions,
        "monthly_totals": monthly,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    days = fetch_days(USERNAME)
    stats = derive_stats(days)
    out = {"username": USERNAME, "days": days, "stats": stats}

    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {OUT_PATH} ({len(days)} days)")
