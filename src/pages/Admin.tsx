/** Temple office dashboard — review agent recommendations and approve bookings. */

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { ApiError, adminToken, api, fmtDate, fmtTime, fmtTimestamp } from "../api";
import { STATUS_LABEL, STATUS_TONE, formatMoney } from "../types";
import type { ApiBooking, RequestStatus } from "../types";
import { Badge, Button, Card, DemoNote, EmptyState, Field, SectionLabel, Wordmark, inputClass } from "../components/ui";

/* ---------------- API shapes ---------------- */

interface Summary {
  requests_by_status: Partial<Record<RequestStatus, number>>;
  upcoming_bookings: number;
  agent_runs: number;
  ai_cost_usd: number;
  input_tokens: number;
  output_tokens: number;
}

interface RequestRow {
  id: string;
  member_name: string;
  status: RequestStatus;
  source: string;
  service_name: string | null;
  summary: string;
  option_count: number;
  created_at: string;
  risk_flags: RiskFlags;
}

interface RiskFlags {
  injection_patterns?: string[];
  injection_patterns_in_reply?: string[];
  sanitized?: string[];
  output_filtered?: string[];
}

interface SlotCheck {
  ok: boolean;
  problems: string[];
  warnings: string[];
  evidence: string[];
  service_id?: string;
  service_name?: string;
  priest_id?: string;
  priest_name?: string;
  date?: string;
  start_time?: string;
  end_time?: string;
  location_type?: "temple" | "home";
  city?: string | null;
  language?: string | null;
  base_price_cents?: number;
  travel_fee_cents?: number;
  total_cents?: number;
  rationale?: string;
}

interface ToolCall {
  tool_name: string;
  args: Record<string, unknown>;
  result_summary: string;
  ok: number;
  duration_ms: number;
  called_at: string;
}

interface AgentRun {
  id: string;
  agent: string;
  model: string;
  response_model: string | null;
  started_at: string;
  latency_ms: number | null;
  status: string;
  error: string | null;
  model_requests: number | null;
  input_tokens: number | null;
  cached_input_tokens: number | null;
  cache_write_tokens: number | null;
  output_tokens: number | null;
  reasoning_tokens: number | null;
  tool_calls: number | null;
  cost_usd: number | null;
  request_id?: string;
  tool_call_log?: ToolCall[];
}

interface Intake {
  service_id: string | null;
  summary?: string;
  preferred_dates?: string[];
  date_notes?: string | null;
  time_of_day?: string | null;
  time_preference?: string | null;
  earliest_start?: string | null;
  latest_start?: string | null;
  location_type?: string | null;
  city?: string | null;
  city_source?: string | null;
  language?: string | null;
  attendees?: number | null;
  special_requirements?: string[];
  service_match_reason?: string;
}

interface Detail {
  request: {
    id: string;
    member_id: string;
    member_name: string;
    member_email: string;
    source: string;
    raw_text: string;
    status: RequestStatus;
    member_message: string | null;
    admin_note: string | null;
    error: string | null;
    created_at: string;
    updated_at: string;
  };
  intake: Intake | null;
  service_name: string | null;
  recommendation: {
    outcome: string;
    options: SlotCheck[];
    dropped_options: SlotCheck[];
    missing_information: string[];
    notes_for_admin: string;
    verified_by: string;
    time_window?: [string, string] | null;
    outside_time_preference?: boolean;
    profile?: string;
  } | null;
  missing_info: string[];
  risk_flags: RiskFlags;
  agent_runs: AgentRun[];
  approvals: { id: number; decision: string; admin_name: string; note: string | null; decided_at: string }[];
  audit: AuditRow[];
  booking: ApiBooking | null;
}

interface AuditRow {
  id: number;
  ts: string;
  actor: string;
  action: string;
  request_id: string | null;
  booking_id: string | null;
  details_json: string | null;
}

interface Reference {
  priests: { id: string; name: string; languages: string[]; qualifications: string[]; max_travel_miles: number }[];
  services: { id: string; name: string; location_mode: "temple" | "home" | "either"; slot_times: string[] | null }[];
  towns: string[];
}

const APPROVABLE: RequestStatus[] = ["pending_review", "needs_info", "failed"];
const NAME_KEY = "serve_admin_name";

const usd = (n: number | null | undefined, digits = 5) => `$${(n ?? 0).toFixed(digits)}`;
const num = (n: number | null | undefined) => (n ?? 0).toLocaleString("en-US");

/* ================= page ================= */

type AdminTab = "requests" | "bookings" | "runs" | "audit";

