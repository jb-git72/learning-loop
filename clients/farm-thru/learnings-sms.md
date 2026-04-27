# SMS Learnings

## Hard limits
- Single segment = 160 chars (target). Two segments = 320 max. Count the EXPANDED merge tag, not `{{birchal_url}}`. Birchal short URLs ~30 chars.
- Three+ segments = fail. SMS gateways treat as multiple billed messages and recipient sees a stitched mess.

## Compliance (FMTH / CSF)
- The Birchal URL IS the regulatory workaround for SMS char-limits. It routes recipients to the canonical CSF risk-warning page where the offer doc + safe-harbour line live. Any investment-context SMS MUST include a URL OR the short paraphrase `general CSF risk warning`.
- Compliance gate ADV-001 accepts the short paraphrase for SMS (added 2026-04-27). The full canonical line `Always consider the general CSF risk warning and offer document before investing.` does NOT need to fit inside a 160-char SMS — the link to the destination page satisfies it.
- Confirmations (sent in reply to a Stripe purchase) are transactional under Spam Act 2003 — no opt-out required, no link required.
- Marketing sends to a list (round-opens, reminders): MUST end with `Reply STOP to opt out.`

## Banned phrases / tone
- No `priority` (FMTH-PRIORITY-001 — replace with `early`).
- No explicit dollar amounts (`$5`, `$50`, `$10K`) in any SMS body.
- No em-dashes. No `huge`, `unmissable`, `act now`, `don't miss`. Single exclamation max — usually zero.
- Never two jobs in one SMS. Round-opens drives to the link. Confirmations reassure. Reminders nudge. Pick one.

## Voice
- Factual takes priority over warmth. SMS is a notification, not a love letter.
- Founder voice OK for round-opens (`We're live`) but the brand name + link + opt-out always come first.
- Lower-case after the brand name reads more human than Title Case.

## Patterns that work
- Round-opens: `<Brand>'s <thing> is now live: <url> Reply STOP.`
- Confirmation: `You're in. <what they got>. <next step>. <refund / contact>.`
- The word `secured` reads warmer than `confirmed` for VIP deposit confirms.
