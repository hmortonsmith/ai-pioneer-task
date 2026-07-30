# Evaluation & delivery plan

## Problem statement

Legal currently reads every incoming contract — mutual NDAs, small customer
order forms, mostly boilerplate — start to finish, cold, regardless of
whether it turns out to be a five-minute confirm or a genuine issue. Every
contract gets the same flat treatment, and at month/quarter end, when sales
activity spikes, that flat treatment is what turns a manageable queue into
an overwhelming one. The redlines that do come up are usually familiar —
questions and edits the team has already seen and already knows how to
answer.

This document sets out how I'd take a proposed fix for that from an idea to
something legal actually trusts, and how I'd know at each stage whether it's
working.

## My approach

I didn't want to hand over a slide deck of assumptions with no evidence
behind them, or a fully-built tool nobody had sanity-checked. So the plan
and the demo were built together, in this order:

1. **Initial discovery, using Claude.** I used Claude to move fast from "an
   idea about triage" to a working first pass — a sample playbook, a
   pipeline, and a dashboard a lawyer could actually open — so there was
   something concrete to react to rather than a hypothetical.
2. **Refinement, using my own experience.** I then stepped back and applied
   my background in data quality/test engineering and full product
   lifecycle thinking: assumptions and risks stated explicitly, requirements
   written with proper acceptance criteria, and a testing strategy that
   starts well before UAT rather than treating UAT as the first checkpoint.
3. **Iteration, correcting the plan where it mattered.** Working with
   Claude in rounds rather than accepting the first output — including
   removing any framing that implied a contract could ever be approved
   without a human making that decision. That's a permanent constraint on
   this plan, not a phase that gets relaxed later.

The plan below reflects that: AI is used throughout to accelerate discovery,
drafting, and analysis, but every checkpoint that matters is validated by a
person, and every contract this tool ever touches is still approved by a
person.

## What's demo and what's real in this submission

Worth being explicit about, since it matters for judging what this actually
proves: the analysis you can see running right now (`--mock` mode in
`contract_triage.py`, and the dashboard it feeds) is **my own worked review
of three sample contracts, written once and hardcoded** — not a rules
engine, and not a live model call. It exists so the review quality can be
judged without an API key.

**The real tool is designed around an LLM doing the actual clause
analysis** — semantic comparison against the playbook's intent, not literal
text or keyword matching, plus judgement calls on clauses the playbook
never anticipated. That's the part a simpler rules-based script genuinely
can't do: two contracts can express the same liability position in
completely different words, and only a model reading for meaning will treat
them the same way. The real, callable path is written out in full in
`build_prompt()` and `call_claude()` in `contract_triage.py` — running it
against a live API key (`--live`) is how Phase 2 and 3 below are meant to
actually work, not the mock path.

## Delivery plan

### Phase 1 — Discovery & requirements (Week 1)

- Shadow 15–20 real contract reviews with legal to see what "usually
  boilerplate" and "familiar redlines" actually mean in practice.
- Use AI to accelerate drafting: turning shadowed sessions into a first-pass
  playbook of standard positions, and turning the brief into a first-pass
  assumptions/risks list and requirements set — then validate and correct
  all of it against what legal actually said, not what sounded plausible.
- Output: `ASSUMPTIONS_RISKS.md`, `REQUIREMENTS.md` (including acceptance
  criteria written as Gherkin scenarios), and a playbook owned by legal.

### Phase 2 — Initial build & test (Week 1–2, overlapping with Phase 1)

- Build the triage pipeline against the validated playbook and a set of
  real (anonymised) contracts, using the live LLM analysis path — the mock
  analysis in this submission is a stand-in for this step, not a substitute
  for it.
- Test before any human ever sees live output: a golden-dataset regression
  suite with outcomes agreed with legal, paraphrase/consistency checks
  (same clause, reworded, same result — this is specifically where an LLM
  earns its place over a simpler rules-based script), and adversarial
  testing for things like hidden or injected instructions in contract text
  — a security-conscious habit worth building in regardless of industry.
