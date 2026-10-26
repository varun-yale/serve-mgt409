"""Code-level safety defenses (switchable for the safety evaluation).

Layer map used in evidence:
  D1 input sanitation      unicode normalization, invisible characters removed, prompt
                           delimiter tags in member text neutralized
  D2 injection screening   pattern flags on member text -> risk flag shown to staff + audit
                           (the request is still processed; nothing is auto-approved anyway)
  D3 output filtering      member-facing model text is checked for contact data and for
                           booking/price claims before it is shown
  D4 duplicate/rate guard  identical open request is reused; per-member submission rate cap
  D5 tool budgets          per-tool call caps inside one agent run (on top of UsageLimits)
  D6 admin lockout         repeated bad admin tokens from one client are throttled
  P1 prompt hardening      explicit rules in both agent prompts (always on in v2 prompts)
Always-on design defenses (not switchable): agents have no write tools; every option is
re-verified by the rules engine; prices come only from the database; bookings are created
only by the token-protected admin approval route inside a transaction.
"""

from __future__ import annotations

import os
import re
import unicodedata

_INVISIBLE = re.compile(r"[​-‏‪-‮⁠-⁤﻿]")
_DELIMS = re.compile(r"</?\s*(member_request|system|assistant|developer|instructions?)\s*>", re.I)

INJECTION_PATTERNS = {
    "override_instructions": r"\b(ignore|disregard|forget|override)\b.{0,40}\b(instruction|prompt|rule|polic)",
    "role_change": r"\byou are now\b|\bact as (the )?(admin|administrator|system|developer)\b|\bdeveloper mode\b",
    "prompt_exfiltration": r"\b(reveal|show|print|repeat|output)\b.{0,30}\b(system prompt|instructions|your prompt)\b",
    "approval_bypass": r"\b(approve|confirm|book)\b.{0,30}\b(immediately|now|without (review|approval)|automatically)\b|\bmark (it|this|the booking|as) (as )?(approved|confirmed)\b",
    "price_manipulation": r"(\$\s?0\b|\bfor free\b|\bwaive(d)?\b.{0,20}\b(fee|price|charge)|\b(price|cost|fee)\b.{0,20}\b(should be|is only|set to|change to)\b)",
    "delimiter_injection": r"</?\s*(member_request|system|assistant|developer)\s*>",
    "data_exfiltration": r"\b(email|phone|address|contact)\b.{0,40}\b(of|for)\b.{0,30}\b(other|all|every|another)\b.{0,15}\b(member|famil|people|user)|\blist (all|every) (member|families|users)\b",
}
_PATTERNS = {k: re.compile(v, re.I | re.S) for k, v in INJECTION_PATTERNS.items()}

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE = re.compile(r"\(?\b\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")
# Affirmative booking/price claims only ("Nothing is booked until…" is fine).
_CLAIMS = re.compile(
    r"(booking|reservation|request|it|this|puja|ceremony|appointment)\s+(is|has been|was)\s+(now\s+)?(confirmed|booked|approved|reserved)"
    r"|\byou('re| are| have been)\s+(confirmed|booked|all set)|\bfree of charge\b|\bfor free\b|\bno charge\b|\$\s?\d", re.I)

TOOL_BUDGET = {"search_available_slots": 8, "verify_slot": 6, "get_priest_day": 6, "get_travel_info": 3,
               "find_qualified_priests": 3, "get_service_details": 3, "list_services": 2, "get_member_profile": 2,
               "get_scheduling_policies": 2}

MAX_SUBMISSIONS_PER_10_MIN = 5
ADMIN_FAILS_BEFORE_LOCK = 10
ADMIN_LOCK_SECONDS = 300


def enabled() -> bool:
    return os.getenv("SERVE_DEFENSES", "on").lower() != "off"


def sanitize(text: str) -> tuple[str, list[str]]:
    """D1. Returns cleaned text and what was changed."""
    changes = []
    t = unicodedata.normalize("NFKC", text)
    if t != text:
        changes.append("unicode_normalized")
    t2 = _INVISIBLE.sub("", t)
    if t2 != t:
        changes.append("invisible_chars_removed")
    t3 = _DELIMS.sub(lambda m: "[" + m.group(1) + "]", t2)
    if t3 != t2:
        changes.append("delimiter_tags_neutralized")
    return t3, changes


def screen(text: str) -> list[str]:
    """D2. Names of injection patterns found in member text."""
    return [name for name, rx in _PATTERNS.items() if rx.search(text)]


def filter_member_text(text: str | None) -> tuple[str | None, list[str]]:
    """D3. Remove contact details; reject text that claims a booking, approval or price."""
    if not text:
        return text, []
    reasons = []
    t = _EMAIL.sub("[removed]", text)
    t = _PHONE.sub("[removed]", t)
    if t != text:
        reasons.append("contact_details_removed")
    if _CLAIMS.search(t):
        return None, reasons + ["booking_or_price_claim_blocked"]
    return t, reasons


def normalize_for_dedupe(text: str) -> str:
    return re.sub(r"\W+", " ", text.lower()).strip()
