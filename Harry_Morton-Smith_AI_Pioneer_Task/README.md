# Contract Review Triage — AI Pioneer task

**Harry Morton-Smith**

## Overall approach: AI-assisted, human-directed

I used Claude to build the first working version of this quickly — the
pipeline, the sample contracts, the dashboard — because that's the fastest
way to get from "an idea about triage" to something you can actually look at
and argue with. But a fast build isn't the point of this task; how it gets
checked afterwards is.

So the actual process, not just the output, was:

1. **Claude built a working demo end-to-end, fast** — a first pass at the
   pipeline, the playbook, and the dashboard, based on the brief as written.
2. **I stepped back and applied my own lens** rather than accepting that
   first pass — 7 years in data quality/test engineering, and thinking about
   this as a product with a full lifecycle, not just a clever prompt.
   Concretely, I asked for the thinking to be redone as: assumptions and
   risks, stated explicitly and in that order; then requirements, including
   acceptance criteria written as Gherkin, because that's exactly how I'd
   frame this for a QE audience in a day job; then a testing strategy that
   starts well before UAT, not just at the end.
3. **I corrected the direction where it mattered.** The first pass allowed a
   path to auto-approving contracts without a human, after a pilot period.
   I don't think that's ever acceptable for something feeding a legal
   sign-off — so I removed it. Every contract, fast-tracked or not, still
   gets a human decision, permanently. That wasn't a wording tweak; it's the
   one constraint everything else in this submission has to respect.
4. **I asked for the risks explained in plain English**, not left as a
   table, so that the requirements and testing decisions built on top of
   them are traceable to a reason I actually understood and agreed with —
   not AI output I accepted on faith because it looked thorough.

I think that loop is the actual point of the exercise, more than the tool
itself. An AI can produce a working thing fast. The value I'd bring to this
role is knowing what to interrogate, correct, and hold accountable before it
gets anywhere near a real workflow — including being willing to say "no,
that's not right" partway through a build, not just after reviewing a
finished output.

## The problem, as I read it

Every contract in your queue still needs a human decision. That's not going to
change, and I don't think it should — someone needs to own the risk. What's
broken is that every contract *currently gets the same treatment*: read start
to finish, cold, before anyone knows whether it's a five-minute rubber stamp
or a genuine problem. At month/quarter end, that flat treatment is what turns
a manageable queue into an overwhelming one.

So I didn't try to build something that reviews contracts. I built something
that **reads every contract the second it lands and tells the lawyer where to
spend their attention first** — before they've opened a single one.

## What I actually built

Not a slide. A working pipeline, plus the artefact a lawyer would open on
Monday morning — **shown here as a demo running on mock analysis, standing
in for what an LLM would do on the real, live path (see "This is a demo"
below).**

```
ai-pioneer-task/
├── playbook/playbook.json         The team's known standard positions,
│                                   encoded once, reused every time
├── contracts/                     3 realistic sample contracts (1 mutual
│                                   NDA, 2 order forms) with genuinely
│                                   different risk profiles
├── tool/contract_triage.py        The pipeline: reads a contract, checks
│                                   it against the playbook, sorts it into
│                                   a lane, drafts the redline
├── output/*.json                  The structured result for each contract
└── dashboard/dashboard.html       The actual thing a lawyer opens — a
                                    triaged docket, not a spreadsheet
```

**Run it yourself:** `cd tool && python3 contract_triage.py --mock`, then open
`dashboard/dashboard.html` in a browser. No API key needed — see "This is a
demo — be clear-eyed about what's actually AI here" below for why.

### The playbook is the real product

