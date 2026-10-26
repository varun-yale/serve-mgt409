# Evaluation: probe_cache_allow_1

- Run at: 2026-10-25T21:04:36  ·  model requested: `gpt-6-luna`  ·  profile: `default`
- Cases passed (all fields + scheduling correct): **1/1**
- Field accuracy overall: **100.0%**  ·  scheduling correct: **1/1**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 2.2, median 2.2, p90 2.2, max 2.2
- Tokens: input 9,035 (cached 3,013, cache-write 3,552), output 876; model requests 6, tool calls 7
- Cost (list price): total $0.001159, mean per request $0.001159

## Field accuracy

| Field | Correct | Total | Accuracy |
|---|---|---|---|
| attendees | 1 | 1 | 100% |
| city | 1 | 1 | 100% |
| dates | 1 | 1 | 100% |
| language | 1 | 1 | 100% |
| location_type | 1 | 1 | 100% |
| service_id | 1 | 1 | 100% |
| special_requirements | 1 | 1 | 100% |
| status | 1 | 1 | 100% |
| time | 1 | 1 | 100% |

## Cases

| Case | Status | Fields | Schedule | Options | Cost | Seconds | Problems |
|---|---|---|---|---|---|---|---|
| ✅ C01_griha_telugu_hamden | pending_review | 9/9 | ok | 2 | $0.00116 | 2.2 |  |
