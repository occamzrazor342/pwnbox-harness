# HARNESS.md — the path/scope contract every agent reads

Every agent in this harness starts by reading your project's own scope/config
document (with Claude Code, that's your `CLAUDE.md` — it's auto-loaded into
context, so it's the natural place for this). That document needs to define
two things: **what's authorized** (which targets/platforms are in scope) and
**where things live** (the paths below). The agents never hardcode a literal
path — they reference these names, and your `CLAUDE.md` supplies the real
values for your own project.

You don't need to rename your folders to match these variable names — you
just need to tell your `CLAUDE.md` which of your folders plays which role.

## The variables

| Variable | What it holds | This repo's own reference deployment uses |
|---|---|---|
| `NOTES_ROOT` | Raw/working notes per target, one subfolder per content category (e.g. Machines, forensics challenges, multi-host content) | `Recon Output/` |
| `WRITEUPS_ROOT` | Polished, publishable output — same category subfolders as `NOTES_ROOT` | `HTB Writeups/` |
| `TOOLING_ROOT` | Reusable scripts, a running technique index, vulnerability-research notes, saved exploit code per target | `Tooling and Scripts/` |
| `ORCHESTRATION_ROOT` | Goal-tracking state: a registry of every run, an append-only event log, per-provider work queues, worker state | `Orchestration/` |
| `SCOPE_DOC` | The single document defining authorized scope and this table's real values for your project | `CLAUDE.md` |
| `LAB_ENV_ROOT` | Signed engagement scope docs, fixed-target connection tables (VM inventory, wargame host/port tables) | `Lab Environment/` |
| `BOUNTY_ROOT_PATTERN` | One folder per bug bounty program, never a shared umbrella folder | `Bug Bounty - <Program Name>/` |

## Setting this up for your own project

1. Pick real folders for each variable (or reuse the ones above — they're a
   sensible default, not a requirement).
2. In your `CLAUDE.md`, state the mapping explicitly and describe your
   authorized scope (which platforms/targets an agent is allowed to touch).
3. That's it — every agent's own instructions already say "read your
   project's scope/config doc first"; they'll pick up your values from there
   instead of assuming this repo's own layout.

## What's genuinely generic here vs. what's a reference implementation

The orchestration logic (the pipeline stages, the blocked-stage retry loop,
the Assumption Register pattern in `synthesize-state`, the cost/iteration
guardrails, the operating principles in `docs/`) doesn't know or care which
platform you're targeting — it only cares about the path variables above.

`agents/connect-agent.md` and `agents/sherlock-agent.md` are the exception:
they're a **reference implementation** for one specific platform (HackTheBox,
plus OverTheWire for fixed-target wargames), including calls to
platform-specific tooling this repo doesn't ship (see their own files for
what they expect). If you're targeting a different platform, treat these two
as the pattern to follow, not something the rest of the harness depends on —
nothing else in this repo calls them directly except the `pwn-box` skill's
first pipeline stage, which you can swap for your own equivalent.

Building a true plugin interface (so a non-HTB platform drops in without
editing any agent file) is deliberately not attempted here — see the README's
"Not built yet" section.
