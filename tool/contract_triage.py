#!/usr/bin/env python3
"""
contract_triage.py
-------------------
A first-pass AI triage tool for low-stakes commercial contracts (mutual NDAs,
order forms) against a legal team's known "playbook" of standard positions.

WHY THIS EXISTS
This does not replace the lawyer. It reads every contract the moment it lands,
compares it against the playbook of positions the team already knows and
accepts, and sorts the queue into three lanes:

    FAST_TRACK        -> matches the playbook, no material deviations found
    MINOR_FLAGS        -> one or two familiar, low-risk deviations with a
                          suggested redline already drafted
    NEEDS_REVIEW        -> multiple or high-severity deviations; a lawyer
                          should look at this first, with the analysis done
                          for them so they start from a summary, not a
                          blank page

A lawyer still makes every decision. The tool's job is to make sure their
attention goes to the 20% of contracts that need it, first, with the
30 minutes of "read the whole thing to find what's different" already done.

CURRENT STATUS: WORK IN PROGRESS
The dashboard now includes a first pass at the interactive review actions
(Clear from queue / Open for amendments) so the review loop can be tried
end to end, not just described. The "open for amendments" action currently
opens the raw contract text in a new tab as a stand-in for a real redline
editor -- the next real iteration would open the flagged clauses directly
in a proper editor (e.g. a Word/Google Docs integration) with the suggested
redlines pre-inserted as tracked changes, rather than plain text a lawyer
has to edit by hand.

HOW TO RUN THIS
    python contract_triage.py --mock
        Runs on the three sample contracts in ../contracts using pre-written
        analysis (see MOCK_ANALYSIS below) so this can be evaluated with no
        API key and no external calls -- useful for this task, and for a
        pilot demo before anyone trusts it with real contract text.

    python contract_triage.py --live
        Runs the real pipeline: reads each contract, calls the Claude API
        with the prompt in build_prompt(), and parses the structured JSON
        response. Requires ANTHROPIC_API_KEY to be set. This is the
        production path -- see call_claude() below.

In both modes, the tool writes one JSON file per contract to ../output/ and
a combined ../dashboard/dashboard_data.js for the review dashboard to read.

A NOTE ON DATA HANDLING
Contracts often contain commercially sensitive terms. A real deployment
should run against an enterprise API agreement with no training on inputs
(Anthropic's commercial terms already provide this), redact counterparty
names before any logging, and keep the playbook and outputs inside the
company's own infrastructure rather than a third-party SaaS tool.
"""

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT / "contracts"
PLAYBOOK_PATH = ROOT / "playbook" / "playbook.json"
OUTPUT_DIR = ROOT / "output"
DASHBOARD_DIR = ROOT / "dashboard"


def load_playbook():
    with open(PLAYBOOK_PATH, "r") as f:
        return json.load(f)


def build_prompt(contract_text: str, playbook: dict) -> str:
    """
    The prompt used in --live mode. Shown here in full because the prompt
    IS the product logic -- this is where the legal team's judgement gets
    encoded, not in a black box.
    """
    return f"""You are supporting an in-house legal team by triaging a routine
commercial contract against their standard playbook positions. You are not
making the final call -- a lawyer reviews everything you flag. Be precise,
conservative, and never invent a clause that is not in the text.

PLAYBOOK (the team's known, pre-agreed standard positions):
{json.dumps(playbook, indent=2)}

CONTRACT TEXT:
---
{contract_text}
---

Return ONLY valid JSON matching this schema:
{{
  "contract_type": "Mutual NDA | Order Form | Other",
  "triage_level": "FAST_TRACK | MINOR_FLAGS | NEEDS_REVIEW",
  "flags": [
    {{
      "clause_area": "e.g. governing_law",
      "issue": "plain-English description of the deviation",
      "contract_position": "what the contract actually says",
      "playbook_position": "what the team's standard position is",
      "severity": "low | medium | high",
      "suggested_redline": "drafted replacement language, ready to paste in, or null if no clean redline exists and it needs a human judgement call"
    }}
  ],
  "summary": "2-3 sentence plain-English summary for the lawyer opening this contract cold",
  "estimated_minutes_saved": "integer estimate of minutes saved vs. reading the contract unaided, based on number and complexity of flags"
}}

Rules:
- Only flag genuine deviations from the playbook. Do not flag clauses that are simply absent if the playbook does not require them (e.g. do not expect a liability cap in a mutual NDA that has no liability clause at all -- that's normal).
- If a clause is materially one-sided, ambiguous, or introduces obligations that are unusual for this contract type, flag it even if not explicitly covered by the playbook, and mark severity "high" with a note that it falls outside the current playbook.
- triage_level = NEEDS_REVIEW if any flag is "high" severity, or 3+ flags of any severity.
- triage_level = FAST_TRACK only if there are zero flags.
- Otherwise triage_level = MINOR_FLAGS.
"""


