# Compliance accuracy evaluation

- Fixtures loaded: 36
- Total rule labels evaluated: 36
- LLM mode: ENABLED — claude-sonnet-4-6
- Overall accuracy: **88.9%** (32/36)
- Labels skipped because rule was out-of-scope for the fixture: 3

## Per-rule scoreboard

| Rule | Sev | Labeled | TP | FP | TN | FN | Acc | Prec | Rec | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ADV-001 | BLOCKING | 3 | 2 | 0 | 1 | 0 | 100% | 100% | 100% | 1.00 |
| ADV-002 | BLOCKING | 3 | 1 | 0 | 2 | 0 | 100% | 100% | 100% | 1.00 |
| ADV-003 | BLOCKING | 3 | 2 | 0 | 1 | 0 | 100% | 100% | 100% | 1.00 |
| ADV-004 | WARNING | 3 | 1 | 0 | 2 | 0 | 100% | 100% | 100% | 1.00 |
| ADV-005 | WARNING | 3 | 1 | 0 | 2 | 0 | 100% | 100% | 100% | 1.00 |
| ADV-006 | WARNING | 3 | 1 | 0 | 2 | 0 | 100% | 100% | 100% | 1.00 |
| ADV-007 | BLOCKING | 3 | 1 | 0 | 2 | 0 | 100% | 100% | 100% | 1.00 |
| ADV-013 | WARNING | 3 | 2 | 0 | 1 | 0 | 100% | 100% | 100% | 1.00 |
| MISL-001 | BLOCKING | 3 | 1 | 0 | 2 | 0 | 100% | 100% | 100% | 1.00 |
| MISL-004 | WARNING | 3 | 1 | 0 | 2 | 0 | 100% | 100% | 100% | 1.00 |
| MISL-002 | WARNING | 3 | 1 | 0 | 1 | 1 | 67% | 100% | 50% | 0.67 |

## False negatives (1) — rule should have fired but didn't

- **[MISL-002]** `MISL-002_fail_unstable_number`
  - text: `15+ Named Farms. One Honest Supply Chain.  FarmThru works with 15+ named regenerative partner farms across NSW. Every on...`

## Out-of-scope labels (3) — fixture lists a rule its scope filters out

- [ADV-017] `ADV-017_fail_marketing_slogan` (expected=fail)
- [ADV-017] `ADV-017_fail_softball_self_question` (expected=fail)
- [ADV-017] `ADV-017_pass_genuine_qa` (expected=pass)
