/** Member-side service request UI: describe-it-in-words sheet and live status. */

import { useEffect, useState } from "react";
import { useOrg } from "../store";
import { fmtDate, fmtTime } from "../api";
import { STATUS_LABEL, STATUS_TONE, formatMoney } from "../types";
import type { MemberRequest } from "../types";
import { Badge, Button, Card, DemoNote, Field, SectionLabel, Sheet, inputClass } from "./ui";

const EXAMPLES = [
  "We just moved into a house in Hamden and would like a griha pravesh on a Saturday morning next month, in Telugu if possible.",
  "Could we have a Satyanarayan puja at the temple next Sunday? About 20 family members will come.",
  "Baby naming ceremony for our daughter in two weeks, preferably in Gujarati.",
];

/** Live status for one request. Polls while the agents are working. */
export function RequestStatus({ requestId }: { requestId: string }) {
  const { requests, fetchRequest, replyToRequest } = useOrg();
  const req = requests.find((r) => r.id === requestId);
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const processing = req?.status === "processing";

  useEffect(() => {
    if (!processing) return;
    setElapsed(0);
    const tick = setInterval(() => setElapsed((e) => e + 1), 1000);
    const poll = setInterval(() => {
      fetchRequest(requestId).catch((e) => setError(e.message));
    }, 2500);
    return () => {
      clearInterval(tick);
      clearInterval(poll);
    };
  }, [processing, requestId, fetchRequest]);

  if (!req) return null;

  const sendReply = async () => {
    setSending(true);
    setError(null);
    try {
      await replyToRequest(req.id, reply);
      setReply("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="animate-rise">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-[0.95rem] font-semibold text-forest-800">
          {req.service_name ?? "Service request"}
        </p>
        <Badge tone={STATUS_TONE[req.status]}>{STATUS_LABEL[req.status]}</Badge>
      </div>

      <Card className="mb-4 px-4 py-3">
        <p className="text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-charcoal-muted">
          Your request
        </p>
        <p className="mt-1 whitespace-pre-line text-[0.84rem] leading-relaxed text-charcoal">
          {req.raw_text}
        </p>
      </Card>

      {processing ? (
        <Card className="mb-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <span className="h-4 w-4 flex-none animate-spin rounded-full border-2 border-forest-200 border-t-forest-700" />
            <div>
              <p className="text-[0.86rem] font-medium text-forest-800">
                {elapsed < 8 ? "Reading your request…" : "Checking priests, languages and the calendar…"}
              </p>
              <p className="text-[0.74rem] text-charcoal-muted">
                Intake Agent → Scheduling Agent · {elapsed}s
              </p>
            </div>
          </div>
        </Card>
      ) : (
        req.member_message && (
          <p className="mb-4 text-[0.88rem] leading-relaxed text-charcoal">{req.member_message}</p>
        )
      )}

      {req.proposed_options.length > 0 && (
        <>
          <SectionLabel>Proposed times — awaiting temple approval</SectionLabel>
          <div className="mb-4 space-y-2">
            {req.proposed_options.map((o, i) => (
              <Card key={i} className="px-4 py-3">
                <p className="text-[0.86rem] font-semibold text-charcoal">
                  {fmtDate(o.date)} · {fmtTime(o.start_time)}
                </p>
                <p className="text-[0.76rem] text-charcoal-muted">
                  {o.priest_name} · {o.location_type === "home" ? `At home${o.city ? `, ${o.city}` : ""}` : "At the temple"}
                  {" · "}
                  {formatMoney(o.total_cents)}
                  {o.travel_fee_cents > 0 ? ` incl. ${formatMoney(o.travel_fee_cents)} travel` : ""}
                </p>
              </Card>
            ))}
          </div>
        </>
      )}

      {req.booking && (
        <Card className="mb-4 border-forest-200 bg-forest-50 px-4 py-3">
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-forest-700">
            Booking {req.booking.status}
          </p>
          <p className="mt-1 text-[0.9rem] font-semibold text-forest-800">
            {fmtDate(req.booking.date)} · {fmtTime(req.booking.start_time)}–{fmtTime(req.booking.end_time)}
          </p>
          <p className="text-[0.78rem] text-charcoal-muted">
            {req.booking.priest_name} ·{" "}
            {req.booking.location_type === "home" ? `Home, ${req.booking.city_display}` : "Temple"} ·{" "}
            {formatMoney(req.booking.total_cents)}
          </p>
        </Card>
      )}

      {req.status === "needs_info" && (
        <div className="mb-4">
          <Field label="Your reply">
            <textarea
              className={inputClass}
              rows={3}
              maxLength={800}
              value={reply}
              onChange={(e) => setReply(e.target.value)}
              placeholder="Add the missing details here"
            />
          </Field>
          <Button full disabled={reply.trim().length < 2 || sending} onClick={sendReply}>
            {sending ? "Sending…" : "Send reply"}
          </Button>
        </div>
      )}

      {error && <p className="mb-3 text-[0.8rem] text-terracotta-600">{error}</p>}

      <DemoNote>
        Requests are saved on the SERVE server. A temple administrator must approve before anything is
        booked. No payment is taken and no email is sent in this prototype.
      </DemoNote>
    </div>
  );
}

/** "Describe what you need" — free-text request handled by the two agents. */
export function AskSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { submitAIRequest, backend } = useOrg();
  const [text, setText] = useState("");
  const [submitted, setSubmitted] = useState<MemberRequest | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const close = () => {
    onClose();
    setTimeout(() => {
      setText("");
      setSubmitted(null);
      setError(null);
    }, 200);
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      setSubmitted(await submitAIRequest(text));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Sheet
      open={open}
      onClose={close}
      title={submitted ? "Request status" : "Describe what you need"}
      footer={
        submitted ? (
          <Button full onClick={close}>
            Done
          </Button>
        ) : (
          <Button full disabled={text.trim().length < 10 || busy || backend !== "ready"} onClick={submit}>
            {busy ? "Sending…" : "Send request"}
          </Button>
        )
      }
    >
      {submitted ? (
        <RequestStatus requestId={submitted.id} />
      ) : (
        <>
          <p className="mb-4 text-[0.87rem] leading-relaxed text-charcoal-muted">
            Tell us the occasion, when, where, and any language or family needs. SERVE's assistant
            checks which priests are qualified and free, then the temple office confirms.
          </p>
          <Field label="Your request" hint={`${text.length}/1500`}>
            <textarea
              className={inputClass}
              rows={5}
              maxLength={1500}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. A housewarming puja at our new home in Hamden next month…"
            />
          </Field>
          <p className="mb-2 text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-charcoal-muted">
            Try an example
          </p>
          <div className="mb-4 space-y-1.5">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                onClick={() => setText(ex)}
                className="block w-full rounded-xl border border-forest-100 bg-white px-3 py-2 text-left text-[0.78rem] leading-relaxed text-charcoal-muted transition hover:border-forest-200"
              >
                {ex}
              </button>
            ))}
          </div>
          {backend === "offline" && (
            <p className="mb-3 text-[0.8rem] text-terracotta-600">
              The SERVE backend isn't reachable, so requests can't be sent right now.
            </p>
          )}
          {error && <p className="mb-3 text-[0.8rem] text-terracotta-600">{error}</p>}
          <DemoNote>
            Uses AI (gpt-6-luna) to read your request and check real availability in the temple's
            demo calendar. Nothing is booked until a temple administrator approves it.
          </DemoNote>
        </>
      )}
    </Sheet>
  );
}

/** Sheet wrapper to reopen a request's status from the profile. */
export function RequestSheet({ requestId, onClose }: { requestId: string | null; onClose: () => void }) {
  return (
    <Sheet
      open={!!requestId}
      onClose={onClose}
      title="Request status"
      footer={
        <Button full onClick={onClose}>
          Close
        </Button>
      }
    >
      {requestId && <RequestStatus requestId={requestId} />}
    </Sheet>
  );
}