export default function Admin() {
  const [authed, setAuthed] = useState<boolean | null>(() => (adminToken.get() ? null : false));
  const [adminName, setAdminName] = useState(() => sessionStorage.getItem(NAME_KEY) ?? "");
  const [tab, setTab] = useState<AdminTab>("requests");
  const [summary, setSummary] = useState<Summary | null>(null);

  useEffect(() => {
    if (!adminToken.get()) return;
    api
      .adminGet("/session")
      .then(() => setAuthed(true))
      .catch(() => setAuthed(false));
  }, []);

  const loadSummary = useCallback(() => {
    api.adminGet<Summary>("/summary").then(setSummary).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (authed) loadSummary();
  }, [authed, loadSummary]);

  if (authed === null) return <Shell />;
  if (!authed)
    return (
      <Shell>
        <TokenGate
          onDone={(name) => {
            setAdminName(name);
            setAuthed(true);
          }}
        />
      </Shell>
    );

  const signOut = () => {
    adminToken.clear();
    setAuthed(false);
  };

  const c = summary?.requests_by_status ?? {};

  return (
    <Shell
      right={
        <div className="flex items-center gap-3">
          <span className="hidden text-[0.8rem] text-charcoal-muted sm:inline">Signed in as {adminName}</span>
          <Button size="sm" variant="ghost" onClick={signOut}>
            Sign out
          </Button>
        </div>
      }
    >
      <div className="mb-6 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-forest-100 bg-forest-100 sm:grid-cols-3 lg:grid-cols-6">
        <Metric label="Pending review" value={c.pending_review ?? 0} />
        <Metric label="Needs information" value={c.needs_info ?? 0} />
        <Metric label="Processing" value={c.processing ?? 0} />
        <Metric label="Upcoming bookings" value={summary?.upcoming_bookings ?? 0} />
        <Metric label="Agent runs" value={summary?.agent_runs ?? 0} />
        <Metric label="AI spend (measured)" value={usd(summary?.ai_cost_usd, 4)} />
      </div>

      <div className="mb-5 flex flex-wrap gap-2">
        {(
          [
            ["requests", "Service requests"],
            ["bookings", "Bookings"],
            ["runs", "Agent runs & cost"],
            ["audit", "Audit log"],
          ] as [AdminTab, string][]
        ).map(([id, label]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`rounded-full border px-4 py-1.5 text-[0.82rem] font-medium transition ${
              tab === id
                ? "border-forest-800 bg-forest-800 text-ivory"
                : "border-forest-200 bg-white text-charcoal-muted hover:border-forest-400"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "requests" && <RequestsTab adminName={adminName} onChange={loadSummary} />}
      {tab === "bookings" && <BookingsTab adminName={adminName} onChange={loadSummary} />}
      {tab === "runs" && <RunsTab />}
      {tab === "audit" && <AuditTab />}
    </Shell>
  );
}

function Shell({ children, right }: { children?: ReactNode; right?: ReactNode }) {
  return (
    <div className="min-h-screen bg-ivory">
      <header className="sticky top-0 z-30 border-b border-forest-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3">
          <div className="flex items-center gap-3">
            <Link to="/" aria-label="SERVE home">
              <Wordmark />
            </Link>
            <span className="hidden text-[0.8rem] font-medium text-charcoal-muted sm:inline">
              Temple office · Shanti Mandir
            </span>
            <Badge tone="gold">Demo data</Badge>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/app" className="text-[0.8rem] text-charcoal-muted transition hover:text-forest-800">
              Member portal →
            </Link>
            {right}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-5 py-6">{children}</main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="bg-white px-4 py-3.5">
      <p className="text-[1.3rem] font-semibold tracking-[-0.01em] text-forest-800">{value}</p>
      <p className="text-[0.74rem] text-charcoal-muted">{label}</p>
    </div>
  );
}

function TokenGate({ onDone }: { onDone: (name: string) => void }) {
  const [token, setToken] = useState("");
  const [name, setName] = useState(() => sessionStorage.getItem(NAME_KEY) ?? "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setBusy(true);
    setError(null);
    adminToken.set(token.trim());
    try {
      await api.adminGet("/session");
      sessionStorage.setItem(NAME_KEY, name.trim());
      onDone(name.trim());
    } catch (e) {
      adminToken.clear();
      setError(e instanceof ApiError && e.status === 401 ? "That admin token isn't valid." : String((e as Error).message));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto mt-10 max-w-md">
      <Card className="p-6">
        <h1 className="mb-1 text-[1.3rem] font-semibold text-forest-800">Temple office sign-in</h1>
        <p className="mb-5 text-[0.85rem] leading-relaxed text-charcoal-muted">
          Enter the admin token from the server's <code>.env</code> (<code>SERVE_ADMIN_TOKEN</code>) or the one
          printed in the backend console at startup.
        </p>
        <Field label="Admin token">
          <input
            type="password"
            className={inputClass}
            value={token}
            onChange={(e) => setToken(e.target.value)}
            autoComplete="off"
          />
        </Field>
        <Field label="Your name" hint="Recorded on approvals and in the audit log. Not a login.">
          <input className={inputClass} value={name} maxLength={60} onChange={(e) => setName(e.target.value)} />
        </Field>
        {error && <p className="mb-3 text-[0.8rem] text-terracotta-600">{error}</p>}
        <Button full disabled={!token.trim() || name.trim().length < 2 || busy} onClick={submit}>
          {busy ? "Checking…" : "Open dashboard"}
        </Button>
        <div className="mt-4">
          <DemoNote>
            Demo-grade access control: one shared token checked by the server on every admin request. A
            production deployment would use real staff accounts.
          </DemoNote>
        </div>
      </Card>
    </div>
  );
}

/* ================= requests ================= */

const FILTERS: { id: RequestStatus | "all"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "pending_review", label: "Pending review" },
  { id: "needs_info", label: "Needs info" },
  { id: "processing", label: "Processing" },
  { id: "approved", label: "Approved" },
  { id: "rejected", label: "Rejected" },
  { id: "failed", label: "Failed" },
  { id: "cancelled", label: "Cancelled" },
];

function RequestsTab({ adminName, onChange }: { adminName: string; onChange: () => void }) {
  const [filter, setFilter] = useState<RequestStatus | "all">("all");
  const [rows, setRows] = useState<RequestRow[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api
      .adminGet<RequestRow[]>(`/requests${filter === "all" ? "" : `?status=${filter}`}`)
      .then((r) => {
        setRows(r);
        setError(null);
      })
      .catch((e) => setError(e.message));
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  const anyProcessing = rows.some((r) => r.status === "processing");
  useEffect(() => {
    if (!anyProcessing) return;
    const t = setInterval(() => {
      load();
      onChange();
    }, 4000);
    return () => clearInterval(t);
  }, [anyProcessing, load, onChange]);

  return (
    <div className="grid gap-5 lg:grid-cols-[0.85fr_1.4fr]">
      <div>
        <div className="mb-3 flex flex-wrap gap-1.5">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`rounded-full border px-3 py-1 text-[0.74rem] font-medium transition ${
                filter === f.id
                  ? "border-forest-700 bg-forest-50 text-forest-800"
                  : "border-forest-100 bg-white text-charcoal-muted hover:border-forest-200"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        {error && <p className="mb-3 text-[0.8rem] text-terracotta-600">{error}</p>}
        {rows.length === 0 ? (
          <EmptyState>No requests here yet. Submit one from the member portal.</EmptyState>
        ) : (
          <div className="space-y-2">
            {rows.map((r) => (
              <button key={r.id} onClick={() => setSelected(r.id)} className="block w-full text-left">
                <Card
                  className={`p-3.5 transition ${
                    selected === r.id ? "border-forest-600 ring-1 ring-forest-600" : "hover:border-forest-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-[0.88rem] font-semibold text-charcoal">
                        {r.service_name ?? "Unidentified service"} · {r.member_name}
                      </p>
                      <p className="mt-0.5 line-clamp-2 text-[0.78rem] leading-relaxed text-charcoal-muted">
                        {r.summary}
                      </p>
                      <p className="mt-1 text-[0.7rem] text-charcoal-muted">
                        {fmtTimestamp(r.created_at)} · {sourceLabel(r.source)}
                        {r.option_count > 0 ? ` · ${r.option_count} option${r.option_count > 1 ? "s" : ""}` : ""}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge tone={STATUS_TONE[r.status]}>{STATUS_LABEL[r.status]}</Badge>
                      {(r.risk_flags?.injection_patterns?.length ?? 0) > 0 && (
                        <Badge tone="terracotta">⚠ Flagged</Badge>
                      )}
                    </div>
                  </div>
                </Card>
              </button>
            ))}
          </div>
        )}
      </div>

      <div>
        {selected ? (
          <RequestDetail
            key={selected}
            id={selected}
            adminName={adminName}
            onChange={() => {
              load();
              onChange();
            }}
          />
        ) : (
          <EmptyState>Select a request to review the agents' work and decide.</EmptyState>
        )}
      </div>
    </div>
  );
}

function sourceLabel(s: string) {
  return s === "ai_request" ? "Free-text (AI)" : s === "request_form" ? "Request form (AI)" : "Slot picker (no AI)";
}

function RequestDetail({ id, adminName, onChange }: { id: string; adminName: string; onChange: () => void }) {
  const [d, setD] = useState<Detail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<{ tone: "ok" | "bad"; text: string; problems?: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [infoMsg, setInfoMsg] = useState("");
  const [rejectMsg, setRejectMsg] = useState("");
  const [editing, setEditing] = useState(false);

  const load = useCallback(() => {
    api
      .adminGet<Detail>(`/requests/${id}`)
      .then((x) => {
        setD(x);
        setError(null);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (d?.request.status !== "processing") return;
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, [d?.request.status, load]);

  const act = async (fn: () => Promise<unknown>, success: string) => {
    setBusy(true);
    setFlash(null);
    try {
      await fn();
      setFlash({ tone: "ok", text: success });
      setNote("");
      setInfoMsg("");
      setRejectMsg("");
      setEditing(false);
      load();
      onChange();
    } catch (e) {
      const err = e as ApiError;
      setFlash({ tone: "bad", text: err.message, problems: err.problems });
      load();
      onChange();
    } finally {
      setBusy(false);
    }
  };

  if (error) return <EmptyState>{error}</EmptyState>;
  if (!d) return <EmptyState>Loading…</EmptyState>;

  const r = d.request;
  const rec = d.recommendation;
  const canDecide = APPROVABLE.includes(r.status);
  const totalCost = d.agent_runs.reduce((s, x) => s + (x.cost_usd ?? 0), 0);

  const approveOption = (i: number) =>
    act(
      () => api.adminPost(`/requests/${id}/approve`, { admin_name: adminName, option_index: i, note: note || null }),
      "Approved — booking confirmed and saved.",
    );

  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-charcoal-muted">
            {r.id} · {sourceLabel(r.source)}
          </p>
          <h2 className="mt-1 text-[1.2rem] font-semibold text-forest-800">
            {d.intake?.summary ?? r.raw_text.slice(0, 90)}
          </h2>
          <p className="mt-1 text-[0.8rem] text-charcoal-muted">
            {r.member_name} · {r.member_email} · submitted {fmtTimestamp(r.created_at)}
          </p>
        </div>
        <Badge tone={STATUS_TONE[r.status]}>{STATUS_LABEL[r.status]}</Badge>
      </div>

      {flash && (
        <div
          className={`mb-4 rounded-xl border px-4 py-3 text-[0.84rem] ${
            flash.tone === "ok"
              ? "border-forest-200 bg-forest-50 text-forest-800"
              : "border-terracotta-100 bg-terracotta-100/60 text-terracotta-600"
          }`}
        >
          <p className="font-medium">{flash.text}</p>
          {flash.problems && flash.problems.length > 0 && (
            <ul className="mt-1 list-disc pl-5 text-[0.8rem]">
              {flash.problems.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {Object.keys(d.risk_flags ?? {}).length > 0 && (
        <div className="mb-4 rounded-xl border border-terracotta-100 bg-terracotta-100/50 px-4 py-3 text-[0.8rem] text-terracotta-600">
          <p className="font-semibold">Safety flags — review the member's words carefully</p>
          {d.risk_flags.injection_patterns && (
            <p>Possible instruction-injection patterns: {d.risk_flags.injection_patterns.join(", ")}</p>
          )}
          {d.risk_flags.injection_patterns_in_reply && (
            <p>Patterns in the member's reply: {d.risk_flags.injection_patterns_in_reply.join(", ")}</p>
          )}
          {d.risk_flags.sanitized && <p>Input cleaned: {d.risk_flags.sanitized.join(", ")}</p>}
          {d.risk_flags.output_filtered && <p>Agent text to member was filtered: {d.risk_flags.output_filtered.join(", ")}</p>}
          <p className="mt-1 text-[0.74rem]">
            Agents cannot book or change prices; every option below was re-checked by the rules engine.
          </p>
        </div>
      )}

      <SectionLabel>Member's words (untrusted input)</SectionLabel>
      <p className="mb-5 whitespace-pre-line rounded-xl border border-forest-100 bg-ivory-200 px-4 py-3 text-[0.86rem] leading-relaxed text-charcoal">
        {r.raw_text}
      </p>

      {r.status === "processing" && (
        <div className="mb-5 flex items-center gap-3 rounded-xl border border-forest-100 bg-white px-4 py-3">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-forest-200 border-t-forest-700" />
          <p className="text-[0.84rem] text-charcoal">Agents are working on this request…</p>
        </div>
      )}

      {r.error && (
        <p className="mb-5 rounded-xl border border-terracotta-100 bg-terracotta-100/50 px-4 py-3 text-[0.8rem] text-terracotta-600">
          Processing error: {r.error}
        </p>
      )}

      {d.booking && (
        <div className="mb-5 rounded-xl border border-forest-200 bg-forest-50 px-4 py-3">
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-forest-700">
            Booking {d.booking.id} · {d.booking.status}
          </p>
          <p className="mt-1 text-[0.95rem] font-semibold text-forest-800">
            {fmtDate(d.booking.date)} · {fmtTime(d.booking.start_time)}–{fmtTime(d.booking.end_time)} ·{" "}
            {d.booking.priest_name}
          </p>
          <p className="text-[0.8rem] text-charcoal-muted">
            {d.booking.location_type === "home" ? `Home in ${d.booking.city_display}` : "Temple"} · total{" "}
            {formatMoney(d.booking.total_cents)} · approved by {d.booking.approved_by}
          </p>
        </div>
      )}

      {d.intake && d.intake.service_id !== undefined && r.source !== "slot_picker" && (
        <>
          <SectionLabel>Intake Agent — extracted request</SectionLabel>
          <dl className="mb-5 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-forest-100 bg-forest-100 sm:grid-cols-2">
            <KV k="Service" v={d.service_name ?? "— not identified"} sub={d.intake.service_match_reason} />
            <KV k="Preferred dates" v={(d.intake.preferred_dates ?? []).map((x) => fmtDate(x)).join(", ") || "—"} sub={d.intake.date_notes ?? undefined} />
            <KV
              k="Time preference"
              v={
                d.intake.time_preference !== undefined
                  ? `${(d.intake.time_preference ?? "any").replace("_", " ")}${
                      d.intake.earliest_start
                        ? ` · ${fmtTime(d.intake.earliest_start)}${
                            d.intake.latest_start && d.intake.latest_start !== d.intake.earliest_start
                              ? `–${fmtTime(d.intake.latest_start)}`
                              : ""
                          }`
                        : ""
                    }`
                  : (d.intake.time_of_day ?? "—")
              }
              sub={d.intake.time_preference !== undefined ? "Window applied by code, not the model" : undefined}
            />
            <KV
              k="Location"
              v={`${d.intake.location_type ?? "—"}${d.intake.city ? ` · ${d.intake.city}` : ""}`}
              sub={d.intake.city_source === "member_profile" ? "Town taken from member profile" : undefined}
            />
            <KV k="Language" v={d.intake.language ?? "not specified"} />
            <KV k="Guests" v={d.intake.attendees != null ? String(d.intake.attendees) : "—"} />
            <KV k="Special requirements" v={(d.intake.special_requirements ?? []).join("; ") || "—"} />
            <KV k="Missing (checked in code)" v={d.missing_info.length ? d.missing_info.join(", ") : "nothing"} />
          </dl>
        </>
      )}

      {rec && (
        <>
          <SectionLabel>
            {r.source === "slot_picker" ? "Requested slot (rules engine)" : "Scheduling Agent — recommended options"}
          </SectionLabel>
          {rec.notes_for_admin && (
            <p className="mb-3 text-[0.84rem] leading-relaxed text-charcoal">
              <span className="font-medium text-forest-800">Notes for staff: </span>
              {rec.notes_for_admin}
            </p>
          )}
          {rec.options.length === 0 && (
            <EmptyState>No option passed the scheduling rules. Use "Edit &amp; approve" or ask the member.</EmptyState>
          )}
          <div className="mb-3 space-y-3">
            {rec.options.map((o, i) => (
              <div key={i} className="rounded-xl border border-forest-100 bg-white p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-[0.95rem] font-semibold text-charcoal">
                      Option {i + 1}: {o.date && fmtDate(o.date)} · {o.start_time && fmtTime(o.start_time)}–
                      {o.end_time && fmtTime(o.end_time)}
                    </p>
                    <p className="text-[0.8rem] text-charcoal-muted">
                      {o.priest_name} · {o.location_type === "home" ? `Home, ${o.city}` : "Temple"}
                      {o.language ? ` · ${o.language}` : ""}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[1rem] font-semibold text-forest-700">{formatMoney(o.total_cents ?? 0)}</p>
                    <p className="text-[0.72rem] text-charcoal-muted">
                      base {formatMoney(o.base_price_cents ?? 0)} + travel {formatMoney(o.travel_fee_cents ?? 0)}
                    </p>
                  </div>
                </div>
                {o.rationale && <p className="mt-2 text-[0.8rem] italic text-charcoal-muted">{o.rationale}</p>}
                <ul className="mt-2 space-y-0.5">
                  {o.evidence.map((e) => (
                    <li key={e} className="text-[0.78rem] text-charcoal">
                      <span className="text-forest-600">✓</span> {e}
                    </li>
                  ))}
                  {o.warnings.map((w) => (
                    <li key={w} className="text-[0.78rem] text-terracotta-600">
                      ! {w}
                    </li>
                  ))}
                </ul>
                {canDecide && (
                  <div className="mt-3">
                    <Button size="sm" disabled={busy} onClick={() => approveOption(i)}>
                      Approve option {i + 1}
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
          {rec.dropped_options.length > 0 && (
            <div className="mb-3 rounded-xl border border-dashed border-terracotta-100 px-4 py-3">
              <p className="text-[0.78rem] font-medium text-terracotta-600">
                Dropped by the rules engine ({rec.dropped_options.length}) — the agent proposed these but they failed
                re-verification:
              </p>
              {rec.dropped_options.map((o, i) => (
                <p key={i} className="mt-1 text-[0.76rem] text-charcoal-muted">
                  {o.priest_name ?? o.priest_id} {o.date} {o.start_time}: {o.problems.join(" ")}
                </p>
              ))}
            </div>
          )}
          {rec.outside_time_preference && (
            <p className="mb-2 text-[0.78rem] text-terracotta-600">
              No valid slot matched the member's requested time; these are the closest alternatives.
            </p>
          )}
          <p className="mb-5 text-[0.72rem] text-charcoal-muted">
            Verified by: {rec.verified_by}
            {rec.profile ? ` · agent profile: ${rec.profile}` : ""}
          </p>
        </>
      )}

      {canDecide && (
        <div className="mb-6 rounded-2xl border border-forest-200 bg-ivory-200/60 p-4">
          <SectionLabel>Decide</SectionLabel>
          <Field label="Note for the record" hint="Optional; saved with the approval.">
            <input className={inputClass} value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
          </Field>

          {editing ? (
            <EditApprove
              requestId={id}
              intake={d.intake}
              initial={rec?.options[0]}
              adminName={adminName}
              note={note}
              busy={busy}
              onApprove={(fn) => act(fn, "Approved edited slot — booking confirmed and saved.")}
              onCancel={() => setEditing(false)}
            />
          ) : (
            <Button variant="secondary" size="sm" onClick={() => setEditing(true)}>
              Edit &amp; approve a different slot
            </Button>
          )}

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div>
              <Field label="Ask the member for information">
                <textarea
                  className={inputClass}
                  rows={2}
                  maxLength={600}
                  value={infoMsg}
                  onChange={(e) => setInfoMsg(e.target.value)}
                  placeholder="e.g. Could you share the town of the new home?"
                />
              </Field>
              <Button
                size="sm"
                variant="secondary"
                disabled={busy || infoMsg.trim().length < 3}
                onClick={() =>
                  act(
                    () => api.adminPost(`/requests/${id}/needs-info`, { admin_name: adminName, message: infoMsg }),
                    "Sent back to the member as Needs information.",
                  )
                }
              >
                Mark needs information
              </Button>
            </div>
            <div>
              <Field label="Reject with a reason">
                <textarea
                  className={inputClass}
                  rows={2}
                  maxLength={600}
                  value={rejectMsg}
                  onChange={(e) => setRejectMsg(e.target.value)}
                  placeholder="e.g. The hall is reserved that weekend."
                />
              </Field>
              <Button
                size="sm"
                variant="danger"
                disabled={busy || rejectMsg.trim().length < 3}
                onClick={() =>
                  act(
                    () => api.adminPost(`/requests/${id}/reject`, { admin_name: adminName, message: rejectMsg }),
                    "Request rejected.",
                  )
                }
              >
                Reject request
              </Button>
            </div>
          </div>
        </div>
      )}

      {r.member_message && (
        <>
          <SectionLabel>What the member currently sees</SectionLabel>
          <p className="mb-5 text-[0.84rem] leading-relaxed text-charcoal">{r.member_message}</p>
        </>
      )}

      {d.agent_runs.length > 0 && (
        <>
          <SectionLabel>Agent trace · {usd(totalCost)} total</SectionLabel>
          <div className="mb-5 space-y-2">
            {d.agent_runs.map((run) => (
              <details key={run.id} className="rounded-xl border border-forest-100 bg-white px-4 py-3">
                <summary className="cursor-pointer text-[0.82rem] text-charcoal">
                  <span className="font-semibold capitalize text-forest-800">{run.agent} agent</span> ·{" "}
                  {run.status === "ok" ? "ok" : <span className="text-terracotta-600">{run.status}</span>} ·{" "}
                  {run.response_model ?? run.model} · {((run.latency_ms ?? 0) / 1000).toFixed(1)}s · in{" "}
                  {num(run.input_tokens)} (cached {num(run.cached_input_tokens)}) · out {num(run.output_tokens)} ·{" "}
                  {run.tool_calls} tool calls · {usd(run.cost_usd)}
                </summary>
                {run.error && <p className="mt-2 text-[0.78rem] text-terracotta-600">{run.error}</p>}
                <ol className="mt-2 space-y-1.5">
                  {run.tool_call_log?.map((t, i) => (
                    <li key={i} className="text-[0.76rem]">
                      <span className="font-mono font-medium text-forest-800">{t.tool_name}</span>
                      <span className="font-mono text-charcoal-muted">({JSON.stringify(t.args)})</span>
                      <span className="text-charcoal-muted"> · {t.duration_ms} ms</span>
                      <p className="mt-0.5 break-all font-mono text-[0.7rem] text-charcoal-muted">→ {t.result_summary}</p>
                    </li>
                  ))}
                </ol>
              </details>
            ))}
          </div>
        </>
      )}

      {(d.approvals.length > 0 || d.audit.length > 0) && (
        <>
          <SectionLabel>Audit trail</SectionLabel>
          <ul className="space-y-1">
            {d.audit.map((a) => (
              <li key={a.id} className="text-[0.76rem] text-charcoal-muted">
                <span className="text-charcoal">{fmtTimestamp(a.ts)}</span> · {a.actor} ·{" "}
                <span className="font-medium text-forest-800">{a.action}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}

function KV({ k, v, sub }: { k: string; v: string; sub?: string }) {
  return (
    <div className="bg-white px-3.5 py-2.5">
      <dt className="text-[0.7rem] font-medium uppercase tracking-[0.1em] text-charcoal-muted">{k}</dt>
      <dd className="mt-0.5 text-[0.84rem] text-charcoal">{v}</dd>
      {sub && <dd className="mt-0.5 text-[0.72rem] italic text-charcoal-muted">{sub}</dd>}
    </div>
  );
}

function EditApprove({
  requestId,
  intake,
  initial,
  adminName,
  note,
  busy,
  onApprove,
  onCancel,
}: {
  requestId: string;
  intake: Intake | null;
  initial?: SlotCheck;
  adminName: string;
  note: string;
  busy: boolean;
  onApprove: (fn: () => Promise<unknown>) => void;
  onCancel: () => void;
}) {
  const [ref, setRef] = useState<Reference | null>(null);
  const [serviceId, setServiceId] = useState(initial?.service_id ?? intake?.service_id ?? "");
  const [priestId, setPriestId] = useState(initial?.priest_id ?? "");
  const [date, setDate] = useState(initial?.date ?? intake?.preferred_dates?.[0] ?? "");
  const [time, setTime] = useState(initial?.start_time ?? "");
  const [chosenLoc, setLoc] = useState<"temple" | "home">(
    (initial?.location_type ?? (intake?.location_type as "temple" | "home" | null) ?? "temple") as "temple" | "home",
  );
  const [city, setCity] = useState(initial?.city ?? intake?.city ?? "");
  const [language, setLanguage] = useState(initial?.language ?? intake?.language ?? "");
  const [check, setCheck] = useState<SlotCheck | null>(null);
  const [checkedKey, setCheckedKey] = useState("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.adminGet<Reference>("/reference").then(setRef).catch((e) => setErr(e.message));
  }, []);

  const svc = ref?.services.find((s) => s.id === serviceId);
  const priests = useMemo(
    () => ref?.priests.filter((p) => !serviceId || p.qualifications.includes(serviceId)) ?? [],
    [ref, serviceId],
  );
  // Services performed in only one place force the location.
  const loc = svc && svc.location_mode !== "either" ? svc.location_mode : chosenLoc;

  const slot = {
    service_id: serviceId,
    priest_id: priestId,
    date,
    start_time: time,
    location_type: loc,
    city: loc === "home" ? city || null : null,
    language: language || null,
  };
  const key = JSON.stringify(slot);
  const complete = serviceId && priestId && /^\d{4}-\d{2}-\d{2}$/.test(date) && /^\d{2}:\d{2}$/.test(time);

  const runCheck = async () => {
    setErr(null);
    try {
      const c = await api.adminPost<SlotCheck>("/check-slot", slot);
      setCheck(c);
      setCheckedKey(key);
    } catch (e) {
      setErr((e as Error).message);
    }
  };

  const timeOptions = svc?.slot_times ?? Array.from({ length: 29 }, (_, i) => {
    const m = 6 * 60 + 30 + i * 30;
    return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
  });

  return (
    <div className="rounded-xl border border-forest-100 bg-white p-4">
      <div className="grid gap-x-3 sm:grid-cols-2">
        <Field label="Service">
          <select className={inputClass} value={serviceId} onChange={(e) => setServiceId(e.target.value)}>
            <option value="">Choose…</option>
            {ref?.services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Priest (qualified only)">
          <select className={inputClass} value={priestId} onChange={(e) => setPriestId(e.target.value)}>
            <option value="">Choose…</option>
            {priests.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {p.languages.join(", ")}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Date">
          <input type="date" className={inputClass} value={date} onChange={(e) => setDate(e.target.value)} />
        </Field>
        <Field label="Start time">
          <select className={inputClass} value={time} onChange={(e) => setTime(e.target.value)}>
            <option value="">Choose…</option>
            {timeOptions.map((t) => (
              <option key={t} value={t}>
                {fmtTime(t)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Location">
          <select
            className={inputClass}
            value={loc}
            disabled={!!svc && svc.location_mode !== "either"}
            onChange={(e) => setLoc(e.target.value as "temple" | "home")}
          >
            <option value="temple">Temple</option>
            <option value="home">Member's home</option>
          </select>
        </Field>
        {loc === "home" ? (
          <Field label="Town">
            <select className={inputClass} value={city} onChange={(e) => setCity(e.target.value)}>
              <option value="">Choose…</option>
              {ref?.towns.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </Field>
        ) : (
          <Field label="Language" hint="Optional">
            <input className={inputClass} value={language} maxLength={30} onChange={(e) => setLanguage(e.target.value)} />
          </Field>
        )}
      </div>

      {check && checkedKey === key && (
        <div
          className={`mb-3 rounded-xl border px-3.5 py-2.5 text-[0.78rem] ${
            check.ok ? "border-forest-200 bg-forest-50" : "border-terracotta-100 bg-terracotta-100/50"
          }`}
        >
          <p className={`font-medium ${check.ok ? "text-forest-800" : "text-terracotta-600"}`}>
            {check.ok
              ? `Passes every rule · ${formatMoney(check.total_cents ?? 0)} (travel ${formatMoney(check.travel_fee_cents ?? 0)})`
              : "Does not pass the scheduling rules"}
          </p>
          {check.problems.map((p) => (
            <p key={p} className="text-terracotta-600">
              ✕ {p}
            </p>
          ))}
          {check.warnings.map((w) => (
            <p key={w} className="text-terracotta-600">
              ! {w}
            </p>
          ))}
        </div>
      )}
      {err && <p className="mb-3 text-[0.8rem] text-terracotta-600">{err}</p>}

      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" disabled={!complete} onClick={runCheck}>
          Check availability
        </Button>
        <Button
          size="sm"
          disabled={busy || !check?.ok || checkedKey !== key}
          onClick={() =>
            onApprove(() =>
              api.adminPost(`/requests/${requestId}/approve`, { admin_name: adminName, slot, note: note || null }),
            )
          }
        >
          Approve this slot
        </Button>
        <Button size="sm" variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
      <p className="mt-2 text-[0.72rem] text-charcoal-muted">
        The server re-checks every rule inside a database transaction when you approve.
      </p>
    </div>
  );
}

/* ================= bookings ================= */

function BookingsTab({ adminName, onChange }: { adminName: string; onChange: () => void }) {
  const [rows, setRows] = useState<ApiBooking[]>([]);
  const [cancelling, setCancelling] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const load = useCallback(() => {
    api.adminGet<ApiBooking[]>("/bookings").then(setRows).catch((e) => setMsg(e.message));
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  const shown = showAll ? rows : rows.filter((b) => b.status === "confirmed");

  const cancel = async (id: string) => {
    try {
      await api.adminPost(`/bookings/${id}/cancel`, { admin_name: adminName, reason });
      setMsg(`Booking ${id} cancelled; the slot is free again.`);
      setCancelling(null);
      setReason("");
      load();
      onChange();
    } catch (e) {
      setMsg((e as Error).message);
    }
  };

  return (
    <div>
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[0.84rem] text-charcoal-muted">
          {shown.length} {showAll ? "bookings" : "confirmed bookings"} · stored in SQLite
        </p>
        <Button size="sm" variant="ghost" onClick={() => setShowAll((v) => !v)}>
          {showAll ? "Show confirmed only" : "Show cancelled too"}
        </Button>
      </div>
      {msg && <p className="mb-3 text-[0.82rem] text-forest-800">{msg}</p>}
      <Card className="overflow-x-auto">
        <table className="w-full min-w-[820px] text-left text-[0.8rem]">
          <thead className="border-b border-forest-100 text-[0.7rem] uppercase tracking-[0.1em] text-charcoal-muted">
            <tr>
              <th className="px-4 py-2.5">When</th>
              <th className="px-4 py-2.5">Service</th>
              <th className="px-4 py-2.5">Member</th>
              <th className="px-4 py-2.5">Priest</th>
              <th className="px-4 py-2.5">Where</th>
              <th className="px-4 py-2.5">Total</th>
              <th className="px-4 py-2.5">Status</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-forest-100">
            {shown.map((b) => (
              <tr key={b.id} className="align-top">
                <td className="px-4 py-2.5 text-charcoal">
                  {fmtDate(b.date, { weekday: "short", month: "short", day: "numeric" })}
                  <br />
                  <span className="text-charcoal-muted">
                    {fmtTime(b.start_time)}–{fmtTime(b.end_time)}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-charcoal">
                  {b.service_name}
                  <br />
                  <span className="text-[0.7rem] text-charcoal-muted">{b.request_id ? "via request" : "seed data"}</span>
                </td>
                <td className="px-4 py-2.5">{b.member_name}</td>
                <td className="px-4 py-2.5">{b.priest_name}</td>
                <td className="px-4 py-2.5">{b.location_type === "home" ? `Home · ${b.city_display}` : "Temple"}</td>
                <td className="px-4 py-2.5 font-medium text-forest-700">{formatMoney(b.total_cents)}</td>
                <td className="px-4 py-2.5">
                  <Badge tone={b.status === "confirmed" ? "green" : "muted"}>{b.status}</Badge>
                </td>
                <td className="px-4 py-2.5 text-right">
                  {b.status === "confirmed" &&
                    (cancelling === b.id ? (
                      <div className="flex min-w-[220px] flex-col gap-1.5">
                        <input
                          className={inputClass}
                          placeholder="Reason"
                          value={reason}
                          maxLength={300}
                          onChange={(e) => setReason(e.target.value)}
                        />
                        <div className="flex justify-end gap-1.5">
                          <Button size="sm" variant="ghost" onClick={() => setCancelling(null)}>
                            Keep
                          </Button>
                          <Button size="sm" variant="danger" disabled={reason.trim().length < 3} onClick={() => cancel(b.id)}>
                            Confirm cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <Button size="sm" variant="danger" onClick={() => setCancelling(b.id)}>
                        Cancel
                      </Button>
                    ))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

/* ================= agent runs ================= */

interface RunsPayload {
  runs: AgentRun[];
  totals: Record<string, number>;
  pricing: Record<string, unknown>;
}

function RunsTab() {
  const [data, setData] = useState<RunsPayload | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.adminGet<RunsPayload>("/agent-runs").then(setData).catch((e) => setErr(e.message));
  }, []);

  const download = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "serve_agent_runs.json";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  if (err) return <EmptyState>{err}</EmptyState>;
  if (!data) return <EmptyState>Loading…</EmptyState>;
  const t = data.totals;
  const price = data.pricing["gpt-6-luna"] as Record<string, number> | undefined;

  return (
    <div>
      <div className="mb-4 grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-forest-100 bg-forest-100 sm:grid-cols-3 lg:grid-cols-6">
        <Metric label="Agent runs" value={t.runs} />
        <Metric label="Model requests" value={num(t.model_requests)} />
        <Metric label="Input tokens" value={num(t.input_tokens)} />
        <Metric label="Cached input tokens" value={num(t.cached_input_tokens)} />
        <Metric label="Output tokens" value={num(t.output_tokens)} />
        <Metric label="Measured cost" value={usd(t.cost_usd, 5)} />
      </div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-[0.76rem] text-charcoal-muted">
          Token counts are the API's own usage numbers. Cost uses{" "}
          {price
            ? `$${price.input_per_1m}/1M input, $${price.cached_input_per_1m}/1M cached input, $${price.cache_write_per_1m}/1M cache write, $${price.output_per_1m}/1M output`
            : "prices.json"}{" "}
          ({String(data.pricing.source ?? "")}).
        </p>
        <Button size="sm" variant="secondary" onClick={download}>
          Download JSON
        </Button>
      </div>
      <Card className="overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-[0.78rem]">
          <thead className="border-b border-forest-100 text-[0.68rem] uppercase tracking-[0.1em] text-charcoal-muted">
            <tr>
              <th className="px-3 py-2.5">Time</th>
              <th className="px-3 py-2.5">Agent</th>
              <th className="px-3 py-2.5">Request</th>
              <th className="px-3 py-2.5">Model (returned)</th>
              <th className="px-3 py-2.5">Status</th>
              <th className="px-3 py-2.5 text-right">Latency</th>
              <th className="px-3 py-2.5 text-right">Requests</th>
              <th className="px-3 py-2.5 text-right">Input</th>
              <th className="px-3 py-2.5 text-right">Cached</th>
              <th className="px-3 py-2.5 text-right">Output</th>
              <th className="px-3 py-2.5 text-right">Tools</th>
              <th className="px-3 py-2.5 text-right">Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-forest-100">
            {data.runs.map((r) => (
              <tr key={r.id}>
                <td className="px-3 py-2">{fmtTimestamp(r.started_at)}</td>
                <td className="px-3 py-2 capitalize">{r.agent}</td>
                <td className="px-3 py-2 font-mono text-[0.7rem]">{r.request_id}</td>
                <td className="px-3 py-2">{r.response_model ?? r.model}</td>
                <td className="px-3 py-2">
                  {r.status === "ok" ? (
                    <Badge tone="green">ok</Badge>
                  ) : (
                    <span title={r.error ?? ""}>
                      <Badge tone="terracotta">{r.status}</Badge>
                    </span>
                  )}
                </td>
                <td className="px-3 py-2 text-right">{((r.latency_ms ?? 0) / 1000).toFixed(1)}s</td>
                <td className="px-3 py-2 text-right">{r.model_requests}</td>
                <td className="px-3 py-2 text-right">{num(r.input_tokens)}</td>
                <td className="px-3 py-2 text-right">{num(r.cached_input_tokens)}</td>
                <td className="px-3 py-2 text-right">{num(r.output_tokens)}</td>
                <td className="px-3 py-2 text-right">{r.tool_calls}</td>
                <td className="px-3 py-2 text-right font-medium text-forest-700">{usd(r.cost_usd, 6)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

/* ================= audit ================= */

function AuditTab() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    api.adminGet<AuditRow[]>("/audit?limit=300").then(setRows).catch((e) => setErr(e.message));
  }, []);
  if (err) return <EmptyState>{err}</EmptyState>;
  return (
    <Card className="overflow-x-auto">
      <table className="w-full min-w-[860px] text-left text-[0.78rem]">
        <thead className="border-b border-forest-100 text-[0.68rem] uppercase tracking-[0.1em] text-charcoal-muted">
          <tr>
            <th className="px-3 py-2.5">Time</th>
            <th className="px-3 py-2.5">Actor</th>
            <th className="px-3 py-2.5">Action</th>
            <th className="px-3 py-2.5">Request / booking</th>
            <th className="px-3 py-2.5">Details</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-forest-100">
          {rows.map((a) => (
            <tr key={a.id} className="align-top">
              <td className="whitespace-nowrap px-3 py-2">{fmtTimestamp(a.ts)}</td>
              <td className="px-3 py-2">{a.actor}</td>
              <td className="px-3 py-2 font-medium text-forest-800">{a.action}</td>
              <td className="px-3 py-2 font-mono text-[0.7rem]">
                {a.request_id}
                {a.booking_id ? ` / ${a.booking_id}` : ""}
              </td>
              <td className="max-w-[420px] break-all px-3 py-2 font-mono text-[0.68rem] text-charcoal-muted">
                {a.details_json && a.details_json.length > 220 ? `${a.details_json.slice(0, 220)}…` : a.details_json}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
