# pwnbox-harness

A multi-agent pipeline for Claude Code that runs a security-research engagement —
recon, exploitation, privilege escalation, writeup — end to end with minimal manual
handoff between stages, plus the orchestration and operating discipline that makes it
safe to run autonomously against real (if scoped) infrastructure.

This isn't a theoretical design. It's extracted from a private vault where it's run
dozens of real engagements against HackTheBox machines, DFIR challenges, and bug bounty
programs — the `docs/Agent-Operating-Principles.md` file in here is the actual, dated
incident history that shaped every guardrail in the pipeline, not a hypothetical
best-practices list.

## What's in here

**Agents** (`agents/*.md`, Claude Code subagent definitions):

| Agent | Stage |
|---|---|
| `connect-agent` | Resolve/spawn a target (reference implementation: HackTheBox + OverTheWire) |
| `recon-agent` | Port/service enumeration, tech fingerprinting |
| `exploit-agent` | Foothold: identify and weaponize the initial-access vector |
| `privesc-agent` | Escalate an initial shell to root/admin |
| `writeup-agent` | Synthesize the whole chain into a polished, why-reasoned writeup |
| `scope-agent` | The hard gate for bug bounty work: resolve a program's real scope before anything else touches it |
| `bounty-exploit-agent` | Minimal, non-destructive proof-of-concept for a live bug bounty program (deliberately not `exploit-agent` — prove-then-stop, not full exploitation) |
| `bounty-report-agent` | Draft a submittable vulnerability report from a confirmed finding |
| `sherlock-agent` | A DFIR/forensics-challenge workflow (reference implementation: HTB Sherlocks) — no shell/root involved, just evidence and a task list |
| `goal-relay-agent` | Turn a finished goal's notes into a mobile-readable hosted report |
| `verify-agent` | Independently check a high-consequence claim (a root/escalation claim, a bounty finding, a resolved signal) before it's treated as ground truth — shares no context with whoever produced the claim, and its job is to try to refute it, not confirm it |

**Skills** (`skills/*/SKILL.md`, the orchestration layer):

- **`pwn-box`** — runs one target through the full agent chain autonomously, including a
  bounded-but-persistent retry loop for a blocked stage (HTB/lab targets are exploitable
  by design; "no viable vector" is a checkpoint, not a verdict) with a mandatory
  synthesis checkpoint before every re-dispatch.
- **`orchestrate-goals`** — a fixed list of targets run through `pwn-box` in sequence.
- **`infinite-worker`** — an open-ended, pausable rolling queue instead of a fixed list.
- **`synthesize-state`** — the mechanism that keeps a multi-pass engagement honest: an
  Assumption Register that separates evidence-backed fact from inherited conclusion
  (UNVALIDATED → VALIDATED/INVALIDATED, live and re-checked, schema-validated via the
  bundled `scripts/validate_assumption_register.py`), invoked mandatorily before ever
  re-dispatching a blocked stage. See `docs/Agent-Operating-Principles.md` #9 for the
  incident this was built to stop from happening again.

**Scripts** (`scripts/*.py`, stdlib-only):

- **`validate_assumption_register.py`** — schema-checks a `synthesize-state` Assumption
  Register JSON sidecar (fixed status enum, required evidence citations for
  VALIDATED/INVALIDATED rows) before it's trusted as the basis for a re-dispatch.

**Docs:**

- `HARNESS.md` — the path/scope contract every agent reads. Read this first if you're
  adopting the harness for your own project.
- `docs/Agent-Operating-Principles.md` — 17 numbered principles on verification habits,
  safety-boundary discipline, cost control, and multi-pass-engagement failure modes,
  each one tied to a real dated incident.

## Quick start

1. Copy `agents/` and `skills/` into your own project's `.claude/` directory.
2. Read `HARNESS.md` and set up your project's `CLAUDE.md` with your own values for the
   path variables it defines, plus a statement of your authorized scope.
3. Invoke `pwn-box` on a target (or an individual agent for a single stage) the same way
   you'd invoke any Claude Code skill/subagent.

## What's genuinely generic vs. what's a reference implementation

The orchestration logic — the pipeline itself, the blocked-stage retry loop, the
Assumption Register pattern, the cost/iteration guardrails — doesn't know or care which
platform you're targeting. `connect-agent` and `sherlock-agent` are the exception: they
ship as a working reference implementation for one specific platform (HackTheBox, plus
OverTheWire for fixed-target wargames). If you're targeting something else, treat those
two as the pattern to follow, not a dependency the rest of the harness needs.

## Not built yet

- **A true pluggable target-provider interface.** Right now, targeting a platform other
  than HTB/OverTheWire means writing your own `connect-agent` (and `sherlock-agent`
  equivalent, if relevant) rather than configuring an existing one. Deliberately not
  attempted here — the path/scope genericization in `HARNESS.md` was the bounded first
  step; a real plugin interface is a bigger design exercise for later.
- **Non-HTB bug bounty report formats.** `bounty-report-agent` currently formats for
  HackerOne specifically (documented in the file itself as the platform this started
  with).
- **A cost-control/verification checkpoint before hunting spends its budget** — deliberately
  not built. This pipeline's retry loop is uncapped by design (see `pwn-box`'s "Handling a
  Blocked Stage"); a fixed-budget-reservation model like a large fleet-wide scanner would
  use doesn't fit an engagement this pipeline is built to keep working at until it lands,
  not to cut off partway through.

## License

MIT — see `LICENSE`.
