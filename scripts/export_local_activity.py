#!/usr/bin/env python3
"""Export per-day activity counts from THIS machine and publish them to the 'activity' branch.

Sources (counts only — no repo names, paths, messages or emails ever leave the machine):
  claude  prompts you sent in Claude Code sessions (~/.claude/projects/**/*.jsonl)
  git     commits authored by you in local repos that have NO github.com remote
          (repos on GitHub are already counted by the contribution calendars — no double counting)

Config: ~/.config/driftn0de-activity.json  (kept outside the repo — it holds your emails)
  {
    "remote": "git@github-driftn0de:driftn0de/driftn0de.git",
    "emails": ["you@example.com"],
    "git_roots": ["~/Developer", "~/Projects"],
    "claude_dir": "~/.claude/projects"
  }

Usage:  python3 export_local_activity.py            # export + push
        python3 export_local_activity.py --dry-run  # print totals only
Standard library only; runs with the macOS system python3.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

CONFIG = Path("~/.config/driftn0de-activity.json").expanduser()
SINCE = date.today() - timedelta(days=372)


def claude_prompts(root: Path) -> Counter:
    days = Counter()
    for f in root.glob("**/*.jsonl"):
        try:
            for line in f.open(encoding="utf-8", errors="ignore"):
                if '"type":"user"' not in line.replace(" ", ""):
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("type") != "user" or e.get("isSidechain") or e.get("isMeta"):
                    continue
                content = (e.get("message") or {}).get("content")
                is_prompt = isinstance(content, str) or (
                    isinstance(content, list) and any(b.get("type") == "text" for b in content if isinstance(b, dict)))
                if not is_prompt or not e.get("timestamp"):
                    continue
                d = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).astimezone().date()
                if d >= SINCE:
                    days[d.isoformat()] += 1
        except OSError:
            continue
    return days


def git_repos(roots, max_depth=4):
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        for dirpath, dirnames, _ in os.walk(root):
            depth = len(Path(dirpath).relative_to(root).parts)
            if ".git" in dirnames:
                yield Path(dirpath)
                dirnames[:] = []  # don't descend into a repo
                continue
            dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("node_modules", "vendor", "Pods")]
            if depth >= max_depth:
                dirnames[:] = []


def git_commits(roots, emails) -> Counter:
    days = Counter()
    for repo in git_repos(roots):
        remotes = subprocess.run(["git", "-C", repo, "remote", "-v"], capture_output=True, text=True).stdout
        if "github.com" in remotes:
            continue  # counted by the GitHub calendars already
        args = ["git", "-C", repo, "log", "--all", "--no-merges", f"--since={SINCE.isoformat()}",
                "--format=%ad", "--date=short"] + [f"--author={e}" for e in emails]
        out = subprocess.run(args, capture_output=True, text=True).stdout
        days.update(line for line in out.split() if line)
    return days


def publish(remote: str, payload: dict):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "local-activity.json").write_text(json.dumps(payload, indent=1, sort_keys=True))
        run = lambda *a: subprocess.run(["git", "-C", tmp, *a], check=True, capture_output=True)  # noqa: E731
        run("init", "-q", "-b", "activity")
        run("add", "-A")
        # authored as the GitHub noreply bot identity: no personal email in the public history
        run("-c", "user.name=activity-export", "-c", "user.email=activity-export@users.noreply.github.com",
            "commit", "-qm", f"activity {date.today().isoformat()}")
        run("push", "-qf", remote, "activity")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not CONFIG.exists():
        sys.exit(f"missing config: {CONFIG} (see docstring)")
    cfg = json.loads(CONFIG.read_text())

    claude = claude_prompts(Path(cfg.get("claude_dir", "~/.claude/projects")).expanduser())
    git = git_commits(cfg.get("git_roots", []), cfg.get("emails", [])) if cfg.get("emails") else Counter()
    payload = {"generated": date.today().isoformat(),
               "days": {d: {"claude": claude[d], "git": git[d]} for d in sorted(set(claude) | set(git))}}
    print(f"claude prompts: {sum(claude.values())} over {len(claude)} days")
    print(f"local commits:  {sum(git.values())} over {len(git)} days")
    if not a.dry_run:
        publish(cfg["remote"], payload)
        print("pushed to activity branch")


if __name__ == "__main__":
    main()
