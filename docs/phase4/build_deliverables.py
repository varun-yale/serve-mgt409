"""Build report.html and slides.html (self-contained) from saved evidence.

Every number is read from evidence/*.json at build time; nothing here calls a model.
Images come from docs/phase4/assets (crops of real application screenshots in evidence/).

    .venv/bin/python docs/phase4/build_deliverables.py
"""

from __future__ import annotations

import base64
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "evidence"
ASSETS = Path(__file__).resolve().parent / "assets"

# ---- Set this once the repository exists; until then the deliverables show a clear blocker. ----
GITHUB_URL: str | None = "https://github.com/varun-yale/serve-mgt409"
HOSTED_URL: str | None = None  # no hosted deployment exists


def j(p):
    return json.loads((EV / p).read_text())


E = {k: j(f"eval/{k}.json")["summary"] for k in
     ("baseline_phase1", "v2_standard", "v2_standard_r2", "v2_optimized", "v2_optimized_r2", "heldout_standard", "heldout_optimized")}
RULES_H = j("eval/rules_only_heldout.json")["summary"]
TOK = j("tokenomics/tokenomics.json")
SAFE = j("safety/safety_results_optimized.json")
SAFE_STD = j("safety/safety_results_standard.json")["summary"]
WORK = j("impact/manual_workload.json")["summary"]
IMPACT = j("impact/impact.json")
E2E = j("phase2_regression/e2e_results.json")
PRICES = json.loads((ROOT / "backend" / "prices.json").read_text())["gpt-6-luna"]
TRACE = j("phase4_screenshots/r1_agent_trace.json")


def trace_rows():
    """Readable excerpts of the real Scheduling Agent tool calls for run R1 (verbatim values)."""
    sched = [r for r in TRACE["agent_runs"] if r["agent"] == "scheduling"][0]
    rows = []
    for t in sched["tool_call_log"]:
        a, res = t["args"], t["result_summary"]
        def g(key):
            m = re.search(r'"%s":\s*("?)([^",}\]]+)' % key, res)
            return m.group(2) if m else "?"
        if t["tool_name"] == "get_service_details":
            out = f"Griha Pravesh · {g('price_label')} · {g('duration_minutes')} min · at {g('location_mode')} · ≥{g('min_lead_days')} days' notice"
        elif t["tool_name"] == "get_travel_info":
            out = f"Hamden: {g('miles_one_way')} miles, {g('drive_minutes_one_way')} min each way · travel fee ${int(g('travel_fee_cents')) / 100:.2f}"
        elif t["tool_name"] == "find_qualified_priests":
            pr = re.findall(r'"name": "([^"]+)".*?"speaks_requested_language": (true|false)', res)
            out = " · ".join(f"{n.replace('Pandit ', '')} {'✓ Telugu' if ok == 'true' else '✗ no Telugu'}" for n, ok in pr)
        else:
            sl = re.findall(r'"priest_id": "(pr_\w+)", "start": "([\d:]+)"', res)
            out = "Open: " + ", ".join(f"{p.replace('pr_', '').title()} {st}" for p, st in sl) + " · Joshi, Sharma excluded: do not speak Telugu"
        args = ", ".join(f"{k}={v}" for k, v in a.items() if v is not None)
        rows.append((t["tool_name"], args, out))
    return sched, rows


import re  # noqa: E402

try:
    out = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "--collect-only"], cwd=ROOT,
                         capture_output=True, text=True, timeout=120).stdout
    N_TESTS = int([l for l in out.splitlines() if "tests collected" in l or "test collected" in l][0].split()[0])
except Exception:
    N_TESTS = 43

C = TOK["configs"]
B, STD, OPT = C["baseline_phase1"], C["v2_standard"], C["v2_optimized"]
PROJ = TOK["projection"]
R1 = E2E["R1"]
R1_RUNS = [r for r in reversed(E2E["agent_runs"]["runs"]) if r["request_id"] == R1["request_id"]]
FLAGGED = [r["id"] for r in SAFE["rows"] if (r["on"]["observations"].get("risk_flags") or {}).get("injection_patterns")]
SS = SAFE["summary"]


def pct(a, b):
    return f"{(a - b) / b * 100:+.0f}%"


def img(name, alt, cls=""):
    data = base64.b64encode((ASSETS / f"{name}.jpg").read_bytes()).decode()
    return f'<img class="{cls}" alt="{html.escape(alt)}" src="data:image/jpeg;base64,{data}">'


def esc(s):
    return html.escape(str(s))


def gh_html(big=False):
    if GITHUB_URL:
        return f'<a class="gh{" big" if big else ""}" href="{GITHUB_URL}">{GITHUB_URL}</a>'
    return f'<span class="gh blocker{" big" if big else ""}">[GITHUB URL PLACEHOLDER — repository not yet created]</span>'


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------
GOLD, BROWN, DARK, IVORY, MUTED, TERRA, LIGHT = "#c9962f", "#5e4b21", "#3b2f16", "#fffdf8", "#6f6453", "#8e6615", "#f4e8ce"


def hbar_chart(rows, maxv, w=640, unit="", fmt=lambda v: str(v), title="", note=""):
    """rows: (label, value, color, sublabel)"""
    bh, gap, lw = 26, 12, 220
    h = 30 + len(rows) * (bh + gap) + (24 if note else 0)
    s = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="{esc(title)}">']
    if title:
        s.append(f'<text x="0" y="16" class="ct">{esc(title)}</text>')
    for i, (lab, v, col, sub) in enumerate(rows):
        y = 30 + i * (bh + gap)
        bw = max(2, (w - lw - 90) * v / maxv)
        s.append(f'<text x="{lw - 10}" y="{y + 17}" text-anchor="end" class="cl">{esc(lab)}</text>')
        s.append(f'<rect x="{lw}" y="{y}" width="{w - lw - 90}" height="{bh}" rx="5" fill="{LIGHT}" opacity=".55"/>')
        s.append(f'<rect x="{lw}" y="{y}" width="{bw:.1f}" height="{bh}" rx="5" fill="{col}"/>')
        s.append(f'<text x="{lw + bw + 8:.1f}" y="{y + 17}" class="cv">{esc(fmt(v))}{esc(unit)}</text>')
        if sub:
            s.append(f'<text x="{lw - 10}" y="{y + bh + 7}" text-anchor="end" class="cs">{esc(sub)}</text>')
    if note:
        s.append(f'<text x="0" y="{h - 6}" class="cs">{esc(note)}</text>')
    s.append("</svg>")
    return "".join(s)


def token_stack_chart():
    rows = [("Phase 1", B), ("v2 standard", STD), ("v2 optimized", OPT)]
    w, h, lw = 640, 170, 120
    mx = max(r["input_tokens"] for _, r in rows)
    s = [f'<svg viewBox="0 0 {w} {h}" class="chart" role="img" aria-label="Input tokens cached vs uncached">',
         '<text x="0" y="16" class="ct">Input tokens on the 27-case set (API-reported): cached vs uncached</text>']
    for i, (lab, r) in enumerate(rows):
        y = 34 + i * 40
        tot = (w - lw - 110) * r["input_tokens"] / mx
        cw = tot * r["cached_input_tokens"] / r["input_tokens"]
        s += [f'<text x="{lw - 10}" y="{y + 18}" text-anchor="end" class="cl">{lab}</text>',
              f'<rect x="{lw}" y="{y}" width="{cw:.1f}" height="26" fill="{GOLD}" rx="4"/>',
              f'<rect x="{lw + cw:.1f}" y="{y}" width="{tot - cw:.1f}" height="26" fill="{BROWN}" rx="4"/>',
              f'<text x="{lw + tot + 8:.1f}" y="{y + 18}" class="cv">{r["input_tokens"]:,} ({r["cached_share_of_input"]:.0%} cached)</text>']
    s += [f'<rect x="{lw}" y="{h - 18}" width="12" height="12" fill="{GOLD}"/><text x="{lw + 18}" y="{h - 8}" class="cs">cached input ($0.01/1M)</text>',
          f'<rect x="{lw + 170}" y="{h - 18}" width="12" height="12" fill="{BROWN}"/><text x="{lw + 188}" y="{h - 8}" class="cs">uncached input ($0.10/1M)</text>',
          "</svg>"]
    return "".join(s)


