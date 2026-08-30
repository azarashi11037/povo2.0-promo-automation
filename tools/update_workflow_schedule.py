#!/usr/bin/env python3
"""Rewrite the encrypted account's next GitHub Actions trigger window."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


BEGIN_MARKER = "    # BEGIN MANAGED PRECISE SCHEDULE"
END_MARKER = "    # END MANAGED PRECISE SCHEDULE"
EARLY_START_MINUTES = 10
FALLBACK_MINUTES = (5, 15, 30)
DAILY_SAFETY_CRON = "43 2 * * *"


def parse_due(value: str) -> datetime:
    due = datetime.fromisoformat(value)
    if due.tzinfo is None:
        raise ValueError("next_due_at must include a timezone")
    return due.replace(second=0, microsecond=0)


def cron(moment: datetime) -> str:
    utc = moment.astimezone(timezone.utc)
    return f"{utc.minute} {utc.hour} {utc.day} {utc.month} *"


def managed_block(due: datetime) -> str:
    primary = due - timedelta(minutes=EARLY_START_MINUTES)
    lines = [
        BEGIN_MARKER,
        f"    # Target due minute: {due.isoformat(timespec='minutes')}",
        f"    # Primary runner: {EARLY_START_MINUTES} minutes early; it waits in-process.",
        f'    - cron: "{cron(primary)}"',
    ]
    for offset in FALLBACK_MINUTES:
        lines.extend(
            (
                f"    # Fallback: {offset} minutes after the target.",
                f'    - cron: "{cron(due + timedelta(minutes=offset))}"',
            )
        )
    lines.extend(
        (
            "    # Daily safety check; also keeps public-repository schedules active.",
            f'    - cron: "{DAILY_SAFETY_CRON}"',
            END_MARKER,
        )
    )
    return "\n".join(lines)


def update_workflow(workflow: Path, due: datetime) -> bool:
    text = workflow.read_text(encoding="utf-8")
    start = text.find(BEGIN_MARKER)
    end = text.find(END_MARKER)
    if start < 0 or end < start:
        raise ValueError("managed schedule markers are missing or out of order")
    end += len(END_MARKER)
    updated = text[:start] + managed_block(due) + text[end:]
    if updated == text:
        return False
    workflow.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--workflow", type=Path, required=True)
    args = parser.parse_args()
    state = json.loads(args.state.read_text(encoding="utf-8"))
    value = state.get("next_due_at")
    if not value:
        print("No next_due_at is stored; precise workflow schedule was unchanged.")
        return 0
    due = parse_due(str(value))
    changed = update_workflow(args.workflow, due)
    print(
        "Precise workflow schedule updated."
        if changed
        else "Precise workflow schedule already matches next_due_at."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
