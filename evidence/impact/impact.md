# Operational impact

## Measured (same scoring for every system)

| System | Main set (27) passed | Main field acc. | Held-out (15) passed | Held-out field acc. | Time per request | Cost per request |
|---|---|---|---|---|---|---|
| Phase 1 agents | 21/27 | 95.9% | not run (code superseded) | — | 13.6s | $0.00088 |
| SERVE v2 agents (optimized) | 26/27 | 99.3% | 14/15 | 98.8% | 10.52s | $0.00056 |
| Rules-only keyword parser | 27/27 (not meaningful*) | 100.0%* | 10/15 | 88.9% | 1.3 ms | $0 |

\* written by the test author after seeing the main-set texts; the held-out set is the fair comparison.

## Estimated (not measured with real staff)

- Each data lookup the agents performed (priest qualifications, languages, calendars, travel, policies, slot checks) is treated as one manual lookup a staff member would do; plus 4.0 min to read the request and write a reply.
- Mean lookups per request (measured from agent traces): 4.81
- Estimated manual staff minutes per request: low 8.8, mid 13.6, high 18.4
- With SERVE: Open request, read evidence, click Approve (1 click) — or Edit & approve (form + check + approve).

## Stakeholder feedback

Not collected. Useful next steps:
- Temple office staff: how long a griha pravesh / satyanarayan request takes today (timed, 5-10 real requests)
- Priests: whether suggested slots respect real preparation/travel realities
- Members: whether the clarifying questions and proposed times are clear (5-question survey)
- Board/treasurer: acceptable cost per request and data-privacy expectations
