# Competitive landscape (researched 2026-10-25)

Method: web search + fetching vendor/listing pages. "Verified" = read on the vendor's own page
or an official help/product page during this session. "Listing" = third-party directory
(GoodFirms, SourceForge, Capterra) — treat as unverified vendor claims. No product was tested
hands-on. Full links: `05_sources.md`.

## Summary table

| Product | Segment | Capabilities found | AI / natural-language intake found? | Source quality |
|---|---|---|---|---|
| **Planning Center** | Church management (US), modular | People database, Giving, Services (worship planning + volunteer scheduling), Check-ins, Registrations, Calendar (room/resource booking with request + approval groups), Groups, Church Center app | Product page links an "AI" item ("Powerful tools you control") with no detail; nothing about request intake | Verified (vendor product + help pages) |
| **Pushpay / Tithely (incl. Breeze) / Subsplash / Realm** | Church giving + ChMS | Pushpay's own 2026 comparison groups platforms into *unified* (giving + database + app share data) vs *modular* (integrations, more reconciliation) | Pushpay's comparison names no specific AI features for these products; a directory claims a TithelyAI demo — **not verified** | Vendor blog (biased; updated 2026-08-06) |
| **ShulCloud** | Synagogue management | Membership/accounts, online billing & donations, rule-based schedule system, communications, website CMS, lifecycle management | None found | Listings + older press releases |
| **Masjidbox** | Mosque platform | Prayer times, donations with automatic receipts, events with one-tap registration + reminders, branded app, screens, live streaming | None mentioned; no booking feature mentioned | Verified (vendor guide page) |
| **Temple Hub** | Hindu temple management (US, founded 2023) | Puja services & bookings, priest schedules, volunteer management, temple calendar, devotee records, donations/fundraising, facility reservations, iPad front-desk POS, app; listed from **$499/temple/month** (≤500 households) | None mentioned | Listings only (no official site found/fetchable) |
| **Booking Ninjas — Temple** | Temple management on Salesforce | Configurable "religious services and rituals" scheduling/requests/reservations, priests + volunteers with "roles, assignments, availability", donations, facilities | Says Salesforce AI "can be incorporated where licensed and configured" — no temple-specific AI | Verified (vendor page) |
| **3ioNetra** | Temple management (India) | Seva, donations, accounting (Tally), devotee app, hall bookings | None found | Listings (India-only) |
| **SmartPuja / Poojyo** | Consumer priest-booking marketplaces (India; online pujas offered to US/UK/CA/AU) | Pick a puja, pay an advance, priest performs in person (Indian cities) or over Zoom; "multiple language options" | No AI described; priest-assignment method not explained | Verified (SmartPuja page); Poojyo via listing |
| **Teertham** | Priest booking (India) | Human Acharya call to discuss needs, then an "AI booking engine" completes booking | AI for the booking step only; intake is a human call | News article |
| **Kashi Vishwanath temple chatbot** | Single-temple chatbot (India) | Answers questions about darshan/aarti booking process | Information chatbot, not scheduling | News article |

## What this shows (and does not show)

- **Platforms exist for every faith, including Hindu temples.** Temple Hub and Booking Ninjas
  already list priest scheduling, puja bookings, volunteers and donations. SERVE's *platform
  vision* is therefore **not** unique as a feature list — it competes on fit and execution.
- **Booking in these products is form/calendar-based.** The pages we read describe slot
  booking, request forms and approval routing (e.g., Planning Center Calendar approval groups),
  not a system that reads a free-text request and checks priest qualification + language +
  travel + conflicts automatically. **We found no product that does what SERVE's workflow
  demonstrates** — but absence in marketing pages is not proof of absence; this is a
  research-limited claim.
- **Marketplaces (SmartPuja, Poojyo) solve a different problem**: matching a household with any
  priest, mostly in India. They are not temple operations software.
- **AI in this space is mostly information chatbots** (Kashi Vishwanath) or generic platform AI
  (Salesforce, directory claims about Tithely). Teertham uses AI after a human intake call.

## How SERVE's current workflow differs (demonstrated, not claimed)

| Dimension | Typical form/calendar booking (as described by vendors) | SERVE MGT 409 workflow (measured in `evidence/`) |
|---|---|---|
| Input | Member picks a service, date and slot in a form | Member writes a free-text request in their own words (typos, transliterations, "10-ish", "after lunch") |
| Constraint checking | Slot availability; approver judges the rest | Rules engine checks qualification, language, hours, time off, bookings, events, travel radius/fee, buffers, lead time for every option |
| Missing info | Form validation | Intake Agent + code decide what is missing and ask one clarifying question |
| Human control | Approval groups (Planning Center) | Admin approves; approval re-runs all rules in a DB transaction; agents cannot write |
| Transparency | Request record | Evidence per option, agent tool-call trace, tokens and cost per run, audit log |

Positioning sentence: *Temple platforms digitize the booking form; SERVE's demonstrated
contribution is an agentic intake-and-scheduling layer that turns a member's message into
rule-verified, human-approved options.*