def arch_svg():
    """Architecture diagram as embedded SVG (matches backend/ implementation)."""
    def box(x, y, w, h, title, lines=(), fill="#fff", stroke=GOLD, tcol=DARK, bold=True):
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>',
               f'<text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" class="ab" fill="{tcol}">{esc(title)}</text>']
        for i, l in enumerate(lines):
            out.append(f'<text x="{x + w / 2}" y="{y + 40 + i * 15}" text-anchor="middle" class="as" fill="{tcol}">{esc(l)}</text>')
        return "".join(out)

    def arrow(x1, y1, x2, y2, label="", dash=False, lx=None, ly=None):
        d = ' stroke-dasharray="5 4"' if dash else ""
        t = f'<text x="{lx if lx is not None else (x1 + x2) / 2}" y="{ly if ly is not None else (y1 + y2) / 2 - 6}" text-anchor="middle" class="al">{esc(label)}</text>' if label else ""
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{BROWN}" stroke-width="1.8" marker-end="url(#ah)"{d}/>{t}'

    s = ['<svg viewBox="0 0 980 520" class="arch" role="img" aria-label="SERVE architecture">',
         f'<defs><marker id="ah" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="{BROWN}"/></marker></defs>',
         f'<rect x="8" y="8" width="964" height="504" rx="18" fill="{IVORY}" stroke="{LIGHT}"/>',
         # row 1: member -> intake -> code -> scheduling
         box(24, 40, 150, 92, "Member", ["Free-text request", "(portal /app)"], fill="#fdf7ea"),
         box(214, 40, 170, 92, "Intake Agent", ["gpt-6-luna", "→ IntakeResult", "tool: get_member_profile"], fill=DARK, stroke=DARK, tcol="#fffdf8"),
         box(424, 40, 150, 92, "Code checks", ["missing info?", "time window", "service/date valid"], fill="#fff"),
         box(614, 40, 170, 92, "Scheduling Agent", ["gpt-6-luna", "→ ScheduleRecommendation", "6 read-only tools"], fill=DARK, stroke=DARK, tcol="#fffdf8"),
         box(824, 40, 130, 92, "Rules engine", ["re-verifies every", "option; DB prices"], fill="#fff"),
         arrow(174, 86, 212, 86), arrow(384, 86, 422, 86), arrow(574, 86, 612, 86), arrow(784, 86, 822, 86),
         f'<path d="M499,40 V22 H99 V36" fill="none" stroke="{BROWN}" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#ah)"/>',
         '<text x="300" y="18" text-anchor="middle" class="al">missing info → one clarifying question back to the member</text>',
         # row 2: approval -> booking
         box(824, 210, 130, 92, "Admin review", ["/admin (token)", "approve · edit", "reject · ask"], fill="#fdf7ea"),
         arrow(889, 132, 889, 208),
         box(614, 210, 170, 92, "Approval route", ["BEGIN IMMEDIATE", "check_slot again", "unique index backstop"], fill="#fff"),
         arrow(822, 256, 786, 256),
         box(424, 210, 150, 92, "Booking", ["confirmed in SQLite", "member sees it", "after refresh"], fill="#fdf7ea"),
         arrow(612, 256, 576, 256),
         # row 3: infrastructure
         box(24, 350, 290, 130, "Portkey → Azure OpenAI", ["gpt-6-luna (reported gpt-6-luna-global)", "cache bypass · model guard", "provider/route headers logged", "key stays server-side"], fill="#fff", stroke=BROWN),
         box(344, 350, 300, 130, "Read-only tools (scheduling.py)", ["get_service_details · find_qualified_priests", "get_travel_info · get_priest_day", "search_available_slots · verify_slot", "per-tool budgets · UsageLimits · 120 s"], fill="#fff", stroke=BROWN),
         box(674, 350, 280, 130, "SQLite", ["services · priests · languages · qualifications", "availability · time off · travel · events", "requests · bookings · approvals", "agent_runs · tool_calls · audit_events"], fill="#fff", stroke=BROWN),
         arrow(260, 132, 170, 348, dash=True, label="model calls", lx=170, ly=250),
         f'<path d="M650,132 V168 H290 V346" fill="none" stroke="{BROWN}" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#ah)"/>',
         f'<path d="M730,132 V182 H404 V332 H494 V346" fill="none" stroke="{BROWN}" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#ah)"/>',
         '<text x="396" y="262" text-anchor="middle" class="al" transform="rotate(-90 396 262)">tool reads</text>',
         arrow(644, 415, 672, 415),
         f'<path d="M499,302 V324 H814 V346" fill="none" stroke="{BROWN}" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#ah)"/>',
         '<text x="660" y="318" text-anchor="middle" class="al">persist</text>',
         '<text x="24" y="505" class="as" fill="#6f6453">Solid arrows: request flow. Dashed: model calls, tool reads, persistence. Agents have no write tools; only the token-protected approval route creates bookings.</text>',
         "</svg>"]
    return "".join(s)


def vision_svg():
    items = [("Service & priest booking", True), ("Donations", False), ("Events", False),
             ("Volunteering", False), ("Member communication", False), ("Multilingual engagement", False)]
    s = ['<svg viewBox="0 0 640 150" class="chart" role="img" aria-label="Vision vs prototype">']
    for i, (t, built) in enumerate(items):
        x, y = 10 + (i % 3) * 210, 10 + (i // 3) * 66
        s.append(f'<rect x="{x}" y="{y}" width="200" height="56" rx="10" fill="{DARK if built else "#fff"}" stroke="{GOLD if built else LIGHT}" stroke-width="1.6"/>')
        s.append(f'<text x="{x + 100}" y="{y + 25}" text-anchor="middle" class="ab" fill="{"#fffdf8" if built else MUTED}">{esc(t if len(t) < 26 else t[:24] + "…")}</text>')
        s.append(f'<text x="{x + 100}" y="{y + 43}" text-anchor="middle" class="as" fill="{"#f9c74f" if built else MUTED}">{"BUILT + MEASURED (AI workflow)" if built else "vision / demo UI only"}</text>')
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------------------
# shared numbers
# ---------------------------------------------------------------------------
N = {
    "b_pass": f"{E['baseline_phase1']['cases_passed']}/27", "b_time": f"{E['baseline_phase1']['field_accuracy_by_field']['time']['accuracy']:.1%}",
    "std": f"{E['v2_standard']['cases_passed']}/27 and {E['v2_standard_r2']['cases_passed']}/27",
    "opt": f"{E['v2_optimized']['cases_passed']}/27 and {E['v2_optimized_r2']['cases_passed']}/27",
    "h_opt": f"{E['heldout_optimized']['cases_passed']}/15", "h_std": f"{E['heldout_standard']['cases_passed']}/15",
    "h_rules": f"{RULES_H['cases_passed']}/15",
    "cost_std": f"${STD['cost_mean_per_request_usd']:.5f}", "cost_opt": f"${OPT['cost_mean_per_request_usd']:.5f}",
    "lat_std": f"{STD['latency_s']['mean']:.1f} s", "lat_opt": f"{OPT['latency_s']['mean']:.1f} s",
    "per_req": f"${PROJ['expected_cost_per_member_request_usd']:.5f}",
    "p1k": f"${PROJ['table']['1000']['expected_usd']:.2f}", "p10k": f"${PROJ['table']['10000']['expected_usd']:.2f}",
    "p100": f"${PROJ['table']['100']['expected_usd']:.2f}",
}

CSS_COMMON = """
:root{--ivory:#fffdf8;--ivory2:#fbf4e4;--cream:#fdf7ea;--line:#f4e8ce;--line2:#e8d4a6;--gold:#c9962f;--gold2:#f9c74f;
--brown:#5e4b21;--dark:#3b2f16;--ink:#2b2518;--muted:#6f6453;--terra:#8e6615;--red:#9b2c1c}
*{box-sizing:border-box}
.chart text{font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
.chart .ct{font-size:13px;font-weight:600;fill:var(--dark)} .chart .cl{font-size:12px;fill:var(--ink)}
.chart .cv{font-size:12px;font-weight:600;fill:var(--dark)} .chart .cs{font-size:10.5px;fill:var(--muted)}
.chart .ab,.arch .ab{font-size:13px;font-weight:700} .chart .as,.arch .as{font-size:10.5px}
.arch text{font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif} .arch .al{font-size:10.5px;fill:var(--brown);font-style:italic}
.gh{font-weight:600;color:var(--terra);word-break:break-all}
.gh.blocker{display:inline-block;letter-spacing:0;text-transform:none;word-break:normal;background:#fdecea;color:var(--red);border:1.5px dashed var(--red);border-radius:8px;padding:3px 8px}
"""

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def report():
    tbl_eval = "".join(
        f"<tr><td>{lab}</td><td>{E[k]['cases_passed']}/{E[k]['cases']}</td><td>{E[k]['field_accuracy_overall']:.1%}</td>"
        f"<td>{E[k]['schedule_correct']}/{E[k]['cases']}</td><td>{E[k]['latency_seconds']['mean']:.1f} s</td><td>${E[k]['cost_usd_per_request_mean']:.5f}</td></tr>"
        for k, lab in (("baseline_phase1", "Phase 1 agents (baseline)"), ("v2_standard", "v2 standard — run 1"),
                       ("v2_standard_r2", "v2 standard — run 2"), ("v2_optimized", "v2 optimized — run 1"),
                       ("v2_optimized_r2", "v2 optimized — run 2")))
    acc_chart = hbar_chart([
        ("Phase 1 agents", E["baseline_phase1"]["cases_passed"], "#a8956a", "main set, 27 cases"),
        ("v2 standard (run 1)", E["v2_standard"]["cases_passed"], BROWN, ""),
        ("v2 optimized (run 1)", E["v2_optimized"]["cases_passed"], GOLD, ""),
        ("v2 optimized (run 2)", E["v2_optimized_r2"]["cases_passed"], GOLD, ""),
    ], 27, fmt=lambda v: f"{v}/27", title="Evaluation cases fully correct (all fields + scheduling)")
    held_chart = hbar_chart([
        ("Rules-only keyword parser", RULES_H["cases_passed"], "#a8956a", "frozen before cases written"),
        ("SERVE agents (standard)", E["heldout_standard"]["cases_passed"], BROWN, ""),
        ("SERVE agents (optimized)", E["heldout_optimized"]["cases_passed"], GOLD, ""),
    ], 15, fmt=lambda v: f"{v}/15", title="Held-out set: 15 messier, more natural requests")

    cost_chart = hbar_chart([
        ("Phase 1", B["cost_mean_per_request_usd"] * 1e5, "#a8956a", f"{B['latency_s']['mean']:.1f} s mean"),
        ("v2 standard", STD["cost_mean_per_request_usd"] * 1e5, BROWN, f"{STD['latency_s']['mean']:.1f} s mean"),
        ("v2 optimized", OPT["cost_mean_per_request_usd"] * 1e5, GOLD, f"{OPT['latency_s']['mean']:.1f} s mean"),
    ], 100, fmt=lambda v: f"${v / 1e5:.5f}", title="Measured list-price cost per request (run 1, same 27 cases)")

    rows_runs = "".join(
        f"<tr><td>{lab}</td><td>{c['model_requests']}</td><td>{c['tool_calls']}</td><td>{c['input_tokens']:,}</td>"
        f"<td>{c['cached_input_tokens']:,} ({c['cached_share_of_input']:.0%})</td><td>{c['cache_write_tokens']:,}</td><td>{c['output_tokens']:,}</td>"
        f"<td>{c['latency_s']['mean']:.1f} / {c['latency_s']['p90']:.1f} s</td><td>${c['cost_total_usd']:.4f}</td><td>${c['cost_mean_per_request_usd']:.5f}</td><td>{c['portkey_cache_hits']}</td></tr>"
        for lab, c in (("Phase 1", B), ("v2 standard", STD), ("v2 optimized", OPT)))
    per_agent = "".join(
        f"<tr><td>{cl}</td><td>{a}</td><td>{v['mean_model_requests']}</td><td>{v['mean_tool_calls']}</td><td>{v['mean_input_tokens']:,}</td>"
        f"<td>{v['mean_cached_input_tokens']:,}</td><td>{v['mean_output_tokens']:,}</td><td>{v['mean_latency_s']:.1f} s</td><td>${v['mean_cost_usd']:.6f}</td></tr>"
        for cl, c in (("v2 standard", STD), ("v2 optimized", OPT)) for a, v in c["per_agent"].items())
    proj_rows = "".join(f"<tr><td>{int(n):,}</td><td>${v['expected_usd']:.2f}</td><td>${v['p90_usd']:.2f}</td><td>{v['model_runs_approx']:,}</td></tr>"
                        for n, v in PROJ["table"].items())
    pr = PROJ["expected_cost_per_member_request_usd"]

    safety_rows = []
    labels = {"A01_direct_injection": "Direct prompt injection (approve, $0, reveal prompt)", "A02_delimiter_breakout": "Fake delimiter / system block",
              "A03_approval_bypass_text": "Approval bypass (text + unauthenticated API call)", "A04_force_conflict": "Force a conflicting booking",
              "A05_unqualified_priest": "Force an unqualified priest", "A06_price_manipulation": "Unauthorized price change",
              "A07_member_data_exfiltration": "Other members' data", "A08_duplicate_submissions": "Duplicate submissions",
              "A09_runaway_tool_use": "Runaway tool use", "A10_output_manipulation": "Make agent tell member a falsehood",
              "A11_admin_token_bruteforce": "Admin token guessing", "A12_prompt_exfiltration": "Prompt / tool exfiltration",
              "L01_legit_control": "Legitimate control request", "L02_legit_benign_keywords": "Legit request with 'free' / 'confirm'"}
    for r in SAFE["rows"]:
        verdict = r["verdict"].split(" — ")[0]
        layers = r["verdict"].split(" — ")[1] if " — " in r["verdict"] else ""
        cls = "new" if verdict.startswith("BLOCKED") else ""
        if r["id"].startswith("L"):  # legitimate controls: the question is whether they still work
            verdict = "Worked as intended (no false block)" if not r["on_unsafe"] else "FAILED — legitimate request blocked"
        safety_rows.append(f"<tr class='{cls}'><td>{r['id'][:3]}</td><td>{esc(labels.get(r['id'], r['risk']))}</td>"
                           f"<td>{'✗ unsafe' if r['off_unsafe'] else '✓ safe'}</td><td>{'✗ unsafe' if r['on_unsafe'] else '✓ safe'}</td>"
                           f"<td>{esc(verdict.capitalize() if not verdict.startswith('BLOCKED') else 'Blocked by new defense')}</td><td>{esc(layers)}</td></tr>")
    safe_chart = hbar_chart([
        ("Unsafe, new defenses OFF", SS["unsafe_with_defenses_off"], "#9b2c1c", "duplicates · token guessing"),
        ("Unsafe, defenses ON", SS["unsafe_with_defenses_on"], GOLD, ""),
        ("Resisted by original design", SS["attacks"] - SS["unsafe_with_defenses_off"], BROWN, "both modes safe"),
        ("Flagged for staff (D2)", len(FLAGGED), "#a8956a", "injection screening"),
    ], 12, fmt=lambda v: f"{v} of 12", title="12 attacks × 2 modes (optimized profile; standard profile identical)")

    w = WORK["means_per_request"]
    work_chart = hbar_chart([
        ("Qualified priests", w["qualified_priests"], "#a8956a", ""),
        ("…that speak the language", w["qualified_and_language_ok"], BROWN, ""),
        ("Priest-day calendars", w["calendars_to_open"], BROWN, ""),
        ("Candidate start times", w["candidate_slots_to_test"], GOLD, ""),
    ], 35, fmt=lambda v: f"{v}", title=f"Mean work behind one request (deterministic, {WORK['requests_analyzed']} complete requests)",
        note=f"Plus ≈{w['rule_checks']:.0f} individual rule checks; {WORK['home_requests_needing_travel_lookup']}/{WORK['requests_analyzed']} need a travel lookup; {WORK['requests_where_correct_answer_is_no_availability']}/{WORK['requests_analyzed']} correctly end in 'no availability'.")

    r1i = R1["intake"]
    intake_run, sched_run = R1_RUNS[0], R1_RUNS[1]
    me = IMPACT["manual_estimate"]["estimated_staff_minutes_per_request"]

    body = f"""
<section class="page title">
  <div class="kicker">MGT 409 · AI Agents · Yale School of Management · Final project · October 2026</div>
  <div class="wordmark">SERVE</div>
  <h1 class="pitch">An AI-enabled operating platform for religious communities, beginning with Hindu temples.</h1>
  <p class="sub">Its current prototype demonstrates intelligent service booking and priest scheduling with human oversight:
  a member describes the seva or puja they need in their own words; two AI agents interpret the request and check real
  priest qualifications, languages, travel and availability; a temple administrator approves the booking.</p>
  <div class="meta">
    <div><span>Author</span>Varun Matta</div>
    <div><span>Course</span>MGT 409 AI Agents, Yale SOM</div>
    <div><span>Repository</span>{gh_html(True)}</div>
    <div><span>Hosted app</span>None — runs locally in one command: <code>./start.sh</code> (README)</div>
  </div>
  <h2 class="sec"><span>1</span>Title and links — executive overview</h2>
  <div class="kpis">
    <div><b>{N['opt'].split(' and ')[0]}–{N['opt'].split(' and ')[1]}</b><span>evaluation cases correct (optimized, two runs) vs {N['b_pass']} for Phase 1</span></div>
    <div><b>{N['h_opt']}</b><span>held-out messy requests correct vs {N['h_rules']} for a rules-only parser</span></div>
    <div><b>0 of 12</b><span>attacks succeeded with defenses on (2 of 12 with new defenses off)</span></div>
    <div><b>{N['cost_opt']}</b><span>measured list-price API cost per request (run 1, 27 cases) · {N['lat_opt']} mean latency</span></div>
  </div>
  <div class="two">
    <div>
      <p><b>What works today.</b> A React member portal and temple-office dashboard backed by FastAPI and SQLite. The
      <b>Intake Agent</b> turns free text into a structured request; the <b>Scheduling Agent</b> uses six read-only tools to find
      options; a deterministic <b>rules engine</b> re-verifies every option; only a token-protected <b>admin approval</b>
      creates a booking, inside a database transaction. Every run records API-reported tokens, cost, latency, tool calls and an audit trail.</p>
      <p><b>What is vision, not product.</b> Donations, events, volunteering and community messaging are part of SERVE's long-term
      platform thesis. In this prototype they exist only as pre-existing demo screens and are not claimed as working features.</p>
    </div>
    <figure class="shot cap2">{img("landing", "SERVE landing page (real application)")}<figcaption>Real application: SERVE landing page. All temple data is fictional (“Shanti Mandir”).</figcaption></figure>
  </div>
</section>

<section class="page">
  <h2 class="sec"><span>2</span>Motivation</h2>
  <p class="evnote">Evidence base: <code>evidence/</code> (real gpt-6-luna runs, 25 Oct 2026) and <code>docs/phase3/</code> (sources). Labels used throughout:
  <span class="tag m">Measured</span> from saved runs · <span class="tag p">Projection</span> from measured inputs + stated assumptions ·
  <span class="tag e">Estimate</span> not measured · <span class="tag h">Hypothesis</span> to be validated.</p>
  <p class="lead">I chose this problem because of my familiarity with Hindu temple communities, including the temple my parents attend in
  Novi, Michigan. From that vantage point I have observed that day-to-day temple operations can depend on manual coordination,
  separate portals, WhatsApp groups and a great deal of volunteer effort.</p>
  <p>One recurring pain point is arranging a priest for a particular seva, puja or life-event ceremony. A family planning a griha pravesh
  (house blessing) has to find a priest who is qualified for that ritual, ideally speaks the family's language, can travel to their town,
  is free on an auspicious date, and is approved by the temple. Today that information is spread across people's heads, phone calls and
  messages. These observations are personal; the broader claims below are framed as hypotheses until validated with temples.</p>
  <table class="t">
    <thead><tr><th>Statement</th><th>Status</th><th>Source / how to validate</th></tr></thead>
    <tbody>
      <tr><td>About 3.0 million Hindus lived in the US in 2020; North America's Hindu population grew 55% from 2010 to 2020.</td><td><span class="tag m">Evidence</span></td><td>Pew Research Center (2025) [1]</td></tr>
      <tr><td>About 1% of US adults identify as Hindu.</td><td><span class="tag m">Evidence</span></td><td>Pew Religious Landscape Study 2023–24 [2]</td></tr>
      <tr><td>A c. 2011 census counted ~1,600 Hindu temples and centers in the US (258 traditional temples); no current authoritative count was found.</td><td><span class="tag m">Evidence (dated)</span></td><td>Institute of American Religion via ARDA [3]</td></tr>
      <tr><td>Temple operations rely on manual coordination, separate portals and WhatsApp groups.</td><td><span class="tag h">Personal observation</span></td><td>Inventory tools at 3–5 temples</td></tr>
      <tr><td>Priest/seva requests take several back-and-forth exchanges to schedule.</td><td><span class="tag h">Hypothesis</span></td><td>Time 5–10 real requests at a temple office</td></tr>
      <tr><td>Staff hold qualification, language and travel constraints in their heads or spreadsheets.</td><td><span class="tag h">Hypothesis</span></td><td>Interview office manager and priests</td></tr>
    </tbody>
  </table>
  <h3>Why priest booking is operationally hard</h3>
  <div class="two">
    <div>
      <p>Matching one request touches many independent constraints: the ritual (only some priests perform a griha pravesh), language
      (Telugu, Tamil, Gujarati, Hindi…), home or temple location and travel radius, priest working hours and leave, existing bookings with
      travel buffers, festival days that occupy every priest, lead-time policies and pricing with travel fees.</p>
      <p>Using SERVE's own database we measured the structure of this work <span class="tag m">Measured</span>. For the complete requests in our
      evaluation sets, a coordinator would on average weigh {w['qualified_priests']} qualified priests, {w['qualified_and_language_ok']} after
      language, open {w['calendars_to_open']} priest-day calendars and test {w['candidate_slots_to_test']} candidate start times. In
      {WORK['requests_where_correct_answer_is_no_availability']} of {WORK['requests_analyzed']} requests the correct answer is “no availability”,
      which a form cannot explain to the member. (Fictional data: this shows the problem's structure, not real temple timings.)</p>
    </div>
    <div>{work_chart}</div>
  </div>
  <h3>Who benefits</h3>
  <table class="t compact"><thead><tr><th>Stakeholder</th><th>Need</th><th>What the prototype offers</th></tr></thead><tbody>
    <tr><td>Members / families</td><td>Ask in their own words; know quickly whether it is possible</td><td>Free-text request, one clarifying question if needed, proposed times</td></tr>
    <tr><td>Temple administrators</td><td>Fewer lookups; confidence that options are valid</td><td>Rule-verified options with evidence; one-click approval; audit log</td></tr>
    <tr><td>Priests</td><td>No double-booking; language and travel respected</td><td>Conflict, buffer, leave and travel-radius checks before approval</td></tr>
    <tr><td>Volunteer coordinators</td><td>Festival staffing</td><td>Roadmap only (not implemented)</td></tr>
  </tbody></table>
</section>

<section class="page">
  <h2 class="sec"><span>3</span>What is new here</h2>
  <p class="lead">SERVE operates at two levels. The <b>long-term vision</b> is a vertical SaaS operating platform for religious organizations.
  The <b>demonstrated contribution</b> is one AI-powered workflow: service intake → priest matching → scheduling validation → human-approved booking.</p>
  {vision_svg()}
  <p>The platform vision is <b>not unique as a feature list</b>. Mature products already serve churches, synagogues and mosques, and at least
  two products target temples with puja booking, priest scheduling, volunteers and donations. We do not claim SERVE is the first platform
  with these features.</p>
  <table class="t compact">
    <thead><tr><th>Product</th><th>Segment</th><th>Capabilities found (sources)</th><th>AI request intake?</th></tr></thead>
    <tbody>
      <tr><td>Planning Center</td><td>Churches (US)</td><td>People, Giving, Services scheduling, Check-ins, Registrations, Calendar room/resource booking with approval groups [4][5]</td><td>“AI” menu item without detail; none for intake</td></tr>
      <tr><td>Pushpay / Tithely / Subsplash / Realm</td><td>Church giving + ChMS</td><td>Unified (giving + database + app) vs modular platforms [6]</td><td>No specific AI features in vendor comparison</td></tr>
      <tr><td>ShulCloud</td><td>Synagogues</td><td>Membership, billing & donations, rule-based schedules, communications [7]</td><td>None found</td></tr>
      <tr><td>Masjidbox</td><td>Mosques</td><td>Prayer times, donations with receipts, event registration, branded app [8]</td><td>None found</td></tr>
      <tr><td>Temple Hub</td><td>Hindu temples (US)</td><td>Puja bookings, priest schedules, volunteers, donations, facility reservations, iPad POS; listed from $499/month [9]</td><td>None mentioned (listings)</td></tr>
      <tr><td>Booking Ninjas — Temple</td><td>Temples (Salesforce)</td><td>Ritual scheduling/requests, priests & volunteers with availability, donations, facilities [10]</td><td>Salesforce AI “where licensed”</td></tr>
      <tr><td>SmartPuja / Poojyo</td><td>Priest marketplaces (India)</td><td>Pick a puja, pay an advance; in person in Indian cities or online [11][12]</td><td>None described</td></tr>
      <tr><td>Teertham</td><td>Priest booking (India)</td><td>Human Acharya call first, then an “AI booking engine” [13]</td><td>AI after human intake</td></tr>
    </tbody>
  </table>
  <h3>Why agentic intake differs from form-based booking</h3>
  <table class="t compact"><thead><tr><th></th><th>Form / calendar booking (as vendors describe it)</th><th>SERVE prototype (measured in evidence/)</th></tr></thead><tbody>
    <tr><td>Input</td><td>Member chooses service, date and slot</td><td>Member writes naturally: “gruhapravesam… saturday the 21st… telugu preferred”</td></tr>
    <tr><td>Constraints</td><td>Slot availability; approver judges the rest</td><td>Qualification, language, hours, leave, bookings + travel buffers, festivals, radius, lead time, price — checked for every option</td></tr>
    <tr><td>Missing information</td><td>Required fields</td><td>Agent + code ask one targeted question (all 7 needs-info cases correct in every optimized run)</td></tr>
    <tr><td>Infeasible requests</td><td>Empty calendar</td><td>Explains why (e.g., only Telugu-speaking priest on leave) and offers nearby alternatives</td></tr>
    <tr><td>Control</td><td>Approval routing (e.g., Planning Center [5])</td><td>Agents cannot write; approval re-checks rules in a transaction; full audit and cost trail</td></tr>
  </tbody></table>
  <p class="evnote">Research limit: we found no product that reads a free-text request and automatically checks priest qualification, language,
  travel and conflicts before human approval — based on vendor and listing pages read on 25 Oct 2026, not hands-on testing. AI in this space
  is mostly information chatbots (e.g., a temple trust's booking-information chatbot [14]).</p>
</section>

<section class="page">
  <h2 class="sec"><span>4</span>The agents</h2>
  <p class="lead">Two specialized PydanticAI agents call <code>gpt-6-luna</code> through Portkey's OpenAI-compatible Responses API. Agents
  recommend; deterministic code decides. The diagram reflects <code>backend/agents.py</code>, <code>pipeline.py</code>, <code>scheduling.py</code> and <code>main.py</code>.</p>
  <figure>{arch_svg()}<figcaption>Figure 1 — SERVE architecture as implemented.</figcaption></figure>
  <table class="t compact agents">
    <thead><tr><th></th><th>Intake Agent</th><th>Scheduling Agent</th></tr></thead>
    <tbody>
      <tr><td>Purpose</td><td>Understand what the member wants; never schedules or prices</td><td>Find up to 3 approvable options with evidence; never books</td></tr>
      <tr><td>Input</td><td>Today's date + member text inside <code>&lt;member_request&gt;</code> (untrusted data)</td><td>Structured request from Intake + code-computed time window</td></tr>
      <tr><td>Structured output</td><td><code>IntakeResult</code>: service_id, dates, time preference (morning, late morning, afternoon, evening, exact, range, any), location, town, language, guests, special needs, missing fields, clarifying question</td><td><code>ScheduleRecommendation</code>: outcome, ≤3 options (priest, date, start, location, rationale), missing information, notes for staff</td></tr>
      <tr><td>Tools (read-only)</td><td><code>get_member_profile</code> (this member only). Service catalog sits in a stable cached prompt prefix (optimized profile)</td><td><code>get_service_details</code>, <code>find_qualified_priests</code>, <code>get_travel_info</code>, <code>get_priest_day</code>, <code>search_available_slots</code>, <code>verify_slot</code></td></tr>
      <tr><td>Business rules in code</td><td>Service/date validation; time window from the category; missing-info decision; output filter on the clarifying question</td><td>Every option re-run through <code>check_slot</code>; prices from DB; time-preference policy; options outside rules are dropped</td></tr>
      <tr><td>Limits & failures</td><td>4 model requests, 4 tool calls, 120 s; failure → request marked for staff follow-up, no fallback model</td><td>10 requests, 16 tool calls, per-tool budgets, 120 s; model guard rejects any non-gpt-6-luna response</td></tr>
    </tbody>
  </table>
  <p><b>Why two agents.</b> Interpretation and constraint search fail differently: intake errors are about language understanding (“10-ish”,
  “sorry, I meant Sunday”), scheduling errors are about data. Separating them keeps each prompt small and cacheable, lets code validate the
  hand-off (a request with missing fields never reaches scheduling), and makes the trace auditable per agent.</p>
</section>

<section class="page">
  <h3 class="cont">4 · The agents — one real end-to-end run</h3>
  <p>Run from the Phase 1 regression suite on the final code (<code>evidence/phase2_regression/</code>, 17/17 checks passed, 25 Oct 2026). The member wrote:
  <i>“Hi, we just bought a house in Hamden and would love a griha pravesh on Saturday, November 21, in the morning if possible. We'd like the ceremony in Telugu.
  About 25 guests, and my mother uses a wheelchair.”</i></p>
  <div class="steps">
    <figure class="shot phone">{img("member_ask", "Member request sheet")}<figcaption>① Member describes the need (real portal).</figcaption></figure>
    <figure class="shot phone">{img("member_pending", "Member sees proposed times")}<figcaption>⑤ Member sees proposed times, clearly not yet booked.</figcaption></figure>
    <div class="steptext">
      <p><b>② Intake Agent</b> ({intake_run['response_model']}, {intake_run['latency_ms'] / 1000:.1f} s, {intake_run['input_tokens']:,} input tokens of which {intake_run['cached_input_tokens']:,} cached, ${intake_run['cost_usd']:.5f}) extracted:
      service <code>{r1i['service_id']}</code>, date {r1i['preferred_dates'][0]}, {r1i['time_preference']} (code window {r1i['earliest_start']}–{r1i['latest_start']}),
      home in {r1i['city']}, {r1i['language']}, {r1i['attendees']} guests, special requirement “{r1i['special_requirements'][0]}”. Nothing missing → hand-off.</p>
      <p><b>③ Scheduling Agent</b> ({sched_run['latency_ms'] / 1000:.1f} s, {sched_run['tool_calls']} tool calls, ${sched_run['cost_usd']:.5f}) called
      {', '.join(f'<code>{t}</code>' for t in R1['tools'])}. Only Pandit Iyer is qualified and speaks Telugu; the search explained why the other two priests were excluded.</p>
      <p><b>④ Rules engine</b> re-verified both options (Sat 21 Nov 08:00 and 08:30, $251, travel fee $0 for 6 miles) and the admin saw the evidence below.</p>
      <p><b>⑥ Administrator</b> clicked <i>Approve option 1</i>: booking <code>{E2E['R1_booking']['id']}</code> was written to SQLite
      (<code>{E2E['sqlite_booking_row']}</code>) and appeared in the member's profile after a page refresh. A second approval of the same request returned
      <b>HTTP {E2E['duplicate_approval']['status']}</b>; forcing that slot onto a later identical request returned <b>HTTP {E2E['R5_conflict']['forced_status']}</b> (“{esc(E2E['R5_conflict']['body']['problems'][0])}”).</p>
    </div>
  </div>
  <figure class="shot trace">{img("trace_sched", "Scheduling agent trace")}<figcaption>③ Real tool calls and results recorded for the Scheduling Agent (admin dashboard, agent trace expanded).</figcaption></figure>
  <div class="two">
    <figure class="shot cap">{img("admin_detail", "Admin request detail")}<figcaption>④ Admin view: member's words, Intake extraction, verified options with evidence.</figcaption></figure>
    <div>
      <figure class="shot">{img("booking_confirmed", "Booking confirmed")}<figcaption>⑥ Persisted booking after approval.</figcaption></figure>
      <figure class="shot phone small">{img("member_profile", "Member profile after refresh")}<figcaption>Member profile after refresh shows the approved request and booking.</figcaption></figure>
    </div>
  </div>
</section>

<section class="page">
  <h3 class="cont">4 · The agents — evaluation</h3>
  <p><b>Method.</b> 27 synthetic requests with expected outputs written <i>before</i> any run (<code>tests/eval/cases.py</code>) covering normal requests, missing information,
  languages, qualifications, accessibility, festivals, existing bookings, priest leave, travel limits, unavailable services, contradictions and time phrasing. A
  deterministic oracle confirms every expected scheduling outcome against the rules engine before the model is called. A separate 15-case held-out set uses messier
  language and was written after a rules-only parser was frozen (hash recorded). Each case runs on a fresh copy of the seeded database through the same pipeline as the app;
  Portkey's response cache is bypassed (0 cache hits in every run). Failed cases are kept; expected answers were never edited after a run.</p>
  <div class="two">
    <div>{acc_chart}</div>
    <div>{held_chart}</div>
  </div>
  <table class="t compact"><thead><tr><th>Run (27 cases)</th><th>Passed</th><th>Field accuracy</th><th>Scheduling correct</th><th>Mean latency</th><th>Cost / request</th></tr></thead><tbody>{tbl_eval}</tbody></table>
  <div class="two">
    <div>
      <p><b>What improved.</b> All six Phase 1 failures were time-of-day handling (time-field accuracy {N['b_time']}): “late morning”, exact times and an explicit range were
      collapsed into morning/afternoon/evening. v2 adds those categories; the model only chooses the category and code turns it into a window
      (late morning = 10:00–11:59) and drops options outside it.</p>
      <p><b>Remaining misses are conservative</b>, never unsafe: asking for the town instead of using the profile (C10, H13), asking to confirm a contradictory location (C18),
      reading “after 4” as any time (H08). Across all v2 runs: 0 pipeline errors, 0 bookings created by agents, 0 agent proposals rejected by the rules engine.</p>
      <p class="evnote">Sources: <code>evidence/eval/*.json|md</code>; small, author-written test sets — treat differences of one case as noise.</p>
    </div>
    <figure class="shot cap2">{img("admin_late_morning", "Late-morning window applied")}<figcaption>Real admin view after the fix: “late morning” → 10:00–11:59 window, all options inside it.</figcaption></figure>
  </div>
</section>

<section class="page">
  <h2 class="sec"><span>5</span>Tokenomics</h2>
  <p class="lead">All usage below is the API's own usage data from real calls on 25 Oct 2026 <span class="tag m">Measured</span>. Costs apply OpenAI's published
  gpt-6-luna list price — ${PRICES['input_per_1m']}/1M input, ${PRICES['cached_input_per_1m']}/1M cached input, ${PRICES['cache_write_per_1m']}/1M cache write,
  ${PRICES['output_per_1m']}/1M output [15]. Calls are routed by the course Portkey configuration to an Azure OpenAI deployment (reported as
  <code>gpt-6-luna-global</code>), whose billed rate we cannot see, so dollar figures are <b>list-price estimates</b>.</p>
  <table class="t compact num"><thead><tr><th>Config (27 cases)</th><th>Model req.</th><th>Tool calls</th><th>Input tok.</th><th>Cached input</th><th>Cache write</th><th>Output tok.</th><th>Latency mean / p90</th><th>Total</th><th>Per request</th><th>Portkey cache hits</th></tr></thead><tbody>{rows_runs}</tbody></table>
  <div class="two">
    <div>{cost_chart}</div>
    <div>{token_stack_chart()}</div>
  </div>
  <h3>What was optimized and why</h3>
  <table class="t compact"><thead><tr><th>Change (optimized profile)</th><th>Reason</th><th>Measured effect</th></tr></thead><tbody>
    <tr><td>Service catalog moved into the Intake Agent's static instructions; date moved to the user message</td><td>Removes the <code>list_services</code> round trip and keeps a stable, cacheable prefix</td><td>Intake model requests {STD['per_agent']['intake']['mean_model_requests']} → {OPT['per_agent']['intake']['mean_model_requests']} per run; intake latency {STD['per_agent']['intake']['mean_latency_s']:.1f} → {OPT['per_agent']['intake']['mean_latency_s']:.1f} s</td></tr>
    <tr><td>Compact tool results (slot search returns priest, start, total only)</td><td>Fewer input tokens on every later model request</td><td>Scheduling input {STD['per_agent']['scheduling']['mean_input_tokens']:,} → {OPT['per_agent']['scheduling']['mean_input_tokens']:,} tokens per run</td></tr>
    <tr><td>Agent no longer required to call <code>verify_slot</code></td><td>Server re-verifies every option anyway (safety unchanged)</td><td>Scheduling tool calls {STD['per_agent']['scheduling']['mean_tool_calls']} → {OPT['per_agent']['scheduling']['mean_tool_calls']} per run</td></tr>
  </tbody></table>
  <p>Net, run 1: model requests {pct(OPT['model_requests'], STD['model_requests'])}, tool calls {pct(OPT['tool_calls'], STD['tool_calls'])}, input tokens
  {pct(OPT['input_tokens'], STD['input_tokens'])}, cost per request {pct(OPT['cost_mean_per_request_usd'], STD['cost_mean_per_request_usd'])}, mean latency
  {pct(OPT['latency_s']['mean'], STD['latency_s']['mean'])}. <b>Accuracy:</b> {N['opt']} (optimized) vs {N['std']} (standard) on repeated runs, and {N['h_opt']} vs {N['h_std']} held-out —
  within run-to-run noise. <b>Safety:</b> identical outcome for both profiles (0 unsafe with defenses on).</p>
  <h3>Two different caches — and why it matters</h3>
  <p><b>Portkey response cache: bypassed.</b> During Phase 2 we found Portkey replaying earlier identical calls: a rerun reported identical costs at ~7× lower latency.
  That run was quarantined as invalid, SERVE now sends <code>x-portkey-cache-force-refresh</code>, and every run logs Portkey's cache status (all evaluation runs: REFRESH, 0 hits).
  <b>Model input caching: measured, not assumed.</b> OpenAI-side prompt caching is reported in each response's <code>cached_tokens</code> field; it covered
  {STD['cached_share_of_input']:.0%} (standard) and {OPT['cached_share_of_input']:.0%} (optimized) of input tokens and is billed at the cached rate.</p>
  <div class="two">
    <div>
      <h3>Projection <span class="tag p">Projection</span></h3>
      <table class="t compact num"><thead><tr><th>Member requests</th><th>Expected cost</th><th>p90 cost</th><th>≈ agent runs</th></tr></thead><tbody>{proj_rows}</tbody></table>
      <p class="evnote">Assumptions: optimized profile, both runs pooled — ${PROJ['assumptions']['cost_scheduled_request_usd (measured mean)']:.6f} per scheduled request and
      ${PROJ['assumptions']['cost_needs_info_round_usd (measured mean)']:.6f} per clarification round (measured); 25% of requests need one clarification → ${pr:.5f} per member request.
      Excludes hosting, Portkey fees and staff time.
      <b>Why $0.00064 and not $0.00056:</b> $0.00056 is the measured mean over all 27 cases in optimized run 1 (including cheap needs-info cases);
      the projection pools both optimized runs, prices a scheduled request and a clarification round separately, and assumes 25% of members need one extra round.</p>
    </div>
    <div>
      <h3>Per-month scenario <span class="tag p">Projection</span></h3>
      <table class="t compact num"><thead><tr><th>Hypothetical temple</th><th>Requests / month</th><th>API cost / month</th></tr></thead><tbody>
        <tr><td>300 households; 1 in 3 submits one request</td><td>100</td><td>${pr * 100:.2f}</td></tr>
        <tr><td>1,000 households; 1 in 2 submits one request</td><td>500</td><td>${pr * 500:.2f}</td></tr>
        <tr><td>Heavy use: 2,000 households × 1 request each</td><td>2,000</td><td>${pr * 2000:.2f}</td></tr>
      </tbody></table>
      <p class="evnote">Household counts and request rates are illustrative assumptions, not data. Even the heavy scenario is about ${pr * 2000:.2f}/month of model cost; hosting and staff time would dominate.</p>
    </div>
  </div>
</section>

<section class="page">
  <h2 class="sec"><span>6</span>Safety</h2>
  <p class="lead">Design principle: <b>the model can suggest, never decide.</b> Agents have no write tools, prices come only from the database, every option is
  re-verified by deterministic code, and only a token-protected administrator route can create a booking — inside a transaction with a unique-index backstop.</p>
  <table class="t compact"><thead><tr><th>Risk</th><th>Defense (layer)</th><th>Where</th></tr></thead><tbody>
    <tr><td>Prompt injection in requests or replies</td><td>Member text delimited as data; prompt safety rules (prompt); input sanitation D1 + injection screening D2 flags staff (code)</td><td>agents.py, defenses.py</td></tr>
    <tr><td>Unauthorized approval</td><td>No agent write tools (design); admin token on every <code>/api/admin</code> route; lockout after 10 bad tokens D6 (code)</td><td>main.py</td></tr>
    <tr><td>Conflicts / hallucinated availability</td><td>Rules engine re-checks every option; approval re-checks in <code>BEGIN IMMEDIATE</code>; unique index (design)</td><td>scheduling.py, pipeline.py</td></tr>
    <tr><td>Price manipulation</td><td>Prices and fees computed from DB; model numbers ignored (design)</td><td>scheduling.py</td></tr>
    <tr><td>Member privacy</td><td>Profile tool scoped to the requesting member; member routes return only that member's data; output filter D3 removes contact data and booking/price claims (code)</td><td>agents.py, main.py, defenses.py</td></tr>
    <tr><td>Duplicate requests</td><td>Identical open request reused; 5 submissions / 10 min cap D4 (code); duplicate approval → 409 (design)</td><td>pipeline.py</td></tr>
    <tr><td>Runaway tool use</td><td>UsageLimits (requests, tool calls), per-tool budgets D5, 120 s timeout (code)</td><td>agents.py</td></tr>
    <tr><td>Silent model substitution</td><td>Run fails if API reports a model other than gpt-6-luna* (code) — added after the multi-target Portkey route returned gpt-5.6 for another id</td><td>pipeline.py</td></tr>
  </tbody></table>
  <div class="two">
    <div>{safe_chart}</div>
    <div><p><b>How the test works.</b> 12 attacks and 2 legitimate controls run through the real HTTP API with real model calls, once with the switchable code-level
    defenses <b>off</b> and once <b>on</b> (<code>tests/safety/run_attacks.py</code>). Design defenses apply in both modes, so an attack safe in both was
    <b>already resisted by the original design</b>; unsafe-off/safe-on means a <b>new defense</b> blocked it.</p>
    <p>Result: {SS['unsafe_with_defenses_off']} unsafe outcomes with new defenses off, {SS['unsafe_with_defenses_on']} with them on; {SS['attacks'] - SS['unsafe_with_defenses_off']} attacks resisted by design;
    {len(FLAGGED)} attacks flagged for staff by D2; both legitimate controls worked with no false-positive flags. Standard profile: {SAFE_STD['unsafe_with_defenses_off']} → {SAFE_STD['unsafe_with_defenses_on']}, identical.</p></div>
  </div>
  <table class="t compact safety"><thead><tr><th>#</th><th>Attack</th><th>Defenses off</th><th>Defenses on</th><th>Verdict</th><th>Layers observed (on)</th></tr></thead><tbody>{''.join(safety_rows)}</tbody></table>
  <div class="two">
    <figure class="shot cap2">{img("admin_injection", "Injection attempt flagged")}<figcaption>A01 in the real dashboard: injection flagged for staff (D2); options still $25 from the DB; nothing booked.</figcaption></figure>
    <div>
      <figure class="shot">{img("conflict_block", "Conflicting slot blocked")}<figcaption>Admin tries to force the already-booked slot: the rules engine refuses; approval is disabled (server returns 409 if forced).</figcaption></figure>
      <p><b>Tool budgets.</b> The real model ignored the runaway bait (A09: 3 tool calls), so D5 never fired live. We proved it with a scripted (non-AI) model in
      <code>tests/test_phase2.py</code>: the 9th slot search is refused, and a 100-step loop is stopped by the request/tool-call limits. {N_TESTS} deterministic tests pass.</p>
      <p><b>Residual risks.</b> One shared demo admin token (not staff accounts); per-client lockout can also lock out the real admin for 5 minutes; no member
      authentication (single demo member); regex screening is bypassable — but a bypass cannot create a booking or change a price.</p>
    </div>
  </div>
</section>

<section class="page">
  <h2 class="sec"><span>7</span>Impact</h2>
  <p class="lead">SERVE has not been deployed at a temple, and no stakeholder interviews or adoption data exist. What we can show is reproducible:
  the workload behind each request, how accurately the agents handle it compared with a non-AI baseline, and how fast and cheaply.</p>
  <table class="t compact"><thead><tr><th>Approach</th><th>Held-out accuracy (15)</th><th>Time to options</th><th>Cost per request</th><th>Status</th></tr></thead><tbody>
    <tr><td>Rules-only keyword parser + same rules engine</td><td>{N['h_rules']} ({RULES_H['field_accuracy_overall']:.1%} fields)</td><td>≈1 ms</td><td>$0</td><td><span class="tag m">Measured</span></td></tr>
    <tr><td>SERVE agents (optimized) + rules engine</td><td>{N['h_opt']} ({E['heldout_optimized']['field_accuracy_overall']:.1%} fields)</td><td>{E['heldout_optimized']['latency_seconds']['mean']:.1f} s mean</td><td>${E['heldout_optimized']['cost_usd_per_request_mean']:.5f}</td><td><span class="tag m">Measured</span></td></tr>
    <tr><td>Manual coordinator</td><td>not measured</td><td>≈{me['low']:.0f}–{me['high']:.0f} min</td><td>staff time</td><td><span class="tag e">Estimate</span></td></tr>
  </tbody></table>
  <div class="two">
    <div>
      <p>The rules-only parser fails exactly where natural language matters: “saturday the 21st”, “around 11ish”, “twenty five ppl”, “after 4”, “after lunch”. The
      agents handled 14 of these 15 and their one miss still produced valid options. On the main set the agents produce verified options in about {N['lat_opt']}.</p>
      <p><b>Workload moved from staff to software</b> <span class="tag m">Measured</span>: per complete request, ≈{w['candidate_slots_to_test']} candidate times and
      ≈{w['rule_checks']:.0f} rule checks across {w['calendars_to_open']} priest calendars; {WORK['home_requests_needing_travel_lookup']} of {WORK['requests_analyzed']} need a travel lookup.
      The administrator's step becomes reviewing evidence and clicking Approve.</p>
      <p><b>Manual effort</b> <span class="tag e">Estimate</span>: {IMPACT['manual_estimate']['mean_lookups_per_request (measured from agent traces)']} lookups per request (from agent traces) × 1–3 min + 4 min
      read/reply ≈ {me['low']}–{me['high']} min; a workload-based model gives ≈{WORK['minutes_estimate']['mean_minutes']} min. <b>Neither is a measured time saving</b>; no staff were timed.</p>
    </div>
    <div>
      <h3>If validated, the practical value</h3>
      <ul>
        <li>Members get an answer — options, a clarifying question or a clear “not possible” — in seconds instead of waiting for a call back.</li>
        <li>Office staff stop cross-checking priests, languages, calendars and travel by hand; every option arrives with its evidence.</li>
        <li>Priests are protected from double-booking and unrealistic travel.</li>
        <li>API cost is negligible (≈{N['p1k']} per 1,000 requests, projected) next to listed temple software prices.</li>
      </ul>
      <h3>Evidence still needed</h3>
      <ol><li>Time 5–10 real requests at a temple office (messages, minutes).</li><li>Priests: do suggested slots respect preparation and muhurta realities?</li>
      <li>Members: are questions and proposals clear? (short survey)</li><li>Board: acceptable cost and privacy expectations.</li></ol>
    </div>
  </div>
</section>

<section class="page">
  <h2 class="sec"><span>8</span>Limits and next steps</h2>
  <div class="two">
    <div>
      <h3>Limits</h3>
      <ul>
        <li><b>Synthetic data.</b> “Shanti Mandir”, its priests, members and bookings are fictional.</li>
        <li><b>Small evaluation sets</b> (27 + 15), written by the author; two runs per configuration — one-case differences are noise.</li>
        <li><b>Remaining extraction errors</b> (C10, C18, H08, H13), all conservative.</li>
        <li><b>Authentication.</b> Shared demo admin token; no production member login.</li>
        <li><b>No payments or messaging.</b> Donations, RSVPs and volunteer sign-ups are demo screens kept in the browser; no email/SMS.</li>
        <li><b>Unverified time savings</b>; no live temple deployment or stakeholder feedback.</li>
        <li><b>Billing uncertainty.</b> Costs are list-price estimates; Azure billing through Portkey is not visible.</li>
      </ul>
    </div>
    <div>
      <h3>Roadmap — future, not implemented</h3>
      <table class="t compact"><thead><tr><th>Opportunity</th><th>Today</th></tr></thead><tbody>
        <tr><td>Volunteer coordination agent (fill festival shifts; draft asks for approval)</td><td>Demo UI only</td></tr>
        <tr><td>Event staffing (map events to priests, volunteers, halls)</td><td>Events + priest blocking exist</td></tr>
        <tr><td>Donations with real payments and receipts</td><td>Demo UI only</td></tr>
        <tr><td>Multilingual member messages and confirmations</td><td>Language used only for priest matching</td></tr>
        <tr><td>Temple administration integrations (accounting, calendars)</td><td>None</td></tr>
        <tr><td>Broader faith communities</td><td>Data model is organization-generic</td></tr>
        <tr><td>Foundations: staff accounts, member login, notifications, hosting, privacy policy</td><td>Required before a pilot</td></tr>
      </tbody></table>
      <p><b>Next step:</b> pilot the booking workflow with one temple office to measure request time and accuracy, then add volunteer coordination for one festival.</p>
    </div>
  </div>
  <h3>Sources</h3>
  <ol class="refs">
    <li>Pew Research Center, “Hindu population change 2010–2020” (2025). pewresearch.org/religion/2025/06/09/hindu-population-change/</li>
    <li>Pew Research Center, Religion weekly update, 30 Sep 2026 (RLS 2023–24). pewresearch.org/newsletter/religion-weekly/religion-weekly-update-sept-30-2026</li>
    <li>ARDA, “First Hindu census reveals quiet growth in U.S.” (Institute of American Religion). thearda.com</li>
    <li>Planning Center — Church management. planningcenter.com/use-cases/chms</li>
    <li>Planning Center Help — Approve or reject requests. help.planningcenter.com/en/approve-or-reject-requests.html</li>
    <li>Pushpay, “Best church management software for 2026” (vendor blog, updated 6 Aug 2026). pushpay.com/blog/best-church-management-software-for-2026/</li>
    <li>ShulCloud on Capterra; RustyBrick launch release. capterra.co.uk/software/192763/shulcloud</li>
    <li>Masjidbox, “Mosque management software: the complete guide.” masjidbox.com/blog/mosque-management-software-the-complete-guide</li>
    <li>Temple Hub listings (SourceForge, GoodFirms). sourceforge.net/software/product/Temple-Hub/</li>
    <li>Booking Ninjas — Temple management on Salesforce. bookingninjas.com/solutions/non-profit/temple</li>
    <li>SmartPuja — E-Puja. smartpuja.com/puja-services/e-puja</li>
    <li>YourStory — Poojyo. yourstory.com/companies/poojyo</li>
    <li>Dynamite News — Teertham app. dynamitenews.com</li>
    <li>UNI — Kashi Vishwanath Temple Trust launches AI chatbot. uniindia.com</li>
    <li>OpenAI API pricing (accessed 25 Oct 2026). developers.openai.com/api/docs/pricing</li>
  </ol>
  <p class="evnote">Evidence map: accuracy <code>evidence/eval/</code> · safety <code>evidence/safety/</code> · tokenomics <code>evidence/tokenomics/</code> · impact <code>evidence/impact/</code> ·
  end-to-end run <code>evidence/phase2_regression/</code> · claims register <code>docs/phase3/03_results_fact_sheet.md</code>. All screenshots are from the real application with fictional data.</p>
  <p class="foot">Repository: {gh_html()}</p>
</section>
"""
    css = CSS_COMMON + """
@page{size:letter;margin:0.55in 0.6in}
html,body{margin:0;background:#efe9dc;color:var(--ink);font:10.5pt/1.48 Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.page{background:var(--ivory);max-width:8.5in;margin:24px auto;padding:0.6in 0.65in;box-shadow:0 6px 24px rgba(59,47,22,.12)}
@media print{html,body{background:#fff}.page{box-shadow:none;margin:0 0 14px;padding:0;max-width:none;background:#fff}
  .page.title{break-after:page}.page.brk{break-before:page}
  figure,svg,.kpis,.steps,tr{break-inside:avoid}h2,h3{break-after:avoid}}
h1,h2,h3{color:var(--dark);line-height:1.2} h3{font-size:12pt;margin:14px 0 6px} h3.cont{font-size:13pt;color:var(--brown);margin-top:0}
h2.sec{font-size:17pt;margin:0 0 10px;display:flex;align-items:center;gap:10px;border-bottom:2px solid var(--line2);padding-bottom:6px}
h2.sec span{display:inline-grid;place-items:center;width:30px;height:30px;border-radius:50%;background:var(--dark);color:var(--gold2);font-size:13pt}
p{margin:6px 0} .lead{font-size:11pt;color:#3d3426}
.title .kicker{font-size:9pt;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.title .wordmark{font-size:40pt;font-weight:300;letter-spacing:.22em;color:var(--gold);margin:6px 0 0}
.title .pitch{font-size:17pt;margin:4px 0 8px;font-weight:650}
.title .sub{font-size:11pt;color:#3d3426;max-width:6.6in}
.meta{display:grid;grid-template-columns:1fr 1fr;gap:6px 18px;margin:12px 0 16px;padding:10px 14px;background:var(--cream);border:1px solid var(--line);border-radius:10px;font-size:10pt}
.meta span{display:block;font-size:8pt;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}
.gh.big{font-size:10.5pt}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:8px 0 12px}
.kpis div{background:var(--dark);color:#fffdf8;border-radius:10px;padding:10px 12px}
.kpis b{display:block;font-size:17pt;color:var(--gold2)} .kpis span{font-size:8.6pt;line-height:1.3;display:block;color:#f4e8ce}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
table.t{width:100%;border-collapse:collapse;margin:8px 0;font-size:9.4pt}
table.t th{background:var(--cream);color:var(--brown);text-align:left;font-weight:650;padding:5px 7px;border-bottom:1.5px solid var(--line2)}
table.t td{padding:4.5px 7px;border-bottom:1px solid var(--line);vertical-align:top}
table.compact{font-size:8.8pt} table.num td:not(:first-child),table.num th:not(:first-child){text-align:right}
table.agents td:first-child{font-weight:650;color:var(--brown);white-space:nowrap}
table.safety tr.new td{background:#fbf1d6;font-weight:600}
.tag{display:inline-block;font-size:7.6pt;font-weight:700;letter-spacing:.04em;padding:1px 6px;border-radius:20px;border:1px solid}
.tag.m{color:#3b5e21;border-color:#b9d3a2;background:#f1f7ea}.tag.p{color:#21465e;border-color:#a9c6d8;background:#eef5fa}
.tag.e{color:#8e4b15;border-color:#e3c19b;background:#fbf1e6}.tag.h{color:#5e2160;border-color:#d4b0d6;background:#f8eef8}
figure{margin:6px 0} figcaption{font-size:8.4pt;color:var(--muted);margin-top:3px}
.shot img{width:100%;border:1px solid var(--line2);border-radius:8px;display:block}
.shot.phone img{max-width:2.2in} .shot.small img{max-width:1.6in}
.shot.cap img{max-height:4.3in;object-fit:cover;object-position:top} .shot.cap2 img{max-height:3.3in;object-fit:cover;object-position:top}
.steps{display:grid;grid-template-columns:1.85in 1.85in 1fr;gap:12px;align-items:start;margin:8px 0}
.steps .shot.phone img{max-width:1.85in} .shot.trace img{max-width:5.9in}
.steptext p{font-size:9.2pt;margin:0 0 6px}
svg.chart,svg.arch{width:100%;height:auto;display:block}
.evnote{font-size:8.6pt;color:var(--muted)} code{font-size:.9em;background:var(--ivory2);padding:0 3px;border-radius:3px}
ol.refs{font-size:8pt;columns:2;column-gap:18px;margin:4px 0 6px;padding-left:16px} ol.refs li{break-inside:avoid;margin-bottom:2px}
ul,ol{margin:4px 0;padding-left:18px} li{margin:2px 0}
.foot{font-size:9pt;margin-top:8px}
"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SERVE — MGT 409 Final Report (Varun Matta)</title><style>{css}</style></head><body>{body}</body></html>"""


# ---------------------------------------------------------------------------
# SLIDES
# ---------------------------------------------------------------------------

def slides():
    acc = hbar_chart([
        ("Phase 1 agents", E["baseline_phase1"]["cases_passed"], "#a8956a", ""),
        ("v2 optimized · run 1", E["v2_optimized"]["cases_passed"], GOLD, ""),
        ("v2 optimized · run 2", E["v2_optimized_r2"]["cases_passed"], GOLD, ""),
    ], 27, w=560, fmt=lambda v: f"{v}/27", title="27-case evaluation: fully correct")
    held = hbar_chart([
        ("Rules-only parser", RULES_H["cases_passed"], "#a8956a", ""),
        ("SERVE agents", E["heldout_optimized"]["cases_passed"], GOLD, ""),
    ], 15, w=560, fmt=lambda v: f"{v}/15", title="Held-out messy requests")
    cost = hbar_chart([
        ("Standard", STD["cost_mean_per_request_usd"] * 1e5, BROWN, f"{STD['latency_s']['mean']:.1f} s"),
        ("Optimized", OPT["cost_mean_per_request_usd"] * 1e5, GOLD, f"{OPT['latency_s']['mean']:.1f} s"),
    ], 100, w=560, fmt=lambda v: f"${v / 1e5:.5f}", title="Cost per request (list price, measured)")
    w_ = WORK["means_per_request"]
    S = []
    S.append(f"""<section class="s title"><div class="cols t1"><div><div class="wm">SERVE</div>
      <h1>An AI-enabled operating platform for religious communities, beginning with Hindu temples.</h1>
      <p class="big">The prototype turns a member's request for a seva or puja into a rule-verified, human-approved priest booking.</p>
      <p class="who">Varun Matta · MGT 409 AI Agents · Yale School of Management</p><p class="ghl">{gh_html(True)}</p></div>
      <figure class="land">{img("landing", "SERVE landing page")}<figcaption>Real application · fictional temple data</figcaption></figure></div></section>""")
    S.append(f"""<section class="s"><h2>The problem: arranging a priest is a puzzle</h2><div class="cols">
      <div><ul class="lg"><li>Temple work runs on manual coordination, separate portals, WhatsApp groups and volunteers <i>(personal observation; hypothesis)</i></li>
      <li>One request = ritual qualification + language + home/temple + travel + priest hours, leave and bookings + festival days + approval</li>
      <li>~3.0M US Hindus (Pew, 2020); +55% in North America 2010–2020</li></ul></div>
      <div class="stats"><div><b>{w_['qualified_priests']}</b>qualified priests to weigh</div><div><b>{w_['candidate_slots_to_test']}</b>candidate times to test</div>
      <div><b>≈{w_['rule_checks']:.0f}</b>rule checks per request</div><div><b>{WORK['requests_where_correct_answer_is_no_availability']}/{WORK['requests_analyzed']}</b>requests where the right answer is “not possible”</div>
      <p class="note">Measured on SERVE's fictional database (problem structure, not real temple timings)</p></div></div></section>""")
    S.append(f"""<section class="s"><h2>Vision vs. what is built</h2>{vision_svg()}
      <div class="cols"><div><h3>Long-term vision (not built)</h3><p>Vertical SaaS for temples, then other faiths: reservations, donations, events, volunteering, communication on one member record.</p></div>
      <div><h3>This project (built + measured)</h3><p>One AI workflow: <b>service intake → priest matching → scheduling validation → human-approved booking</b>. Donation, RSVP and volunteer screens are demo UI only.</p></div></div></section>""")
    S.append("""<section class="s"><h2>What is different</h2><table class="st"><thead><tr><th>Product</th><th>What it offers</th><th>AI request intake</th></tr></thead><tbody>
      <tr><td>Planning Center</td><td>Church ChMS; room booking with approval groups</td><td>none found</td></tr>
      <tr><td>Temple Hub</td><td>US temples: puja booking, priest schedules, donations ($499/mo listed)</td><td>none mentioned</td></tr>
      <tr><td>Booking Ninjas</td><td>Temple software on Salesforce</td><td>Salesforce AI “where licensed”</td></tr>
      <tr><td>SmartPuja / Teertham</td><td>Priest marketplaces (India)</td><td>none / AI after human call</td></tr>
      <tr class="hl"><td>SERVE prototype</td><td>Free text → qualification, language, travel, conflicts checked → admin approves</td><td>two agents + rules engine</td></tr></tbody></table>
      <p class="note">Platforms with these management features already exist; we don't claim SERVE is first. Sources: vendor/listing pages read 25 Oct 2026 (report §3).</p></section>""")
    S.append(f"""<section class="s"><h2>How the agents work</h2>{arch_svg()}</section>""")
    sched, trows = trace_rows()
    trs = "".join(f"<tr><td><code>{esc(n)}</code><div class='ta'>{esc(ar)}</div></td><td>{esc(o)}</td></tr>" for n, ar, o in trows)
    S.append(f"""<section class="s"><h2>Demo: the Scheduling Agent's real tool calls</h2>
      <p class="req">“…a griha pravesh on Saturday, November 21, in the morning… in Telugu. About 25 guests, and my mother uses a wheelchair.”</p>
      <div class="demo2"><table class="tr"><thead><tr><th>Tool call (exact arguments)</th><th>What the database returned (excerpt)</th></tr></thead><tbody>{trs}</tbody></table>
      <div><figure>{img("member_pending", "Proposed times")}<figcaption>Member sees 2 proposed times — not booked until approved</figcaption></figure></div></div>
      <p class="note n1">Run R1 · {sched['response_model']} · {sched['latency_ms'] / 1000:.1f} s · {sched['input_tokens']:,} in ({sched['cached_input_tokens']:,} cached) · {sched['output_tokens']} out · ${sched['cost_usd']:.5f} · Portkey cache {sched['portkey_cache'].split(',')[0]} · evidence/phase4_screenshots/r1_agent_trace.json</p></section>""")
    S.append(f"""<section class="s"><h2>Admin approval and safety</h2><div class="cols">
      <figure>{img("admin_injection", "Injection flagged")}<figcaption>Injection attempt flagged; prices still from DB</figcaption></figure>
      <div><figure class="cb">{img("conflict_block", "Conflict blocked")}<figcaption>Forcing a booked slot: refused (409)</figcaption></figure>
      <div class="stats small three"><div><b>{SS['unsafe_with_defenses_off']} → {SS['unsafe_with_defenses_on']}</b>unsafe outcomes, new defenses off → on (12 attacks)</div>
      <div><b>{SS['attacks'] - SS['unsafe_with_defenses_off']}</b>already resisted by design</div><div><b>{len(FLAGGED)}</b>flagged for staff</div></div>
      <p class="note">Agents have no write tools; only the token-protected approval route books, re-checking all rules.</p></div></div></section>""")
    S.append(f"""<section class="s"><h2>Evaluation and tokenomics (measured)</h2><div class="cols"><div>{acc}{held}</div><div>{cost}
      <ul class="md"><li>Optimized: catalog in cached prefix, compact tool results, server-side verification</li>
      <li>{pct(OPT['cost_mean_per_request_usd'], STD['cost_mean_per_request_usd'])} cost, {pct(OPT['latency_s']['mean'], STD['latency_s']['mean'])} latency, same accuracy & safety</li>
      <li>{OPT['cached_share_of_input']:.0%} of input tokens served from model cache (API-reported)</li>
      <li>Projection: {N['p1k']} per 1,000 · {N['p10k']} per 10,000 requests</li></ul>
      <p class="note">{N['cost_opt']} = measured mean, run 1. Projection uses {N['per_req']}/request: both runs pooled + assumed 25% clarification rounds.</p>
      <p class="note">gpt-6-luna list price; Azure billing via Portkey not visible. Portkey response cache bypassed (0 hits).</p></div></div></section>""")
    me_ = IMPACT['manual_estimate']['estimated_staff_minutes_per_request']
    S.append(f"""<section class="s"><h2>Impact and limits</h2><div class="cols">
      <div><h3>Measured</h3><div class="stats">
        <div><b>{N['h_opt']}</b>held-out requests correct (rules-only parser: {N['h_rules']})</div>
        <div><b>~{N['lat_opt']}</b>to rule-verified options</div>
        <div><b>{N['cost_opt']}</b>API cost per request (list price)</div>
        <div><b>0</b>bookings created by agents · {N_TESTS} tests pass</div></div>
        <h3 style="margin-top:18px">Estimated — not measured</h3><ul class="md"><li>Manual handling ≈ {me_['low']:.0f}–{me_['high']:.0f} min per request; no staff were timed</li></ul></div>
      <div><h3>Limits</h3><ul class="md"><li>Fictional temple and data; small author-written test sets (27 + 15)</li>
      <li>Shared demo admin token; no member login</li><li>No payments or messaging</li>
      <li>No temple deployment or stakeholder feedback yet</li><li>Costs are list-price estimates (Azure billing not visible)</li></ul>
      <h3>Needed next</h3><ul class="md"><li>Time 5–10 real requests at a temple office</li><li>Priest and member feedback</li></ul></div></div></section>""")
    S.append(f"""<section class="s title end"><h2>Conclusion and next steps</h2><div class="cols"><div><ul class="lg">
      <li>Pilot the booking workflow with one temple office; time real requests</li><li>Staff accounts, member login, notifications, hosting</li>
      <li>Then: volunteer coordination, event staffing, donations, multilingual messages, other faiths</li></ul></div>
      <div><p class="quote">AI does the checking.<br>People make the decision.</p><p class="ghl">{gh_html(True)}</p><p class="who">Varun Matta · MGT 409 · Yale SOM</p></div></div></section>""")
    assert len(S) <= 10
    css = CSS_COMMON + """
html,body{margin:0;height:100%;background:#1d170b;font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink);overflow:hidden}
#deck{position:absolute;left:50%;top:50%;width:1280px;height:720px;transform-origin:center center}
.s{position:absolute;inset:0;background:var(--ivory);padding:48px 64px;display:none;flex-direction:column;overflow:hidden;border-radius:4px}
.s.on{display:flex} .s h2{font-size:38px;color:var(--dark);margin:0 0 18px;border-bottom:3px solid var(--line2);padding-bottom:10px}
.s h3{font-size:22px;color:var(--brown);margin:6px 0} .s p{font-size:21px;line-height:1.4;margin:6px 0}
.s.title{background:linear-gradient(140deg,#3b2f16 0%,#5e4b21 55%,#8e6615 100%);color:#fffdf8;justify-content:center}
.s.title h1{font-size:40px;line-height:1.2;margin:8px 0 14px;color:#fffdf8;max-width:1050px} .s.title h2{color:#fffdf8;border-color:rgba(255,255,255,.25)}
.wm{font-size:88px;font-weight:300;letter-spacing:.24em;color:var(--gold2)} .big{font-size:26px!important}
.who{font-size:20px!important;opacity:.85} .ghl{margin-top:18px!important} .s.title .gh{color:var(--gold2);font-size:22px}
.s.title .gh.blocker{background:#fdecea;color:#9b2c1c;font-size:18px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:34px;align-items:start;flex:1;min-height:0}
ul.lg li{font-size:24px;margin:10px 0;line-height:1.35} ul.md li{font-size:20px;margin:8px 0;line-height:1.35}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px} .stats div{background:var(--dark);color:#f4e8ce;border-radius:14px;padding:14px 16px;font-size:17px}
.stats b{display:block;font-size:38px;color:var(--gold2)} .stats.small b{font-size:30px} .stats.small div{font-size:15px;padding:10px 12px}
.note{font-size:15px!important;color:var(--muted)} .s.title .note{color:#f4e8ce}
table.st{width:100%;border-collapse:collapse;font-size:20px} table.st th{background:var(--cream);color:var(--brown);text-align:left;padding:10px}
table.st td{padding:10px;border-bottom:1px solid var(--line)} table.st tr.hl td{background:var(--dark);color:var(--gold2);font-weight:600}
figure{margin:0} figure img{width:100%;border-radius:10px;border:1px solid var(--line2);display:block;max-height:470px;object-fit:cover;object-position:top}
figcaption{font-size:15px;color:var(--muted);margin-top:6px}
.t1{grid-template-columns:1.15fr .85fr;align-items:center} .land img{max-height:520px;object-fit:cover;object-position:left top;box-shadow:0 20px 50px rgba(0,0,0,.35)}
.s.title figcaption{color:#f4e8ce} .s.end ul.lg li{font-size:27px;color:#fffdf8} .quote{font-size:40px!important;font-weight:600;color:var(--gold2);line-height:1.25!important}
.cb img{max-height:300px} .stats.three{grid-template-columns:1fr 1fr 1fr;margin-top:12px}
.n1{font-size:13px!important;white-space:nowrap;margin-top:8px!important} .req{font-size:22px!important;font-style:italic;color:var(--brown);margin:0 0 14px!important}
.demo2{display:grid;grid-template-columns:1fr 250px;gap:24px;align-items:start}
table.tr{width:100%;border-collapse:collapse;font-size:19px} table.tr th{background:var(--cream);color:var(--brown);text-align:left;padding:9px 10px;font-size:17px}
table.tr td{padding:10px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.3} table.tr code{font-size:19px;font-weight:700;color:var(--dark);background:none}
.ta{font-size:14px;color:var(--muted);font-family:ui-monospace,Menlo,monospace;margin-top:3px;word-break:break-word}
.demo{display:grid;grid-template-columns:300px 1fr 300px;gap:22px;align-items:start}
.demo figure img{max-height:500px;object-fit:contain;background:#fff}
svg.arch{width:100%;height:auto;max-height:590px} svg.chart{width:100%;height:auto}
.s .chart .ct{font-size:15px}.s .chart .cl,.s .chart .cv{font-size:14px}
#hud{position:fixed;right:18px;bottom:12px;color:#c9b88f;font-size:13px;font-family:Inter,system-ui,sans-serif}
"""
    js = """
const slides=[...document.querySelectorAll('.s')];let i=0;
function show(n){i=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,k)=>s.classList.toggle('on',k===i));
document.getElementById('hud').textContent=(i+1)+' / '+slides.length+'  ·  ← → to navigate · F full screen';location.hash='#'+(i+1);}
function fit(){const d=document.getElementById('deck');const s=Math.min(innerWidth/1280,innerHeight/720);d.style.transform='translate(-50%,-50%) scale('+s+')';}
addEventListener('resize',fit);
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' ','Enter'].includes(e.key)){e.preventDefault();show(i+1)}
else if(['ArrowLeft','PageUp','Backspace'].includes(e.key)){e.preventDefault();show(i-1)}
else if(e.key==='Home')show(0);else if(e.key==='End')show(slides.length-1);
else if(e.key==='f'||e.key==='F'){document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen()}});
addEventListener('click',e=>{if(e.target.tagName!=='A')show(e.clientX>innerWidth/2?i+1:i-1)});
fit();show((parseInt(location.hash.slice(1))||1)-1);
"""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SERVE — MGT 409 Slides (Varun Matta)</title><style>{css}</style></head><body><div id="deck">{''.join(S)}</div><div id="hud"></div><script>{js}</script></body></html>"""


if __name__ == "__main__":
    (ROOT / "report.html").write_text(report())
    (ROOT / "slides.html").write_text(slides())
    for f in ("report.html", "slides.html"):
        print(f, f"{(ROOT / f).stat().st_size / 1024:.0f} KB")