- Output: the working pipeline running real model calls, plus a passing
  automated test suite as the entry criteria for Phase 3.

### Phase 3 — Shadow-run UAT (Week 3–4)

- The tool runs on every incoming contract in parallel with the existing
  process. Legal reviews exactly as they do today, without seeing the
  tool's triage level in advance, to avoid anchoring their own judgement.
- After each review, compare the tool's triage level and flags against what
  the lawyer actually found. Track hardest: any contract the tool marked
  Fast-track or Minor flags where the lawyer found a real issue anyway —
  that's the number that has to be zero, not just low.
- Also track: flag-level precision, lawyer-reported time to close out a
  contract with the triage summary open, and whether suggested redlines get
  used as-is, edited, or discarded (the clearest signal on whether the
  playbook itself is accurate).
- Entry criteria for Phase 4: zero missed high-severity issues across the
  shadow run, and at least 50% reported time saved on Fast-track/Minor-flags
  contracts.

### Phase 4 — Rollout & ongoing monitoring

- The tool goes live across all three lanes at once, because the lanes only
  ever change how fast a contract gets to a person, never whether one does.
  "Fast-track" means the lawyer opens it, sees zero flags and the reasoning
  behind that, and makes the approval decision themselves in a couple of
  minutes instead of a cold full read — the decision is always theirs, on
  every contract, permanently.
- **Audit trail, built before rollout, not after.** Every clear/amend
  action needs to be written to a permanent, queryable record: reviewer
  identity, timestamp, the triage level and flags shown at the time, and
  which playbook version was live. This isn't optional infrastructure —
  it's what makes "who signed off on this contract" answerable months
  later, and it's a hard prerequisite for the audit sampling below: you
  can't randomly re-check fast-tracked contracts if there's no record of
  which ones were fast-tracked, by whom, or when.
- **A single, access-controlled storage location for every contract**,
  replacing wherever they currently land (email attachments, ad hoc
  uploads). The tool needs somewhere durable to read from, the audit trail
  needs something to point back to, and legal needs one place to answer
  "show me every contract with X clause," not institutional memory.
- A random sample of contracts, across all three lanes, still gets pulled
  for a full, unannounced human read on an ongoing basis, specifically to
  catch automation bias (a lawyer trusting the tool's flags too readily
  over time) and playbook drift, not just to catch tool errors.
- Playbook owned by legal, versioned, and reviewed on a set cadence. Repeated
  "non-standard" flags on the same term across several contracts is usually
  a sign the market has moved and the playbook needs updating — not that
  several counterparties independently asked for the same one-off.

## What "success" looks like in three months

- Queue backlog at month/quarter-end visibly flattens, measured in
  contracts outstanding at end of business each day.
- Lawyer time shifts from reading boilerplate to the genuinely judgement-
  heavy contracts, and they'll say this directly if you ask — a signal
  worth trusting alongside the numbers.
- Zero incidents where a Fast-tracked contract turns out to have contained
  a real issue that a lawyer's own approval step didn't catch. That's a
  harder bar than "usually right," and it's the right bar.

## What I'd explicitly not claim

I would not present this as a tool that reduces headcount need, or as one
that's "done" after Phase 2. The playbook needs an owner inside legal who
updates it as positions change; without that, accuracy decays quietly and
nobody notices until a fast-tracked contract turns out to be wrong. And no
phase of this plan ever removes the requirement that a person approves each
contract — that's a constant across every phase above, not a milestone to
graduate past.

I also wouldn't claim this is ready for Phase 4 as submitted. The audit
trail and the contract storage location described above don't exist yet —
right now the demo's "Clear" button doesn't record who cleared what, and
contracts live as flat files in a folder. Both are named explicitly as
prerequisites, not afterthoughts, because a legal team can't be accountable
to a system that doesn't remember who decided what.