def call_claude(prompt: str) -> dict:
    """
    Production path. Requires `pip install anthropic` and ANTHROPIC_API_KEY.
    Not called in --mock mode.
    """
    import anthropic  # noqa: local import so --mock mode has no dependency

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = "".join(
        block.text for block in response.content if block.type == "text"
    )
    raw_text = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(raw_text)


# ---------------------------------------------------------------------------
# MOCK ANALYSIS
#
# These are the actual worked reviews for the three sample contracts in
# ../contracts, produced by applying the same prompt/playbook logic above.
# They exist so this tool (and the dashboard it feeds) can be evaluated
# without needing an API key, and so the review quality can be judged on
# its own merits, independent of any particular model or API call.
# ---------------------------------------------------------------------------

MOCK_ANALYSIS = {
    "01_mutual_nda_globex.md": {
        "contract_type": "Mutual NDA",
        "triage_level": "MINOR_FLAGS",
        "flags": [
            {
                "clause_area": "confidentiality_term",
                "issue": "Confidentiality obligations survive 'in perpetuity' with no trade-secret carve-out distinction.",
                "contract_position": "Section 4: confidentiality obligations survive termination 'in perpetuity'.",
                "playbook_position": "3 years post-termination, indefinite only for genuine trade secrets.",
                "severity": "medium",
                "suggested_redline": "Replace Section 4 with: 'The confidentiality obligations set out herein shall survive termination of this Agreement for a period of three (3) years, save that information constituting a trade secret under applicable law shall remain protected for as long as it retains trade secret status.'",
            },
            {
                "clause_area": "governing_law",
                "issue": "Governing law and exclusive jurisdiction set to Delaware rather than England & Wales.",
                "contract_position": "Section 5: governed by Delaware law, exclusive jurisdiction of Delaware courts.",
                "playbook_position": "England & Wales, exclusive jurisdiction of E&W courts.",
                "severity": "medium",
                "suggested_redline": "Replace Section 5 with: 'This Agreement shall be governed by and construed in accordance with the laws of England and Wales. The Parties submit to the exclusive jurisdiction of the courts of England and Wales.'",
            },
        ],
        "summary": "Standard mutual NDA with two familiar asks: perpetual confidentiality (want 3 years) and Delaware governing law (want England & Wales). Both have ready-made counter-language below -- this is a five-minute glance, not a full read.",
        "estimated_minutes_saved": 20,
    },
    "02_order_form_acme.md": {
        "contract_type": "Order Form",
        "triage_level": "FAST_TRACK",
        "flags": [],
        "summary": "Every checked term (governing law, liability cap, renewal notice, data protection, termination for convenience, payment terms) matches the standard playbook position exactly. No deviations found. Recommended for fast-track sign-off, logged for audit trail.",
        "estimated_minutes_saved": 15,
    },
    "03_order_form_northwind.md": {
        "contract_type": "Order Form",
        "triage_level": "NEEDS_REVIEW",
        "flags": [
            {
                "clause_area": "governing_law",
                "issue": "Governing law set to New York with an added right for a Delaware-domiciled affiliate to choose its own forum -- unusual and asymmetric.",
                "contract_position": "New York law; Customer's Delaware affiliate may bring disputes 'in a forum of its choosing'.",
                "playbook_position": "England & Wales, exclusive jurisdiction.",
                "severity": "high",
                "suggested_redline": None,
            },
            {
                "clause_area": "limitation_of_liability",
                "issue": "Liability is explicitly uncapped and extends to indirect and consequential losses, with no carve-out structure at all.",
                "contract_position": "'Total liability... shall be uncapped... including but not limited to indirect, special, and consequential losses.'",
                "playbook_position": "Capped at 12 months' fees, standard carve-outs only.",
                "severity": "high",
                "suggested_redline": "Replace with standard limitation of liability clause: liability capped at 12 months' fees paid or payable under this Order Form, with carve-outs limited to confidentiality breach, IP infringement, gross negligence, and death or personal injury; exclude indirect and consequential losses for both parties.",
            },
            {
                "clause_area": "indemnity",
                "issue": "One-sided, unlimited-scope indemnity ('any and all claims... of any kind') with no reciprocal indemnity from Customer.",
                "contract_position": "Supplier indemnifies Customer for 'any and all claims, losses, damages, and expenses of any kind'.",
                "playbook_position": "Mutual indemnity, scoped to IP infringement and confidentiality breach only.",
                "severity": "high",
                "suggested_redline": "Narrow to mutual indemnity scoped to third-party claims arising from (a) IP infringement and (b) breach of confidentiality obligations, by either party.",
            },
            {
                "clause_area": "auto_renewal",
                "issue": "36-month auto-renewal with a 90-day opt-out right granted to Customer only -- no reciprocal right for Supplier.",
                "contract_position": "Auto-renews for successive 36-month terms; only Customer may give 90 days' notice not to renew.",
                "playbook_position": "Auto-renewal acceptable with mutual right, max 30-60 day notice.",
                "severity": "medium",
                "suggested_redline": "Make the non-renewal right mutual, and reduce notice period to 60 days for both parties.",
            },
            {
                "clause_area": "termination_for_convenience",
                "issue": "No termination-for-convenience right at all for either party during the 36-month term -- only for-cause termination.",
                "contract_position": "'Neither party may terminate... except for material uncured breach.'",
                "playbook_position": "Either party may terminate for convenience on 30 days' notice.",
                "severity": "high",
                "suggested_redline": "Add a mutual termination-for-convenience right on 60 days' written notice, reflecting the longer 36-month term.",
            },
            {
                "clause_area": "data_protection",
                "issue": "Personal data will be shared for professional services, but no data processing / UK GDPR clause is included in this Order Form.",
                "contract_position": "'Customer will share end-user personal data... No data processing terms are otherwise specified.'",
                "playbook_position": "Must reference UK GDPR / DPA 2018 with a standard DPA where personal data is shared.",
                "severity": "high",
                "suggested_redline": "Add the standard Data Processing Addendum by reference, and require both parties to comply with UK GDPR and the Data Protection Act 2018 in respect of any personal data shared under this Order Form.",
            },
            {
                "clause_area": "payment_terms",
                "issue": "Net 60 payment terms, longer than the standard maximum.",
                "contract_position": "Payable Net 60 days from invoice.",
                "playbook_position": "Net 30 standard, Net 45 acceptable maximum.",
                "severity": "low",
                "suggested_redline": "Negotiate down to Net 45; Net 60 should require commercial sign-off, not just legal sign-off.",
            },
        ],
        "summary": "High-risk paper: uncapped liability, a broad one-sided indemnity, no termination-for-convenience right, and a missing data protection clause despite personal data being in scope -- alongside a non-standard forum clause. This is exactly the kind of contract that should jump the queue, and it comes with the deviations already isolated so the lawyer starts from a marked-up list, not page one.",
        "estimated_minutes_saved": 35,
    },
}


