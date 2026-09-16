#!/usr/bin/env python3
"""
validate_assumption_register.py

Checks a synthesize-state Assumption Register JSON sidecar against its schema, so a
malformed or incomplete register gets caught before it's trusted as the basis for a
re-dispatch. Stdlib only, no dependencies.

Usage:
    python3 validate_assumption_register.py <path-to-register.json>

Exit code 0 and "OK" on stdout if valid; exit code 1 and a list of issues on stderr
otherwise. Run this after synthesize-state writes/updates a register, before treating
it as complete -- see docs/Agent-Operating-Principles.md #9 for why this exists (a
flattened, unschema'd register is exactly how a narrow validated fact turns into a
broad unsupported one without anyone noticing).

Schema: the JSON file is a list of row objects, each with:
    id           str, required, non-empty, unique within the file
    assumption   str, required, non-empty -- the claim being tracked
    status       str, required, one of: UNVALIDATED, VALIDATED, INVALIDATED
    evidence_ref str, required -- for VALIDATED/INVALIDATED, must be non-empty and
                 point somewhere checkable (a file path, optionally with a line/section
                 after a colon, e.g. "target-raw.md:142-150"); for UNVALIDATED, must be
                 empty ("") -- an UNVALIDATED row citing "evidence" is a contradiction
                 in terms (see the module docstring in synthesize-state's own SKILL.md).
    basis        str, required, non-empty -- for VALIDATED/INVALIDATED, a short restated
                 reason; for UNVALIDATED, what's missing or what would resolve it.
"""

import json
import sys

VALID_STATUSES = {"UNVALIDATED", "VALIDATED", "INVALIDATED"}
REQUIRED_FIELDS = ["id", "assumption", "status", "evidence_ref", "basis"]


def validate(rows):
    issues = []

    if not isinstance(rows, list):
        return [f"top-level JSON must be a list of row objects, got {type(rows).__name__}"]

    seen_ids = set()
    for i, row in enumerate(rows):
        where = f"row {i}"
        if not isinstance(row, dict):
            issues.append(f"{where}: expected an object, got {type(row).__name__}")
            continue

        for field in REQUIRED_FIELDS:
            if field not in row:
                issues.append(f"{where}: missing required field '{field}'")

        row_id = row.get("id")
        if row_id:
            where = f"row {i} (id={row_id!r})"
            if row_id in seen_ids:
                issues.append(f"{where}: duplicate id -- ids must be stable and unique across passes")
            seen_ids.add(row_id)
        elif "id" in row:
            issues.append(f"{where}: 'id' present but empty")

        if not row.get("assumption"):
            issues.append(f"{where}: 'assumption' must be a non-empty string")

        status = row.get("status")
        if status is not None and status not in VALID_STATUSES:
            issues.append(f"{where}: status {status!r} not one of {sorted(VALID_STATUSES)}")

        evidence_ref = row.get("evidence_ref", "")
        if status in ("VALIDATED", "INVALIDATED") and not evidence_ref:
            issues.append(
                f"{where}: status={status} requires a non-empty 'evidence_ref' "
                f"(a file path, e.g. 'target-raw.md:142-150') -- a validated/invalidated "
                f"claim with no citation is not actually validated, see synthesize-state's "
                f"own rule"
            )
        if status == "UNVALIDATED" and evidence_ref:
            issues.append(
                f"{where}: status=UNVALIDATED but 'evidence_ref' is set to {evidence_ref!r} -- "
                f"if you have evidence, the status isn't UNVALIDATED; if you don't, clear this field"
            )

        if not row.get("basis"):
            issues.append(f"{where}: 'basis' must be a non-empty string")

    return issues


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Failed to read/parse {path}: {e}", file=sys.stderr)
        sys.exit(1)

    issues = validate(data)
    if issues:
        print(f"INVALID: {len(issues)} issue(s) found in {path}", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {len(data)} row(s), schema valid")


if __name__ == "__main__":
    main()
