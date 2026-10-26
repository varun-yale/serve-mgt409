# Evaluation: probe_cache_bypass

- Run at: 2026-10-25T21:05:05  ·  model requested: `gpt-6-luna`  ·  profile: `default`
- Cases passed (all fields + scheduling correct): **1/1**
- Field accuracy overall: **100.0%**  ·  scheduling correct: **1/1**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 17.07, median 17.07, p90 17.07, max 17.07
- Tokens: input 8,998 (cached 4,167, cache-write 2,361), output 879; model requests 6, tool calls 7
- Cost (list price): total $0.001023, mean per request $0.001023

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
| ✅ C01_griha_telugu_hamden | pending_review | 9/9 | ok | 2 | $0.00102 | 17.07 |  |
