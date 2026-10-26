# Problem statement and differentiation

Labels used throughout: **[Evidence]** externally sourced · **[Measured]** from SERVE's own
evaluation files · **[Hypothesis]** founder hypothesis, not yet validated with temples.

## 1. Context

- **[Evidence]** About 3.0 million Hindus lived in the United States in 2020; North America's
  Hindu population grew 55% from 2010 to 2020 (Pew Research, 2025). About 1% of US adults identify
  as Hindu (Pew Religious Landscape Study 2023–24).
- **[Evidence, dated]** A c. 2011 census counted ~1,600 Hindu temples and centers in the US,
  including 258 traditional temples (Institute of American Religion, via ARDA). No authoritative
  current count was found.
- **[Evidence]** Software already exists for churches (Planning Center, Pushpay, Tithely),
  synagogues (ShulCloud), mosques (Masjidbox), and Hindu temples (Temple Hub, Booking Ninjas).

## 2. Problem statement (founder hypotheses)

> Hindu temples in the US are typically run by a small paid staff, priests and many volunteers.
> **[Hypothesis]** Their operations are spread across disconnected tools — paper or phone requests
> for pujas, spreadsheets or WhatsApp for priest and volunteer schedules, a separate payment or
> donation app, email newsletters and an outdated website — so staff re-enter information and
> members don't know where to go.

Specific hypotheses (none yet validated with real temples):

| # | Hypothesis | How to validate |
|---|---|---|
| H1 | Religious-service requests (griha pravesh, satyanarayan, namakaranam) arrive by phone, email or in person and take several back-and-forth exchanges to schedule | Time 5–10 real requests at a temple office; count messages per request |
| H2 | Matching a request requires checking several constraints staff hold in their heads or spreadsheets: priest qualification, language, travel distance, existing bookings, festival days, priest leave | Interview the office manager and priests; list the checks they perform |
| H3 | Volunteer coordination for festivals relies on group chats and sign-up sheets | Review a festival's volunteer process |
| H4 | Donations, events and communications live in separate tools that don't share member data | Inventory tools at 3–5 temples |
| H5 | Multilingual communities (Telugu, Tamil, Gujarati, Hindi…) need service in their language, and staff must remember which priest speaks what | Ask temples how they handle language requests |

**[Measured]** What we *can* show today is that the scheduling step is constraint-heavy. Across
the 35 complete requests in our evaluation set, finding valid options means weighing on average
3.5 qualified priests, opening 2.5 priest-day calendars, testing ~31 candidate times and ≈277
individual rule checks; in 9 of 35 the correct answer is "no availability" (for example, the only
Telugu-speaking priest is on leave, or the town is beyond the travel radius)
— `evidence/impact/manual_workload.md`. That is evidence about the problem's *structure* (using
fictional data), not about how long real temples take.

## 3. Differentiation at two levels

### Level 1 — Long-term vision (not implemented; startup thesis)
SERVE intends to become an **all-in-one vertical SaaS operating platform for religious
organizations, starting with Hindu temples in the US**: service reservations and scheduling,
donations, events, volunteering and community communication on one member record.

- Honest competitive read: this feature list overlaps with existing products, including a
  US temple platform (Temple Hub, listed from $499/month) and configurable Salesforce-based
  software (Booking Ninjas). The vision's differentiation would have to come from **temple-specific
  depth** (priest qualifications, languages, ritual calendars, home-visit logistics), **price and
  ease for volunteer-run temples**, and an **AI-first operating model** — all hypotheses.
- The data model is already organization-generic (`Organization`, not "temple") so churches,
  mosques, synagogues and Buddhist centers could use the same shapes.

### Level 2 — What the MGT 409 project demonstrates (implemented and measured)
One AI-powered operational workflow: **service intake → priest matching → scheduling →
human-approved booking.**

| Differentiator | Demonstrated by |
|---|---|
| Members describe needs in their own words; agents extract structured requests and ask only for what's missing | 26–27/27 main-set and 14/15 held-out cases correct (optimized profile) |
| Every proposal is checked against real constraints (qualification, language, hours, leave, bookings, festivals, travel, lead time) by a deterministic rules engine — the model cannot override it | 0 agent proposals failed re-verification; 0 bookings created by agents; forced conflicts return HTTP 409 |
| Human approval is the only path to a booking | Approval route is token-protected and re-checks rules inside a transaction |
| Safety is engineered and tested, not assumed | 12 attacks: 2 succeed with new defenses off, 0 with defenses on; 10 already resisted by design |
| Cost is measured and small | $0.00046–0.00057 per request (optimized, list price); projected ≈ $0.64 per 1,000 member requests |
| Every run is auditable | Per-run tokens, cost, latency, tool calls, Portkey route, audit log |

What it does **not** claim: real temple adoption, user feedback, measured staff time savings,
or that the broader platform (donations, volunteering, events) is AI-powered or production-ready.
The member portal's donation, RSVP and volunteer screens are pre-existing demo UI kept in the
browser only.
