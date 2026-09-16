---
name: synthesize-state
description: This skill should be used by the orchestrator (not a subagent) to reconstruct the verified state of an in-progress engagement from its raw evidence — separating evidence-backed fact from inherited conclusion — and pin an Assumption Register + Unresolved Signals table to the top of the relevant notes. Invoke after recon completes, MANDATORILY before re-dispatching any blocked stage, when resuming a goal that's gone cold, or any time conclusions in the notes may have flattened. Named triggers: "synthesize <target>", "reconcile the notes", "what do we actually know", and the pre-re-dispatch checkpoint in pwn-box's blocked-stage loop.
version: 1.0.0
---

# synthesize-state — Evidence-vs-Conclusion Reconciliation

## Why this skill exists

Across a multi-pass engagement, each agent writes *conclusions* into the
notes, and later passes inherit them as *facts*. Two failure modes compound:

1. **Flattening** — a narrow, well-supported claim ("can't reach the
   `invites` collection") silently widens into a broad, unsupported one
   ("the injection is a dead end"), and the broad version becomes the
   premise everyone downstream builds on.
2. **Evidence discard** — the data behind a conclusion is thrown away at
   collection time (dumped only to `/tmp`, redacted in the notes, or never
   written down at all), so the conclusion can no longer be checked — yet
   it still reads as settled.

The Odyssey resume (2026-09-04) is the worked example: "MongoDB injection is
a dead end → box blocked" rested on 43 of 52 readable documents never being
preserved and the one thematically load-bearing field being redacted in the
agent's own notes. A synthesis pass caught it; nobody re-running the
blocked stage would have. See `assumption_register_over_flattened_conclusions`
and `subagent_fabricates_evidence_under_pressure` in memory for the
standing principles behind this.

## Hard rule: this runs in the orchestrator's own context

**Do NOT dispatch this as a fire-and-forget subagent that returns a
summary.** Synthesis is the highest-trust step in the pipeline; handing it
to the lowest-context actor is exactly the failure this skill exists to
prevent (a cold agent re-summarizing is *how* conclusions flatten and
evidence gets fabricated). The orchestrator reads the raw evidence and
writes the register itself.

You MAY dispatch a **read-only** helper (e.g. an `Explore`/general-purpose
agent) to do the noisy part — extracting verbatim excerpts and line
references from large raw files — but the VALIDATED/UNVALIDATED judgment
and the written register stay with you. Treat any excerpt a helper returns
as a pointer to verify against the raw file, not as a finding.

## Inputs

For target `<target>`, read — in full, from the durable notes store, not from
recall:
- `<NOTES_ROOT>/Machines/<target>-raw.md` (the evidence base — read this,
  don't skim; it is the ground truth every conclusion is checked against)
- `<NOTES_ROOT>/Machines/<target>-recon.md`, `-foothold.md`, `-privesc.md`
  (the conclusions to be checked)
- the goal's `<ORCHESTRATION_ROOT>/registry.json` entry (prior `blockedReason`,
  `reconEscalations`)
- For Fortresses, the `<name>-entrypoint.md` running notes instead.

## Method

1. **Read the raw evidence first, conclusions second.** Build your own
   picture from tool output before reading what prior passes concluded, so
   their framing doesn't anchor you.
2. **For every load-bearing conclusion in the notes, find its evidence in
   the raw file.** Classify:
   - **VALIDATED** — a specific raw-evidence reference (file + line/section)
     directly supports it. Cite it. No citation you can point to → it is
     NOT validated, regardless of how confident the prose is.
   - **UNVALIDATED** — asserted but its supporting evidence is absent from
     durable notes (only in `/tmp`, only in prose, redacted, or never
     recorded), OR never actually tested. This is not "probably true" — it
     is *unknown*, and every UNVALIDATED item that matters becomes an
     Unresolved Signal ("re-collect / actually test X").
   - **INVALIDATED** — the raw evidence contradicts it.
3. **Split conflated claims.** When one conclusion bundles a narrow
   supported claim with a broad unsupported one, break it into sub-rows
   (the Odyssey A3a "can't reach invites" = VALIDATED vs. A3b "readable data
   is useless" = UNVALIDATED split). A validated narrow fact never licenses
   the broad conclusion built on top of it.
4. **Never infer a finding from missing evidence.** "The dump is gone, so
   it probably had nothing" is exactly backwards — missing evidence means
   *unknown*, logged as a signal to re-collect, never as a negative result.
5. **Rank the Unresolved Signals** by offensive value right now, and — if
   the engagement has multiple named objectives (multiple flags, multiple
   in-scope assets) — keep a Crown-Jewels-style split of
   **already-accessible** vs. **requires-further-work** (see
   `docs/Agent-Operating-Principles.md` #10 for the full reasoning and
   worked example). Re-rank on each pass; a newly validated/invalidated
   assumption can change what's highest-value.

## Output

Prepend (or update in place — see below) a clearly delimited block at the
top of the stage notes file the next agent will read (recon checkpoint →
`-recon.md`; blocked exploit → `-foothold.md`; blocked privesc →
`-privesc.md`). Format:

```
> ═══════════════════════════════════════════════════════════════════════
> # ORCHESTRATOR SYNTHESIS — <YYYY-MM-DD> (<why: resume / post-recon / pre-re-dispatch>)
> ═══════════════════════════════════════════════════════════════════════
>
> ## Assumption Register (live — update status in place, don't append dupes)
> | # | Assumption carried by prior passes | Status | Basis / what would change it |
> ...  (VALIDATED rows cite raw refs; UNVALIDATED rows say what's missing)
>
> ## Unresolved Signals (ranked; the concrete threads to pull)
> | Signal | Why it matters | Investigated? |
> ...
>
> ## Immediate next actions (in order)
> 1. ...
>
> ## Evidence-backed facts (safe to rely on; don't re-derive)
> - ...  (only things you actually validated against raw evidence)
> ═══════════════════════════════════════════════════════════════════════
```

The Assumption Register is **live state**: on a later invocation, update the
existing rows' Status in place (UNVALIDATED→VALIDATED/INVALIDATED as
evidence arrives) rather than pasting a second register below the first.

Keep the block tight — it's a decision aid the next agent reads first, not a
retelling of the notes. Do not delete the detailed pass reports below it;
this sits on top of them.

## Handing off

After writing the register, the orchestrator's next dispatch prompt is built
from the **Immediate next actions** and **Unresolved Signals**, framed as
*testing the UNVALIDATED assumptions* — never as re-confirming a conclusion.
Explicitly tell the re-dispatched agent which prior conclusions are now
marked UNVALIDATED and why, so it doesn't repeat the flattened reasoning.

## Prevention (the upstream half this skill can't fix on its own)

A synthesis pass cannot recover evidence discarded at collection time. The
complementary rule lives in `pwn-box` and applies to every stage agent:
**persist raw evidence to durable notes, never redact a load-bearing field
to shorten a note, and graduate any data dump out of `/tmp` before the
session ends.** If this skill finds a conclusion resting on discarded
evidence, log both the signal (re-collect X) AND — if it's a recurring
pattern — flag the collection-time gap so the agent instructions get
tightened, not just this one dataset re-pulled.
