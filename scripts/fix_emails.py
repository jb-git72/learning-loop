"""
Fix three weak scoring dimensions in FarmThru emails (EM-001 to EM-007):
1. scroll_stop_hook — add primary_text field (first 1-2 sentences of body)
2. personalization — add {first_name} greeting, reader context, time signals
3. tactic_execution — add headline field (= subject line)
"""

import json
import pathlib

EMAIL_DIR = pathlib.Path(__file__).resolve().parent.parent / "clients" / "farm-thru" / "loop" / "emails"


def fix_em001(email: dict) -> dict:
    """Welcome email — rewrite generic opening, add personalization."""
    # Fix 1: Rewrite body opening from generic "Welcome." to story hook
    new_opening = (
        'Hi {first_name},\n\n'
        '"I didn\'t know where my chicken came from." That question changed everything.\n\n'
        'Welcome to FarmThru.'
    )
    # Replace the old opening lines
    body = email["body"]
    body = body.replace(
        "Welcome.\n\nYou have just joined the waitlist",
        new_opening + "\n\nYou just joined the waitlist",
    )
    # Add time signal
    body = body.replace(
        "Over the next couple of weeks",
        "Over the next few days",
    )
    email["body"] = body

    # primary_text = the story hook
    email["primary_text"] = "\"I didn't know where my chicken came from.\" That question changed everything."

    # Fix 3: headline = subject
    email["headline"] = email["subject"]

    return email


def fix_em002(email: dict) -> dict:
    """Founder story — body starts with personal story, good hook. Add personalization."""
    body = email["body"]
    # Add {first_name} greeting and time signal
    body = "Hi {first_name},\n\n" + body
    # Add time signal after "More soon."
    body = body.replace(
        "More soon.",
        "Over the next few days, we'll show you the farms and the food. More soon.",
    )
    email["body"] = body

    # primary_text: the opening hook already strong — "I want to tell you why FarmThru exists."
    # But next line is the real story hook with the tray of beef mince
    email["primary_text"] = "I want to tell you why FarmThru exists. A few years ago I was holding a tray of beef mince in a supermarket."

    # Fix 3: headline = subject
    email["headline"] = email["subject"]

    return email


def fix_em003(email: dict) -> dict:
    """Product deep-dive — already has story opening. Add personalization."""
    body = email["body"]
    # Add {first_name} greeting and time signal
    body = "Hi {first_name},\n\nThis week, something worth sharing.\n\n" + body
    email["body"] = body

    # primary_text: strong story hook already present
    email["primary_text"] = "Last month, Rachel Ward watched the supermarket buyer taste her grass-fed beef and say \"this is exceptional\" — then offer her 40% less than it cost to raise."

    # Fix 3: headline = subject
    email["headline"] = email["subject"]

    return email


def fix_em004(email: dict) -> dict:
    """Farm spotlight — already has named farm + moment. Add personalization."""
    body = email["body"]
    # Add {first_name} greeting and time signal
    body = "Hi {first_name},\n\nThis week we're at the farm.\n\n" + body
    email["body"] = body

    # primary_text: strong story hook
    email["primary_text"] = "Yesterday, I watched James from Little Yarran Farm load the last of his 18-month grass-fed cattle onto the truck."

    # Fix 3: headline = subject
    email["headline"] = email["subject"]

    return email


def fix_em005(email: dict) -> dict:
    """Investment thesis — rewrite generic opening to question. Add personalization."""
    body = email["body"]
    # Rewrite generic opener to a question hook
    body = body.replace(
        "You have seen the food. You have met the farms. Now let us talk about what comes next.",
        "Since you signed up, you have seen the food and met the farms. Here is the question: what if you could own a piece of this?",
    )
    # Add {first_name} greeting
    body = "Hi {first_name},\n\n" + body
    email["body"] = body

    # primary_text: question hook
    email["primary_text"] = "Since you signed up, you have seen the food and met the farms. Here is the question: what if you could own a piece of this?"

    # Fix 3: headline = subject
    email["headline"] = email["subject"]

    return email


def fix_em006(email: dict) -> dict:
    """Countdown — rewrite "Quick update." to time-specific hook. Add personalization."""
    body = email["body"]
    # Rewrite generic opener
    body = body.replace(
        "Quick update.\n\nFarmThru's equity crowdfunding campaign on Birchal opens very soon.",
        "In a few days, FarmThru opens to investors on Birchal.",
    )
    # Add {first_name} greeting
    body = "Hi {first_name},\n\n" + body
    email["body"] = body

    # primary_text: time-specific hook
    email["primary_text"] = "In a few days, FarmThru opens to investors on Birchal."

    # Fix 3: headline = subject
    email["headline"] = email["subject"]

    return email


def fix_em007(email: dict) -> dict:
    """Final call — already has story hook with Sarah. Add personalization."""
    body = email["body"]
    # Add {first_name} greeting and time signal
    body = "Hi {first_name},\n\nToday is the last chance.\n\n" + body
    email["body"] = body

    # primary_text: story hook
    email["primary_text"] = "Yesterday at 3pm, Sarah from Manly refreshed her phone for the third time."

    # Fix 3: headline = subject
    email["headline"] = email["subject"]

    return email


FIXERS = {
    "EM-001": fix_em001,
    "EM-002": fix_em002,
    "EM-003": fix_em003,
    "EM-004": fix_em004,
    "EM-005": fix_em005,
    "EM-006": fix_em006,
    "EM-007": fix_em007,
}


def main():
    for fname in sorted(EMAIL_DIR.glob("EM-*.json")):
        email_id = fname.stem
        fixer = FIXERS.get(email_id)
        if not fixer:
            print(f"  SKIP {email_id} — no fixer defined")
            continue

        email = json.loads(fname.read_text())
        email = fixer(email)

        # Verify body under 2000 chars
        body_len = len(email["body"])
        if body_len > 2000:
            print(f"  WARN {email_id}: body is {body_len} chars (over 2000)")

        # Verify primary_text under 200 chars
        pt_len = len(email.get("primary_text", ""))
        if pt_len > 200:
            print(f"  WARN {email_id}: primary_text is {pt_len} chars (over 200)")

        # Count you/your references
        body_lower = email["body"].lower()
        you_count = sum(
            body_lower.count(w) for w in ["you ", "your ", "you're", "you'll", "you."]
        )
        print(f"  {email_id}: body={body_len} chars, primary_text={pt_len} chars, you-refs={you_count}, headline={'yes' if 'headline' in email else 'no'}")

        fname.write_text(json.dumps(email, indent=2) + "\n")

    print("\nDone. All emails updated.")


if __name__ == "__main__":
    main()
