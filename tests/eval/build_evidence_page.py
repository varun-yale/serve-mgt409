"""Render the saved evidence markdown into one self-contained HTML page (for review/screenshots).

    .venv/bin/python -m tests.eval.build_evidence_page   ->  evidence/evidence_summary.html
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "evidence"
SECTIONS = [
    ("Evaluation — Phase 1 baseline (27 cases)", EV / "eval" / "baseline_phase1.md"),
    ("Evaluation — v2 optimized (27 cases)", EV / "eval" / "v2_optimized.md"),
    ("Evaluation — v2 optimized, held-out (15 cases)", EV / "eval" / "heldout_optimized.md"),
    ("Tokenomics", EV / "tokenomics" / "tokenomics.md"),
    ("Safety — defenses off vs on (optimized profile)", EV / "safety" / "safety_results_optimized.md"),
    ("Operational impact", EV / "impact" / "impact.md"),
]


def inline(t: str) -> str:
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def md_to_html(md: str) -> str:
    out, table, lst = [], [], False
    for line in md.splitlines() + [""]:
        if line.startswith("|"):
            table.append([c.strip() for c in line.strip("|").split("|")])
            continue
        if table:
            head, body = table[0], [r for r in table[2:]]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
                       + "</tbody></table>")
            table = []
        if line.startswith("- "):
            if not lst:
                out.append("<ul>")
                lst = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue
        if lst:
            out.append("</ul>")
            lst = False
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            out.append(f"<h3>{inline(line[3:])}</h3>")
        elif line.strip():
            out.append(f"<p>{inline(line)}</p>")
    return "\n".join(out)


def main():
    parts = []
    for title, path in SECTIONS:
        if path.exists():
            parts.append(f"<section><h2>{html.escape(title)}</h2>{md_to_html(path.read_text())}</section>")
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>SERVE — Phase 2 evidence</title>
<style>
body{{margin:0;background:#fffdf8;color:#2b2518;font:14px/1.5 Inter,system-ui,-apple-system,Segoe UI,sans-serif}}
header{{background:linear-gradient(140deg,#3b2f16,#8e6615 60%,#c9962f);color:#fffdf8;padding:28px 40px}}
header h1{{margin:0;font-size:24px}} header p{{margin:6px 0 0;opacity:.85}}
main{{max-width:1180px;margin:0 auto;padding:24px 40px 60px}}
section{{background:#fff;border:1px solid #f4e8ce;border-radius:16px;padding:20px 24px;margin:18px 0}}
h2{{color:#3b2f16;font-size:18px;margin:0 0 10px}} h3{{color:#5e4b21;font-size:14px;margin:18px 0 6px;text-transform:uppercase;letter-spacing:.08em}}
table{{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0}} th,td{{border-bottom:1px solid #f4e8ce;padding:6px 8px;text-align:left;vertical-align:top}}
th{{color:#6f6453;font-weight:600;background:#fdf7ea}} code{{background:#fbf4e4;padding:1px 4px;border-radius:4px}}
</style></head><body><header><h1>SERVE — Phase 2 evidence summary</h1>
<p>Real gpt-6-luna calls via Portkey (cache bypassed). Fictional demonstration data. Generated from files in evidence/.</p></header>
<main>{''.join(parts)}</main></body></html>"""
    (EV / "evidence_summary.html").write_text(page)
    print("wrote", EV / "evidence_summary.html")


if __name__ == "__main__":
    main()
