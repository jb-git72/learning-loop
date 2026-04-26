# Compliance Checker Test Fixtures

Hand-labeled JSON fixtures used by the automated accuracy evaluator for
`engine/compliance_checker.py`. Each fixture is one piece of FMTH-style
marketing copy plus the expected pass/fail verdict for one or more rules
defined in `shared/regulatory/csf-australia/compliance_rules.json`.

The evaluator runs each fixture through `check_compliance(...)` and
compares the actual rule-by-rule outcome against the `expected` dict.
Per-rule precision and recall are reported.

## Schema

Every fixture is a single JSON object:

```json
{
  "fixture_id": "ADV-001_pass_canonical",
  "description": "Email contains the exact canonical CSF risk warning at the bottom — should pass ADV-001.",
  "text": "...marketing copy here...",
  "content_type": "email",
  "applies_to": "issuer",
  "expected": {
    "ADV-001": "pass"
  }
}
```

### Field reference

| Field | Type | Notes |
|---|---|---|
| `fixture_id` | string | Must equal the filename (without `.json`). Format: `<RULE_ID>_<pass\|fail\|edge>_<short_descriptor>`. |
| `description` | string | One sentence, plain English, what scenario this fixture tests. |
| `text` | string | The marketing copy to evaluate. Realistic FMTH-style equity-crowdfunding voice. Keep it 50-400 words. |
| `content_type` | string | One of `email`, `landing-page`, `meta-ad`, `social-post`, `offer-document`. |
| `applies_to` | string | One of `issuer`, `intermediary`, `both`. Currently all FMTH fixtures are `issuer`. |
| `expected` | object | Map of `rule_id` → `"pass"` or `"fail"`. Only include rules you are confident about — the evaluator ignores rules not listed. |

## Conventions

- **Filename = `fixture_id` + `.json`.** Keep the two in sync.
- **One scenario per fixture.** Don't stuff multiple rule violations into the
  same text unless the goal is explicitly an interaction test.
- **Don't reuse text across fixtures.** Each one should be a distinct scenario.
- **Under-specify rather than mislabel.** If you're not sure whether a rule
  should pass or fail for a given fixture, leave it out of `expected`.
- **`edge` fixtures are deliberate.** They exist to catch known calibration
  gaps in the LLM judges. Some are labeled with the answer a human
  compliance officer would give, even if the current model gets it wrong.

## Adding a new fixture

1. Read the rule definition in `compliance_rules.json` (the `claim`,
   `severity`, `scope`, and `llm_prompt` fields).
2. Decide on a scenario: pass, fail, or edge.
3. Pick a `fixture_id` of the form
   `<RULE_ID>_<pass|fail|edge>_<short_descriptor>` — the filename and
   `fixture_id` must match.
4. Write the marketing copy. Keep it 50-400 words and FMTH-flavoured
   (regenerative grocery, Brookvale hub, Birchal CSF round, partner farms).
5. Set `expected` to only the rules you can confidently label.
6. Save as `engine/tests/fixtures/compliance/<fixture_id>.json`.
7. Run the evaluator to confirm the fixture loads and the expected vs
   actual diff is what you intended.

## Why some fixtures are calibration tests

A handful of fixtures are flagged as `CRITICAL CALIBRATION TEST` in the
delivery report. These cover known model weaknesses, including:

- LLM treating future scheduled dates as "stale" (no temporal context).
- LLM warning on MISL-004 even when copy contains zero forecasts.
- ADV-006 imbalance check firing on short Meta ads with brief in-body risk
  acknowledgement.
- ADV-017 currently runs on email/landing-page content, but its scope is
  meant to be issuer comments on the intermediary's communication facility
  only.

These fixtures are labeled with the **correct** verdict (what a human
compliance officer would say). The evaluator will surface regressions if
the model output drifts from that.
