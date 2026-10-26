# Final-project narrative (draft text for report.html and slides.html)

Use numbers only from `03_results_fact_sheet.md`. Keep the vision/demo distinction everywhere:
**vision** = all-in-one platform for religious organizations (future); **demonstrated** = AI
service-booking workflow (built and measured).

---

## Report outline (required order; target 10–15 pages)

### 1. Title and links (½ page)
**SERVE — AI agents that turn a temple member's request into a rule-verified, human-approved booking**
Varun Matta · MGT 409 AI Agents · Yale SOM · Fall 2026
Links: GitHub `<REPO URL — TODO>` · Demo video (optional) `<TODO>` · Run: `./start.sh`
One-line: *SERVE's long-term vision is an operating platform for temples; this project demonstrates
its first AI workflow — service intake, priest matching, scheduling, and human-approved booking.*

### 2. Motivation (1½ pages)
- Context [Evidence]: ~3.0 million US Hindus (Pew 2020), North America +55% 2010–2020; ~1,600
  temples and centers in a dated c. 2011 census.
- Founder hypothesis [Hypothesis]: temple operations are fragmented — phone/email puja requests,
  WhatsApp and spreadsheets for priests and volunteers, separate donation and event tools.
- Why the booking workflow first: it is constraint-heavy. [Measured, fictional data] finding valid
  options means weighing 3.5 qualified priests, 2.5 calendars, ~31 candidate times and ≈277 rule
  checks on average; 9 of 35 requests correctly end in "no availability".
- A worked example (C01): "griha pravesh in Hamden on Saturday the 21st, morning, in Telugu, 25
  guests, mother uses a wheelchair" → only one priest qualifies and speaks Telugu.

### 3. What is new (1–1½ pages)
- Landscape table (from `01_competitive_landscape.md`): Planning Center, Pushpay/Tithely, ShulCloud,
  Masjidbox, Temple Hub, Booking Ninjas, SmartPuja/Poojyo, Teertham.
- Honest read: platform features exist (incl. US temple software); booking is form/calendar-based;
  AI in the space is mostly information chatbots. We found no product that reads a free-text
  request and checks qualification, language, travel and conflicts automatically
  (research-limited).
- Two-level differentiation: vision (vertical SaaS, temple-specific depth) vs demonstrated
  (agentic intake + deterministic verification + human approval + auditable cost).

### 4. Agents (2½–3 pages) — the core section
- Architecture diagram + sequence diagram (`evidence/architecture.md`, render as SVG).
- Intake Agent: structured `IntakeResult`; catalog in a cached prompt prefix; `get_member_profile`.
- Scheduling Agent: 6 read-only tools; structured `ScheduleRecommendation`; limits (10 requests,
  16 tool calls, per-tool budgets, 120 s).
- Deterministic layer: missing-info check, time windows, re-verification of every option, prices
  from the DB, booking only via the admin approval route (transaction + unique index).
- **Real run walkthrough** with screenshots: member sheet → admin detail (extraction, evidence,
  trace with tokens/cost) → approve → booking after refresh (`evidence/phase1/screenshots/`,
  `evidence/phase2_screenshots/`).
- Evaluation: 27-case set + 15 held-out; expected answers fixed in advance and oracle-checked;
  baseline 21/27 → v2 26–27/27; held-out 14/15 vs rules-only 10/15; failure analysis.

### 5. Tokenomics (1½ pages)
- Table C from the fact sheet (Phase 1 vs standard vs optimized), per-agent breakdown, run-to-run
  variance.
- What the optimization did: catalog in static prefix (intake 2.07 → 1.07 model requests),
  compact tool results, server-side verification → −32% cost, −31% latency, same safety.
- Caching verified from API `cached_tokens` (64–65% of input). Pricing source + Azure caveat.
- Projection table D, clearly labelled with assumptions.
- Lesson learned (good report material): Portkey cache replays made an early baseline look 7×
  faster with identical costs — detected, quarantined, and fixed with cache bypass + header logging.

### 6. Safety (1½–2 pages)
- Threat list specific to SERVE; defense layers D1–D6 + design defenses + prompt rules.
- Off/on table (fact sheet B): 2 → 0 unsafe; 10 already resisted by design (say so); 5 attacks
  flagged for staff; legitimate controls unaffected.
- Scripted-model proof of tool budgets and usage limits.
- Model-substitution guard (multi-target Portkey config returned gpt-5.6 for a different model id).
- Residual risks: shared admin token, per-client lockout can lock out real admin, regex screening
  is bypassable (but cannot cause bookings or price changes).

### 7. Impact (1 page)
- Reproducible comparison table (`04_impact_and_roadmap.md` §1–2).
- Estimates labelled (9–18 min or ≈15.5 min manual per request — not measured).
- No real users yet; list the stakeholder evidence to collect.

### 8. Limits and next steps (1 page)
- Limits: fictional data, author-written test set, 2 runs per config, list-price costs, no member
  login, shared admin token, donations/volunteer/RSVP screens are demo-only, no hosting.
- Next steps: temple pilot measuring H1/H2; staff accounts; volunteer coordination agent; event
  staffing; payments; multilingual messages; other faiths (roadmap table).

---

## Slides (≤10; include GitHub URL)

1. **Title** — SERVE: from a member's words to an approved booking · GitHub URL · vision vs demo line.
2. **Problem** — fragmented temple operations (hypotheses) + why booking is hard (3.5 priests,
   ~31 slots, ≈277 checks, 9/35 "no availability").
3. **Vision vs what we built** — platform roadmap greyed out; booking workflow highlighted.
4. **Landscape** — 6-row comparison; "form-based booking vs agentic intake + verification".
5. **How it works** — architecture diagram (two agents, tools, rules engine, approval).
6. **Live run** — screenshots: request → evidence + trace → approve → booking.
7. **Accuracy** — 21/27 → 26–27/27; held-out 14/15 vs rules-only 10/15.
8. **Safety** — off/on chart 2 → 0; layers; "agents cannot book or price".
9. **Cost & speed** — $0.00083 → $0.00056/request, 15.3 s → 10.5 s; ≈$0.64 per 1,000 (projection).
10. **Impact, limits, next** — reproducible workload numbers; estimates labelled; pilot plan; roadmap.

Speaker-note rule: say "measured", "estimated" or "hypothesis" whenever a number is used.