def run(mode: str):
    playbook = load_playbook()
    OUTPUT_DIR.mkdir(exist_ok=True)
    DASHBOARD_DIR.mkdir(exist_ok=True)

    contract_files = sorted(CONTRACTS_DIR.glob("*.md"))
    if not contract_files:
        print(f"No contracts found in {CONTRACTS_DIR}")
        sys.exit(1)

    results = []
    for path in contract_files:
        text = path.read_text()

        if mode == "mock":
            if path.name not in MOCK_ANALYSIS:
                print(f"No mock analysis available for {path.name}, skipping.")
                continue
            analysis = MOCK_ANALYSIS[path.name]
        else:
            prompt = build_prompt(text, playbook)
            analysis = call_claude(prompt)

        analysis["contract_file"] = path.name
        analysis["contract_text"] = text
        out_path = OUTPUT_DIR / (path.stem + ".json")
        out_path.write_text(json.dumps(analysis, indent=2))
        results.append(analysis)
        print(f"[{analysis['triage_level']:12}] {path.name} -> {out_path.name}")

    # Combined file the static dashboard reads (no server needed)
    js_path = DASHBOARD_DIR / "dashboard_data.js"
    js_path.write_text("const CONTRACT_DATA = " + json.dumps(results, indent=2) + ";\n")
    print(f"\nWrote {len(results)} results. Dashboard data: {js_path}")
    print(f"Open {DASHBOARD_DIR / 'dashboard.html'} in a browser to view the triage queue.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--mock", action="store_true", help="Use pre-computed analysis, no API key required.")
    group.add_argument("--live", action="store_true", help="Call the real Claude API. Requires ANTHROPIC_API_KEY.")
    args = parser.parse_args()
    run("mock" if args.mock else "live")
