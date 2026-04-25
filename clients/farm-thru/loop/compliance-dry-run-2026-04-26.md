# CSF compliance dry-run — FMTH

- LLM judges: disabled (cheap pass)
- Total content pieces: 26
- Passed (zero BLOCKING): 25 / 26
- Total BLOCKING violations: 3
- Total WARNINGs: 0

## Per-piece summary

| ID | Type | Eval | Pass | Blocking | Warnings |
|---|---|---:|:---:|---:|---:|
| EM-NONVIP-01 | email | 11 | OK | 0 | 0 |
| EM-NONVIP-02 | email | 11 | OK | 0 | 0 |
| EM-NONVIP-03 | email | 11 | OK | 0 | 0 |
| EM-VIP-01 | email | 11 | OK | 0 | 0 |
| EM-VIP-02 | email | 11 | OK | 0 | 0 |
| EM-VIP-03 | email | 11 | OK | 0 | 0 |
| EM-WELCOME-NONVIP | email | 11 | OK | 0 | 0 |
| EM-WELCOME-VIP | email | 11 | OK | 0 | 0 |
| index-b | landing-page | 10 | OK | 0 | 0 |
| index-c | landing-page | 10 | OK | 0 | 0 |
| index-d | landing-page | 10 | OK | 0 | 0 |
| index-e | landing-page | 10 | OK | 0 | 0 |
| index-f | landing-page | 10 | OK | 0 | 0 |
| index-g | landing-page | 10 | OK | 0 | 0 |
| index-h | landing-page | 10 | OK | 0 | 0 |
| index-i | landing-page | 10 | OK | 0 | 0 |
| index-j | landing-page | 10 | OK | 0 | 0 |
| index-k | landing-page | 10 | OK | 0 | 0 |
| index-l | landing-page | 10 | OK | 0 | 0 |
| index-m | landing-page | 10 | OK | 0 | 0 |
| index-n | landing-page | 10 | OK | 0 | 0 |
| index-o | landing-page | 10 | OK | 0 | 0 |
| index-p | landing-page | 10 | OK | 0 | 0 |
| index-q | landing-page | 10 | OK | 0 | 0 |
| index | landing-page | 10 | OK | 0 | 0 |
| FIXTURE-BROKEN | email | 11 | FAIL | 3 | 0 |

## Failing pieces — BLOCKING violations

### FIXTURE-BROKEN  (email)
- **[ADV-001]** (RG-261.92/s738ZG(6)) — Add 'Always consider the general CSF risk warning and offer document before investing.' to the bottom of the content.
  - context: `(no canonical phrase found in content)`
- **[ADV-002]** (RG-261.96/RG-261.99/founder directive 2026-04-25) — Remove specific investment $ amounts. Use generic phrasing like 'small refundable deposit' or 'low minimum entry'.
  - matched: `$5 refundable`
  - context: `...our VIP spot today for just a $5 refundable deposit! Reply to this email...`
- **[ADV-003]** (RG-261.115/s736) — Remove. Investments must go via the licensed CSF intermediary (e.g. Birchal), not via direct contact.
  - matched: `Reply to this email to apply`
  - context: `...just a $5 refundable deposit! Reply to this email to apply. Minimum $50, maximum $10,000...`