The tool is not smart on its own. It's only as good as `playbook.json` — the
handful of standard positions ("governing law: England & Wales", "liability
capped at 12 months' fees", "confidentiality: 3 years, not perpetual") that
your legal team already carries in their heads because they've seen the same
three or four requests a hundred times. I wrote a plausible starting version
of that file, clearly marked as a placeholder. In a real two-week sprint,
building the actual playbook — by shadowing a few contract reviews and
writing down what the lawyer already knows — would be most of week one. The
code is the easy part.

### Three lanes, not a yes/no

I split the queue into three, because "AI decides" and "AI does nothing" are
both wrong answers here:

- **Fast-track** — matches the playbook exactly. Still logged for audit, but
  doesn't need a lawyer's morning.
- **Minor flags** — one or two familiar, low-risk asks (perpetual
  confidentiality, wrong governing law) with a redline already drafted. A
  five-minute glance to confirm, not a cold read.
- **Needs review, priority** — genuinely unusual or high-severity terms
  (uncapped liability, one-sided indemnity, missing data protection clause).
  These jump the queue *and* arrive with the deviations already isolated, so
  the lawyer starts from a marked-up summary instead of page one.

The three sample contracts were picked to actually land in each lane — see
`dashboard.html` for how that looks in practice.

### Work in progress: the review loop, not just the triage

The dashboard now also demonstrates the actual review actions, not just the
triage output: each contract can be **cleared from the queue** or **opened
for amendments**. "Open for amendments" currently hands off a plain-text
memo (flags, playbook positions, suggested redlines, and the original
contract text) in a new tab — a stand-in for the real next step, which
would open the flagged clauses directly in a proper editor (Word/Google
Docs) with the suggested redlines already inserted as tracked changes,
rather than text a lawyer has to apply by hand. I'm flagging this
explicitly as unfinished rather than presenting it as done: the point of
this submission is the direction and the reasoning, not a production-ready
editor integration.

Two other gaps I'm deliberately not glossing over, because a real version
of this tool doesn't work without them:

- **Audit trail.** Right now, clicking "Clear" in the demo just removes a
  card from the screen — it doesn't record *who* cleared it or *when*. A
  real version needs every clear/amend action written to a permanent,
  queryable log: reviewer identity, timestamp, the triage level and flags
  the tool showed them at the time, and which playbook version was in use.
  Without that, there's no way to answer "who signed off on this contract"
  six months later, and no way to run the audit sampling described in
  `EVALUATION.md` — you can't randomly re-check fast-tracked contracts if
  there's no record of which ones were fast-tracked, by whom, or when.
- **Contract storage.** This demo works off flat files in `contracts/`.
  A real version needs contracts landing in one persistent, access-
  controlled location — not scattered across email attachments and
  wherever they happened to be uploaded from — so the tool has something
  durable to read from, the audit trail has something to point back to,
  and legal has a single place to go looking for "every NDA we've signed
  with Delaware governing law," not a memory of where it lives.

Neither of these is a nice-to-have bolted on later — they're what turn this
from a demo into something legal could actually be accountable to.

### This is a demo — be clear-eyed about what's actually AI here

**What you're looking at right now, in `--mock` mode, is not AI running
live.** It's my own worked analysis of three contracts, written out once and
hardcoded into `MOCK_ANALYSIS`, so the review quality can be judged without
needing an API key. Nothing in the dashboard right now is a rules engine
*or* a live model — it's me doing the reasoning a model would do, by hand,
one time, and playing it back.

**The real tool is meant to use an LLM to do the actual clause analysis —
not a keyword or regex match against the playbook.** That distinction
matters and I want to be upfront about it rather than let the demo imply
more than it shows. A rules engine can only catch a deviation if it's
phrased the way the rule expects; a contract that expresses the same
liability cap in different words, or introduces an unusual clause the
playbook never anticipated, will slip straight past it. That's the actual
hard part of this problem, and it's the reason an LLM belongs in this
pipeline at all rather than a simpler string-matching script — semantic
comparison against the playbook's intent, and judgement calls on clauses
the playbook doesn't cover, not just literal text matching.

`contract_triage.py` ships with the real path fully written, not just
described: `build_prompt()` is the actual prompt I'd send, and
`call_claude()` is a working call to the Claude API — point
`ANTHROPIC_API_KEY` at it and `--live` runs for real against genuine model
output, no code changes needed. I'd rather show you exactly what the model
would be asked to do, and let my worked mock answers be judged against that
prompt, than dress up hardcoded output to look like a live demo.

## Evaluating it — did this actually help?

See `EVALUATION.md` for the full plan. Headline version: discovery and
requirements first, then a shadow run alongside the human process — running
the real `--live` LLM path, not the mock — measuring the tool's triage
against what the lawyer actually found and how much time it genuinely
saved. A person approves every contract in every lane, always — the
evaluation is about whether the AI-driven analysis earns trust as a
time-saving assistant, not about whether it's ever allowed to act alone.

## If this were an actual two-week sprint

This is how I'd have wanted to spend it, in the spirit of the role itself:

- **Days 1–2:** Sit with legal, shadow 15–20 real reviews, write down every
  "we've seen this before" moment. That becomes the real playbook.
- **Days 3–6:** Build the pipeline against real (anonymised) contracts,
  tune the three-lane thresholds against what the lawyer actually would
  have prioritised.
- **Days 7–9:** Shadow-run live, silently, alongside the human process.
  Compare triage decisions after the fact — no contract auto-approved yet.
- **Days 10:** Hand over: the dashboard, the playbook file (owned by legal,
  not by me), and the eval numbers. Legal decides whether fast-track ever
  goes live, and on what.

## Why I approached it this way

The brief said most of this is boilerplate, the same questions come up
repeatedly, and the bottleneck is that every contract gets equal, undifferentiated
attention. That's a triage problem before it's an automation problem. I'd
rather hand your legal team a tool that makes their queue legible and drafts
the boring 80% for them, and stays firmly out of the 20% that needs their
judgement, than a tool that quietly tries to replace the reviewer and earns
their distrust the first time it gets something wrong.
