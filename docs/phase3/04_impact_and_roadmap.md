# Impact (reproducible) and roadmap

## Impact — what we can show

### 1. Reproducible operational comparison (same 42 requests, same scorer)
Commands and outputs are in the repo; anyone can rerun them.

| Approach | Held-out accuracy (15 messy requests) | Time to options | Cost / request | Notes |
|---|---|---|---|---|
| Rules-only keyword parser + same rules engine | 10/15 (88.9% fields) | ~1 ms | $0 | Breaks on "the 21st", "11ish", "twenty five ppl", "after 4", "after lunch" |
| SERVE agents (optimized) + rules engine | **14/15 (98.8% fields)** | **11.3 s mean** | **$0.00063** | 1 miss: "after 4" read as any time (options still valid) |
| Manual coordinator | not measured | **estimated** 9–18 min | staff time | See estimate model below |

Commands: `python -m tests.eval.rules_heldout`, `python -m tests.eval.run_eval --set heldout --label …`.

### 2. Workload removed from staff (deterministic, from the database)
`python -m tests.eval.manual_workload` → for 35 complete requests a coordinator would need, on
average, to consider 3.5 qualified priests, check language (2.5 remain), open 2.5 priest-day
calendars, test 30.8 candidate times (≈277 rule checks), and look up travel for 15 of 35 home
requests; 9 of 35 correctly end with "no availability". In SERVE those checks run automatically
and the administrator reviews evidence and clicks **Approve** (one click; or edit, check and
approve).

### 3. Quality and control
- Every option shown to staff passed the rules engine; 0 agent proposals needed to be dropped
  across all v2 runs; approval re-checks inside a transaction (forced conflicts → 409).
- Clarifying questions are asked immediately (needs-info cases: C07–C09, C17, C22, H05, H09 all
  answered correctly).
- Full audit trail and per-run cost visible to staff.

### 4. Estimates (clearly labelled; no staff were timed)
- Trace-based: 4.8 lookups/request × 1–3 min + 4 min → **≈ 9–18 min** per request.
- Workload-based: 1 min/calendar + 0.25 min/candidate slot + 3 min travel + 4 min → **≈ 15.5 min** (corrected in Phase 4; earlier draft said 14.3).
- Neither number is a measured time saving.

### 5. What is NOT claimed
No temple has used SERVE; no stakeholder feedback, adoption numbers, testimonials or measured
time savings exist. Data is fictional.

### 6. Stakeholder feedback worth collecting next (unverified)
1. Temple office manager: time 5–10 real service requests end to end (messages, minutes).
2. Priests: do suggested slots respect preparation, travel and ritual timing (muhurta) realities?
3. Members: are clarifying questions and proposed times clear? (5-question survey)
4. Board/treasurer: acceptable cost per request; privacy expectations for member data.

## Roadmap (future — none of this is implemented beyond demo UI)

| Priority | Opportunity | Why it fits the platform | What exists today |
|---|---|---|---|
| 1 | **Volunteer coordination agent** — fill understaffed festival shifts, rank volunteers by past sign-ups/skills, draft asks for approval | Same pattern as booking: read data → propose → human approves | Volunteer UI with in-browser demo data only |
| 2 | **Event staffing** — map festival events to priest, volunteer and hall requirements; detect gaps early | Uses existing events, priests and conflict rules | Events table with real dates; priest blocking by events |
| 3 | **Donations** — real payments (e.g. Stripe), receipts, fund reporting; AI only for summaries/anomalies | Core revenue workflow for temples; not an AI-first problem | Demo donation sheet (no payments) |
| 4 | **Multilingual engagement** — member messages and confirmations in Telugu, Tamil, Gujarati, Hindi | Language is already a scheduling constraint; LLMs handle translation | Language matching for priests only |
| 5 | **Broader religious organizations** — churches, mosques, synagogues, Buddhist centers | Data model already organization-generic | Types only; single sample temple |
| Foundations | Real staff accounts and roles, member login, notifications (email/SMS), hosted deployment, data-privacy policy | Required before any real temple pilot | Shared demo admin token; single demo member |

Suggested validation sequence: pilot the booking workflow with one temple office (measure H1/H2),
then add volunteer coordination for one festival.
