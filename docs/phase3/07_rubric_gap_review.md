# Rubric gap review (100 points) — status after Phase 3

Scores are a self-assessment of evidence readiness, not a prediction of grading.

| Category | Max | Evidence we have | Remaining gaps / risks | Action before submission |
|---|---|---|---|---|
| **Idea — novelty & real-world value** | 21 | Clear problem framing; competitor research with sources; measured constraint complexity; honest two-level differentiation | Value is hypothesis-based (no temple interview); competitors (Temple Hub) cover the platform vision; "no AI intake found" is research-limited | Lead with the agentic workflow, not the platform; cite sources; if possible get even one real temple-office quote (only if genuine) |
| **App — end-to-end functionality** | 15 | Full flow works; 17/17 e2e; persistence; approval/409; admin dashboard; safety flags | Member portal donation/RSVP/volunteer remain demo-only (labelled); no hosted link | Demo only the booking workflow; keep demo labels |
| **App — staff can run it in 10 min** | 5 | `start.sh` verified on a fresh copy (14 s with warm caches) incl. a real AI request; `.env` loading repo → parent; `.env.example`; README | **No GitHub repo yet**; cold install time on another machine unmeasured; needs Python ≥3.10 + Node ≥18; graders need their own key; admin token printed at startup if unset | Create repo, push, clone into an empty dir and time `./start.sh` from scratch; state prerequisites at top of README |
| **App — look & feel** | 10 | Consistent gold/ivory/brown design; screenshots | Admin dashboard dense on small screens (untested on mobile) | Quick mobile check; optional |
| **Report — motivation & differentiation** | 8 | `02_problem_and_differentiation.md`, `01_competitive_landscape.md`, sources | Must keep hypotheses labelled | Use draft text |
| **Report — agents, tools, workflow, diagram, real run** | 10 | Architecture + sequence diagrams; tool table; real-run screenshots; traces | Diagrams are Mermaid (must be rendered inline as SVG in a self-contained HTML) | Render diagrams to inline SVG |
| **Report — tokenomics & measured costs** | 8 | API-reported tokens, cached tokens, cost per run, two configs × two runs, projections | Azure billed rate unknown (disclosed) | Include pricing source and caveat |
| **Report — safety, implemented defenses, real tests** | 8 | 12 attacks off/on × 2 profiles; deterministic tests; model guard | Most attacks resisted by design (must say so); regex screening limits | Present honestly — it is a strength |
| **Report — impact & measurable evidence** | 5 | Reproducible AI vs rules-only comparison; workload metrics; labelled estimates | **No real stakeholder data** — the main weak spot | Don't overclaim; present validation plan |
| **Report — design** | 2 | — | Not written yet | Self-contained HTML, consistent style |
| **Slides — content** | 6 | Outline in `06_final_narrative.md` | Not written | ≤10 slides, GitHub URL |
| **Slides — design** | 2 | — | Not written | |

## Unsupported or risky claims to avoid
- "First/only AI temple platform" → say "we found no product that…" with sources.
- Any time-saved number without the word **estimated**.
- "SERVE supports donations/volunteering/events" as a working capability → roadmap/demo UI.
- Phase 1 latency figures (partly Portkey cache replays) → use Phase 2 numbers only.
- "6 injection attempts flagged" → correct number is **5**.
- Pricing as actual billed cost → "list-price estimate".

## Missing evidence that could cost points
1. GitHub URL (required in report and slides) — repo not created yet.
2. A from-scratch clone timing on a clean environment (current test used warm caches).
3. Any genuine external validation (even one interview) for the Idea/Impact categories.
4. Rendered diagrams and screenshots embedded in self-contained HTML (base64 images).
5. Optional demo video (2–3 min) — not required, but helps App and Idea scoring.

## Housekeeping found during review
- `start.sh` printed port 8000 regardless of `PORT` — fixed (message only).
- Requirements note: README should state Python ≥3.10 and Node ≥18 near the top (already in Quick start).
