/** Member portal — phone-shaped on desktop, full-bleed on mobile. */

import { useState } from "react";
import { Link } from "react-router-dom";
import { useOrg } from "../store";
import { fmtDate, fmtTime } from "../api";
import { STATUS_LABEL, STATUS_TONE, formatMoney } from "../types";
import { AskSheet, RequestSheet, RequestStatus } from "../components/requests";
import type { Event, Service, VolunteerOpportunity } from "../types";
import {
  Badge,
  Button,
  Card,
  DemoNote,
  DoneState,
  EmptyState,
  Field,
  Progress,
  SectionLabel,
  Segmented,
  Sheet,
  Toggle,
  Wordmark,
  inputClass,
} from "../components/ui";

type Tab = "home" | "events" | "services" | "volunteer" | "profile";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "home", label: "Home", icon: "⌂" },
  { id: "events", label: "Events", icon: "◷" },
  { id: "services", label: "Services", icon: "✧" },
  { id: "volunteer", label: "Volunteer", icon: "♡" },
  { id: "profile", label: "Profile", icon: "◉" },
];

export default function Portal() {
  const [tab, setTab] = useState<Tab>("home");
  const [donateOpen, setDonateOpen] = useState(false);
  const [service, setService] = useState<Service | null>(null);
  const [event, setEvent] = useState<Event | null>(null);
  const [opportunity, setOpportunity] = useState<VolunteerOpportunity | null>(null);
  const [infoOpen, setInfoOpen] = useState(false);
  const [askOpen, setAskOpen] = useState(false);
  const [openRequest, setOpenRequest] = useState<string | null>(null);

  const org = useOrg();

  const go = (t: Tab) => setTab(t);

  return (
    <div className="min-h-screen bg-forest-800/5 sm:bg-forest-800/10">
      {/* desktop chrome */}
      <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4">
        <Link to="/" aria-label="SERVE home">
          <Wordmark />
        </Link>
        <div className="flex items-center gap-3">
          <Link
            to="/admin"
            className="text-[0.8rem] font-medium text-charcoal-muted transition hover:text-forest-800"
          >
            Admin dashboard →
          </Link>
          <Badge tone="gold">Demo</Badge>
        </div>
      </div>

      {org.backend === "offline" && (
        <div className="mx-auto mb-3 max-w-md px-5">
          <DemoNote>
            The SERVE backend isn't running, so service requests are unavailable and events show
            sample dates. Start it with the command in the README.
          </DemoNote>
        </div>
      )}

      {/* phone frame */}
      <div className="mx-auto w-full max-w-md px-0 pb-0 sm:px-5 sm:pb-10">
        <div className="relative flex h-[100dvh] flex-col overflow-hidden bg-ivory sm:h-[760px] sm:rounded-[2rem] sm:border sm:border-forest-200 sm:shadow-[0_30px_70px_-28px_rgba(31,58,46,0.45)]">
          <div className="scroll-area flex-1 overflow-y-auto pb-24">
            {tab === "home" && (
              <Home
                onDonate={() => setDonateOpen(true)}
                onService={setService}
                onEvent={setEvent}
                onOpportunity={setOpportunity}
                onInfo={() => setInfoOpen(true)}
                go={go}
              />
            )}
            {tab === "events" && <Events onEvent={setEvent} />}
            {tab === "services" && <Services onService={setService} onAsk={() => setAskOpen(true)} />}
            {tab === "volunteer" && <Volunteer onOpportunity={setOpportunity} />}
            {tab === "profile" && (
              <Profile onInfo={() => setInfoOpen(true)} onRequest={setOpenRequest} />
            )}
          </div>

          {/* bottom nav */}
          <nav
            className="absolute inset-x-0 bottom-0 flex border-t border-forest-100 bg-white/95 backdrop-blur"
            aria-label="Main"
          >
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                aria-current={tab === t.id ? "page" : undefined}
                className={`flex flex-1 flex-col items-center gap-0.5 py-2.5 pb-[max(0.6rem,env(safe-area-inset-bottom))] text-[0.62rem] font-medium transition ${
                  tab === t.id ? "text-forest-800" : "text-charcoal-muted"
                }`}
              >
                <span aria-hidden="true" className="text-[1.05rem] leading-none">
                  {t.icon}
                </span>
                {t.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <DonateSheet open={donateOpen} onClose={() => setDonateOpen(false)} />
      <ServiceSheet service={service} onClose={() => setService(null)} />
      <EventSheet
        event={event}
        onClose={() => setEvent(null)}
        onVolunteer={(o) => {
          setEvent(null);
          setOpportunity(o);
        }}
      />
      <VolunteerSheet opportunity={opportunity} onClose={() => setOpportunity(null)} />
      <InfoSheet open={infoOpen} onClose={() => setInfoOpen(false)} org={org.organization} />
      <AskSheet open={askOpen} onClose={() => setAskOpen(false)} />
      <RequestSheet requestId={openRequest} onClose={() => setOpenRequest(null)} />
    </div>
  );
}

/* ================= home ================= */

function Home({
  onDonate,
  onService,
  onEvent,
  onOpportunity,
  onInfo,
  go,
}: {
  onDonate: () => void;
  onService: (s: Service) => void;
  onEvent: (e: Event) => void;
  onOpportunity: (o: VolunteerOpportunity) => void;
  onInfo: () => void;
  go: (t: Tab) => void;
}) {
  const { organization, member, events, services, opportunities, announcements } = useOrg();

  const actions = [
    { label: "Donate", icon: "♥", onClick: onDonate },
    { label: "Book a Service", icon: "✧", onClick: () => go("services") },
    { label: "Events", icon: "◷", onClick: () => go("events") },
    { label: "Volunteer", icon: "♡", onClick: () => go("volunteer") },
  ];

  return (
    <>
      <header
        className="px-5 pb-6 pt-10 text-ivory"
        style={{ background: organization.heroImage }}
      >
        <p className="text-[0.7rem] uppercase tracking-[0.16em] opacity-80">Welcome back</p>
        <h1 className="mt-1 text-[1.6rem] font-semibold">{organization.name}</h1>
        <p className="mt-1 text-[0.84rem] opacity-85">{organization.tagline}</p>
        <p className="mt-4 text-[0.78rem] opacity-75">Signed in as {member.name}</p>
      </header>

      <div className="grid grid-cols-4 gap-2 px-4 py-4">
        {actions.map((a) => (
          <button
            key={a.label}
            onClick={a.onClick}
            className="flex min-h-[4.6rem] flex-col items-center justify-center gap-1.5 rounded-2xl border border-forest-100 bg-white px-1 py-3 text-center transition active:scale-[0.97] hover:border-forest-200"
          >
            <span aria-hidden="true" className="text-[1.1rem] text-terracotta-500">
              {a.icon}
            </span>
            <span className="text-[0.62rem] font-medium leading-tight text-forest-800">
              {a.label}
            </span>
          </button>
        ))}
      </div>

      <div className="space-y-6 px-4 pb-6">
        <section>
          <SectionLabel>Upcoming</SectionLabel>
          <div className="space-y-2">
            {events.slice(0, 3).map((e) => (
              <button key={e.id} onClick={() => onEvent(e)} className="block w-full text-left">
                <Card className="flex items-center gap-3 p-3 transition hover:border-forest-200">
                  <div
                    className="h-12 w-12 flex-none rounded-xl"
                    style={{ background: e.image }}
                    aria-hidden="true"
                  />
                  <div className="min-w-0">
                    <p className="truncate text-[0.88rem] font-semibold text-charcoal">{e.name}</p>
                    <p className="text-[0.76rem] text-charcoal-muted">
                      {e.date} · {e.time}
                    </p>
                  </div>
                </Card>
              </button>
            ))}
          </div>
        </section>

        <section>
          <SectionLabel>Popular services</SectionLabel>
          <div className="space-y-2">
            {services
              .filter((s) => s.popular && s.enabled)
              .map((s) => (
                <button key={s.id} onClick={() => onService(s)} className="block w-full text-left">
                  <Card className="flex items-center justify-between gap-3 p-3 transition hover:border-forest-200">
                    <div className="min-w-0">
                      <p className="truncate text-[0.88rem] font-semibold text-charcoal">
                        {s.name}
                      </p>
                      <p className="text-[0.76rem] text-charcoal-muted">
                        {s.scheduling === "request_based" ? "Request a date" : s.durationLabel}
                      </p>
                    </div>
                    <span className="flex-none text-[0.88rem] font-semibold text-forest-700">
                      {s.priceLabel}
                    </span>
                  </Card>
                </button>
              ))}
          </div>
        </section>

        <section>
          <SectionLabel>Volunteers needed</SectionLabel>
          <div className="space-y-2">
            {opportunities.slice(0, 3).map((o) => (
              <button
                key={o.id}
                onClick={() => onOpportunity(o)}
                className="block w-full text-left"
              >
                <Card className="p-3 transition hover:border-forest-200">
                  <div className="mb-2 flex items-baseline justify-between gap-3">
                    <p className="truncate text-[0.88rem] font-semibold text-charcoal">
                      {o.eventName} · {o.role}
                    </p>
                    <span className="flex-none text-[0.74rem] text-charcoal-muted">
                      {o.spotsFilled} of {o.spotsTotal}
                    </span>
                  </div>
                  <Progress filled={o.spotsFilled} total={o.spotsTotal} />
                </Card>
              </button>
            ))}
          </div>
        </section>

        <section>
          <SectionLabel>Latest announcement</SectionLabel>
          <Card className="p-4">
            <p className="text-[0.9rem] font-semibold leading-snug text-forest-800">
              {announcements[0].title}
            </p>
            <p className="mt-1.5 text-[0.82rem] leading-relaxed text-charcoal-muted">
              {announcements[0].body}
            </p>
            <p className="mt-2 text-[0.72rem] text-charcoal-muted">
              Posted {announcements[0].postedOn}
            </p>
          </Card>
        </section>

        <button onClick={onInfo} className="block w-full text-left">
          <Card className="flex items-center justify-between p-4 transition hover:border-forest-200">
            <span className="text-[0.88rem] font-medium text-forest-800">
              Hours, directions & contact
            </span>
            <span aria-hidden="true" className="text-charcoal-muted">
              →
            </span>
          </Card>
        </button>
      </div>
    </>
  );
}

/* ================= events ================= */

function Events({ onEvent }: { onEvent: (e: Event) => void }) {
  const { events, myRsvpEventIds } = useOrg();
  const [view, setView] = useState<"list" | "calendar">("list");

  return (
    <div className="px-4 py-6">
      <h1 className="mb-4 text-[1.4rem] font-semibold text-forest-800">Events</h1>

      <div className="mb-4">
        <Segmented
          value={view}
          onChange={setView}
          options={[
            { value: "list", label: "List" },
            { value: "calendar", label: "Calendar" },
          ]}
        />
      </div>

      {view === "list" ? (
        <div className="space-y-3">
          {events.map((e) => (
            <button key={e.id} onClick={() => onEvent(e)} className="block w-full text-left">
              <Card className="overflow-hidden transition hover:border-forest-200">
                <div className="h-24 w-full" style={{ background: e.image }} aria-hidden="true" />
                <div className="p-3.5">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-[0.95rem] font-semibold text-charcoal">{e.name}</p>
                    {myRsvpEventIds.includes(e.id) && <Badge tone="green">RSVP'd</Badge>}
                  </div>
                  <p className="mt-0.5 text-[0.78rem] text-charcoal-muted">
                    {e.date} · {e.time}
                  </p>
                  <p className="mt-1.5 text-[0.82rem] leading-relaxed text-charcoal-muted">
                    {e.summary}
                  </p>
                </div>
              </Card>
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-2">
          {events.map((e) => (
            <button key={e.id} onClick={() => onEvent(e)} className="block w-full text-left">
              <Card className="flex items-center gap-3 p-3 transition hover:border-forest-200">
                <div className="w-14 flex-none rounded-xl bg-forest-50 py-2 text-center">
                  <p className="text-[0.6rem] uppercase tracking-wide text-charcoal-muted">
                    {e.date.split(",")[1]?.trim().split(" ")[0] ?? "Oct"}
                  </p>
                  <p className="text-[1.05rem] font-semibold leading-tight text-forest-800">
                    {e.date.replace(/\D+/g, "").slice(0, 2) || "—"}
                  </p>
                </div>
                <div className="min-w-0">
                  <p className="truncate text-[0.88rem] font-semibold text-charcoal">{e.name}</p>
                  <p className="text-[0.76rem] text-charcoal-muted">{e.time}</p>
                </div>
              </Card>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ================= services ================= */

function Services({ onService, onAsk }: { onService: (s: Service) => void; onAsk: () => void }) {
  const { services } = useOrg();
  const live = services.filter((s) => s.enabled);
  const categories = [...new Set(live.map((s) => s.category))];
  const [active, setActive] = useState<string>("All");

  const shown = active === "All" ? live : live.filter((s) => s.category === active);

  return (
    <div className="px-4 py-6">
      <h1 className="mb-1 text-[1.4rem] font-semibold text-forest-800">Services</h1>
      <p className="mb-4 text-[0.84rem] text-charcoal-muted">
        Browse what's offered and request a time in a few taps.
      </p>

      <button onClick={onAsk} className="mb-5 block w-full text-left">
        <Card className="overflow-hidden border-forest-200 transition hover:border-forest-400">
          <div
            className="px-4 py-4 text-ivory"
            style={{ background: "linear-gradient(140deg, #3b2f16 0%, #8e6615 60%, #c9962f 100%)" }}
          >
            <p className="text-[0.66rem] font-semibold uppercase tracking-[0.14em] text-gold-200">
              New · AI-assisted
            </p>
            <p className="mt-1 text-[1rem] font-semibold">Describe what you need</p>
            <p className="mt-1 text-[0.8rem] leading-relaxed text-ivory/85">
              "A housewarming in Hamden next month, in Telugu" — we'll find qualified, available
              priests and the office confirms.
            </p>
          </div>
        </Card>
      </button>

      <div className="scroll-area -mx-4 mb-4 flex gap-2 overflow-x-auto px-4 pb-1">
        {["All", ...categories].map((c) => (
          <button
            key={c}
            onClick={() => setActive(c)}
            className={`flex-none rounded-full border px-3.5 py-1.5 text-[0.78rem] font-medium transition ${
              active === c
                ? "border-forest-800 bg-forest-800 text-ivory"
                : "border-forest-200 bg-white text-charcoal-muted hover:border-forest-400"
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {shown.map((s) => (
          <button key={s.id} onClick={() => onService(s)} className="block w-full text-left">
            <Card className="p-3.5 transition hover:border-forest-200">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[0.93rem] font-semibold text-charcoal">{s.name}</p>
                  <p className="mt-0.5 text-[0.8rem] leading-relaxed text-charcoal-muted">
                    {s.summary}
                  </p>
                  <p className="mt-1.5 text-[0.74rem] text-charcoal-muted">{s.durationLabel}</p>
                </div>
                <span className="flex-none text-[0.9rem] font-semibold text-forest-700">
                  {s.priceLabel}
                </span>
              </div>
              {s.scheduling === "request_based" && (
                <div className="mt-2.5">
                  <Badge tone="muted">Requires scheduling</Badge>
                </div>
              )}
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ================= volunteer ================= */

function Volunteer({ onOpportunity }: { onOpportunity: (o: VolunteerOpportunity) => void }) {
  const { opportunities, volunteerSignups, member, cancelVolunteerSignup } = useOrg();
  const mine = volunteerSignups.filter((s) => s.memberId === member.id);

  const byEvent = opportunities.reduce<Record<string, VolunteerOpportunity[]>>((acc, o) => {
    (acc[o.eventName] ||= []).push(o);
    return acc;
  }, {});

  return (
    <div className="px-4 py-6">
      <h1 className="mb-1 text-[1.4rem] font-semibold text-forest-800">Volunteer</h1>
      <p className="mb-5 text-[0.84rem] text-charcoal-muted">
        Pick a shift that fits. Every role here is currently open.
      </p>

      <section className="mb-6">
        <SectionLabel>My upcoming commitments</SectionLabel>
        {mine.length === 0 ? (
          <EmptyState>You haven't signed up for a shift yet.</EmptyState>
        ) : (
          <div className="space-y-2">
            {mine.map((s) => (
              <Card key={s.id} className="flex items-center justify-between gap-3 p-3.5">
                <div className="min-w-0">
                  <p className="truncate text-[0.88rem] font-semibold text-charcoal">
                    {s.role}
                  </p>
                  <p className="text-[0.76rem] text-charcoal-muted">
                    {s.eventName} · {s.window}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => cancelVolunteerSignup(s.id)}
                >
                  Cancel
                </Button>
              </Card>
            ))}
          </div>
        )}
      </section>

      {Object.entries(byEvent).map(([eventName, roles]) => (
        <section key={eventName} className="mb-6">
          <SectionLabel>{eventName}</SectionLabel>
          <div className="space-y-2">
            {roles.map((o) => {
              const left = o.spotsTotal - o.spotsFilled;
              return (
                <button
                  key={o.id}
                  onClick={() => onOpportunity(o)}
                  className="block w-full text-left"
                >
                  <Card className="p-3.5 transition hover:border-forest-200">
                    <div className="mb-2 flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-[0.9rem] font-semibold text-charcoal">{o.role}</p>
                        <p className="text-[0.76rem] text-charcoal-muted">{o.window}</p>
                      </div>
                      <span className="flex-none text-[0.76rem] font-medium text-forest-700">
                        {left > 0 ? `${left} spot${left === 1 ? "" : "s"} left` : "Full"}
                      </span>
                    </div>
                    <Progress filled={o.spotsFilled} total={o.spotsTotal} />
                  </Card>
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}

/* ================= profile ================= */

function Profile({ onInfo, onRequest }: { onInfo: () => void; onRequest: (id: string) => void }) {
  const {
    member,
    organization,
    requests,
    serviceBookings,
    backend,
    donations,
    volunteerSignups,
    rsvps,
    toggleNotification,
    cancelRsvp,
  } = useOrg();

  const myBookings = serviceBookings.filter((b) => b.status === "confirmed");
  const myDonations = donations.filter((d) => d.memberId === member.id);
  const mySignups = volunteerSignups.filter((s) => s.memberId === member.id);
  const myRsvps = rsvps.filter((r) => r.memberId === member.id);

  return (
    <div className="px-4 py-6">
      <div className="mb-6 flex items-center gap-3.5">
        <div className="grid h-14 w-14 flex-none place-items-center rounded-full bg-forest-800 text-[1.1rem] font-semibold text-ivory">
          {member.name
            .split(" ")
            .map((p) => p[0])
            .join("")}
        </div>
        <div className="min-w-0">
          <h1 className="text-[1.25rem] font-semibold text-forest-800">{member.name}</h1>
          <p className="text-[0.82rem] text-charcoal-muted">
            {organization.name} · member since {member.joinedOn}
          </p>
        </div>
      </div>

      <section className="mb-6">
        <SectionLabel>My service requests</SectionLabel>
        {backend === "offline" ? (
          <EmptyState>Service requests load from the SERVE backend, which isn't running.</EmptyState>
        ) : requests.length === 0 ? (
          <EmptyState>No requests yet.</EmptyState>
        ) : (
          <div className="space-y-2">
            {requests.map((r) => (
              <button key={r.id} onClick={() => onRequest(r.id)} className="block w-full text-left">
                <Card className="flex items-center justify-between gap-3 p-3.5 transition hover:border-forest-200">
                  <div className="min-w-0">
                    <p className="truncate text-[0.88rem] font-semibold text-charcoal">
                      {r.service_name ?? "Service request"}
                    </p>
                    <p className="truncate text-[0.76rem] text-charcoal-muted">{r.raw_text}</p>
                  </div>
                  <Badge tone={STATUS_TONE[r.status]}>{STATUS_LABEL[r.status]}</Badge>
                </Card>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="mb-6">
        <SectionLabel>My confirmed bookings</SectionLabel>
        {myBookings.length === 0 ? (
          <EmptyState>No confirmed bookings yet.</EmptyState>
        ) : (
          <div className="space-y-2">
            {myBookings.map((b) => (
              <Card key={b.id} className="flex items-center justify-between gap-3 p-3.5">
                <div className="min-w-0">
                  <p className="truncate text-[0.88rem] font-semibold text-charcoal">
                    {b.service_name}
                  </p>
                  <p className="text-[0.76rem] text-charcoal-muted">
                    {fmtDate(b.date, { weekday: "short", month: "short", day: "numeric" })} ·{" "}
                    {fmtTime(b.start_time)} · {b.priest_name}
                  </p>
                </div>
                <Badge tone="green">confirmed</Badge>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="mb-6">
        <SectionLabel>My donations</SectionLabel>
        {myDonations.length === 0 ? (
          <EmptyState>No donations yet.</EmptyState>
        ) : (
          <div className="space-y-2">
            {myDonations.map((d) => (
              <Card key={d.id} className="flex items-center justify-between gap-3 p-3.5">
                <div className="min-w-0">
                  <p className="truncate text-[0.88rem] font-semibold text-charcoal">
                    {d.fundName}
                  </p>
                  <p className="text-[0.76rem] text-charcoal-muted">
                    {d.date} · {d.frequency === "monthly" ? "Monthly" : "One-time"}
                  </p>
                </div>
                <span className="flex-none text-[0.88rem] font-semibold text-forest-700">
                  {formatMoney(d.amountCents)}
                </span>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="mb-6">
        <SectionLabel>My volunteer commitments</SectionLabel>
        {mySignups.length === 0 ? (
          <EmptyState>No shifts booked.</EmptyState>
        ) : (
          <div className="space-y-2">
            {mySignups.map((s) => (
              <Card key={s.id} className="p-3.5">
                <p className="text-[0.88rem] font-semibold text-charcoal">{s.role}</p>
                <p className="text-[0.76rem] text-charcoal-muted">
                  {s.eventName} · {s.window}
                </p>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="mb-6">
        <SectionLabel>My event RSVPs</SectionLabel>
        {myRsvps.length === 0 ? (
          <EmptyState>No RSVPs yet.</EmptyState>
        ) : (
          <div className="space-y-2">
            {myRsvps.map((r) => (
              <Card key={r.id} className="flex items-center justify-between gap-3 p-3.5">
                <div className="min-w-0">
                  <p className="truncate text-[0.88rem] font-semibold text-charcoal">
                    {r.eventName}
                  </p>
                  <p className="text-[0.76rem] text-charcoal-muted">
                    {r.date} · {r.guests} {r.guests === 1 ? "guest" : "guests"}
                  </p>
                </div>
                <Button size="sm" variant="danger" onClick={() => cancelRsvp(r.id)}>
                  Cancel
                </Button>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="mb-6">
        <SectionLabel>Family members</SectionLabel>
        <Card className="divide-y divide-forest-100">
          {member.family.map((f) => (
            <div key={f.name} className="flex items-center justify-between px-4 py-3">
              <span className="text-[0.86rem] text-charcoal">{f.name}</span>
              <span className="text-[0.76rem] text-charcoal-muted">{f.relation}</span>
            </div>
          ))}
        </Card>
      </section>

      <section className="mb-6">
        <SectionLabel>Notification preferences</SectionLabel>
        <Card className="divide-y divide-forest-100">
          {member.notifications.map((n) => (
            <div key={n.id} className="flex items-center justify-between gap-3 px-4 py-3">
              <span className="text-[0.84rem] text-charcoal">{n.label}</span>
              <Toggle
                checked={n.enabled}
                onChange={() => toggleNotification(n.id)}
                label={n.label}
              />
            </div>
          ))}
        </Card>
      </section>

      <button onClick={onInfo} className="mb-4 block w-full text-left">
        <Card className="flex items-center justify-between p-4 transition hover:border-forest-200">
          <span className="text-[0.88rem] font-medium text-forest-800">
            About {organization.name}
          </span>
          <span aria-hidden="true" className="text-charcoal-muted">
            →
          </span>
        </Card>
      </button>

      <DemoNote>
        Prototype. Service requests and bookings are saved on the SERVE server. Donations, RSVPs,
        volunteer shifts and notification settings are sample data kept in this browser tab only.
      </DemoNote>
    </div>
  );
}

/* ================= sheets ================= */

const AMOUNTS = [2500, 5100, 10100, 25100];

function DonateSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { organization, donate } = useOrg();
  const [fund, setFund] = useState(organization.donationFunds[0].id);
  const [amount, setAmount] = useState<number | "custom">(5100);
  const [custom, setCustom] = useState("");
  const [freq, setFreq] = useState<"one_time" | "monthly">("one_time");
  const [done, setDone] = useState(false);

  const cents = amount === "custom" ? Math.round(parseFloat(custom || "0") * 100) : amount;
  const valid = cents > 0;

  const close = () => {
    onClose();
    // Reset after the sheet animates out.
    setTimeout(() => {
      setDone(false);
      setAmount(5100);
      setCustom("");
      setFreq("one_time");
      setFund(organization.donationFunds[0].id);
    }, 200);
  };

  const fundName = organization.donationFunds.find((f) => f.id === fund)?.name ?? "";

  return (
    <Sheet
      open={open}
      onClose={close}
      title={done ? "Donation preview" : "Donate"}
      footer={
        done ? (
          <Button full onClick={close}>
            Done
          </Button>
        ) : (
          <Button
            full
            disabled={!valid}
            onClick={() => {
              donate(fund, cents, freq);
              setDone(true);
            }}
          >
            Continue
          </Button>
        )
      }
    >
      {done ? (
        <DoneState
          title="This is where payment would happen."
          lines={[
            { label: "Fund", value: fundName },
            { label: "Amount", value: formatMoney(cents) },
            { label: "Frequency", value: freq === "monthly" ? "Monthly" : "One-time" },
          ]}
          note="Demo only — no payment was processed and no card was charged. The donation is shown in your profile for this browser tab only; it is not saved on the server."
        />
      ) : (
        <>
          <SectionLabel>Choose a fund</SectionLabel>
          <div className="mb-5 space-y-2">
            {organization.donationFunds.map((f) => (
              <button
                key={f.id}
                onClick={() => setFund(f.id)}
                className={`block w-full rounded-xl border px-4 py-3 text-left transition ${
                  fund === f.id
                    ? "border-forest-600 bg-forest-50"
                    : "border-forest-100 bg-white hover:border-forest-200"
                }`}
              >
                <p className="text-[0.88rem] font-semibold text-charcoal">{f.name}</p>
                <p className="text-[0.76rem] text-charcoal-muted">{f.blurb}</p>
              </button>
            ))}
          </div>

          <SectionLabel>Amount</SectionLabel>
          <div className="mb-3 grid grid-cols-4 gap-2">
            {AMOUNTS.map((a) => (
              <button
                key={a}
                onClick={() => setAmount(a)}
                className={`rounded-xl border py-2.5 text-[0.84rem] font-semibold transition ${
                  amount === a
                    ? "border-forest-600 bg-forest-800 text-ivory"
                    : "border-forest-200 bg-white text-charcoal hover:border-forest-400"
                }`}
              >
                {formatMoney(a)}
              </button>
            ))}
          </div>

          <button
            onClick={() => setAmount("custom")}
            className={`mb-3 w-full rounded-xl border py-2.5 text-[0.84rem] font-medium transition ${
              amount === "custom"
                ? "border-forest-600 bg-forest-50 text-forest-800"
                : "border-forest-200 bg-white text-charcoal-muted hover:border-forest-400"
            }`}
          >
            Custom amount
          </button>

          {amount === "custom" && (
            <Field label="Enter an amount (USD)">
              <input
                className={inputClass}
                inputMode="decimal"
                value={custom}
                onChange={(e) => setCustom(e.target.value.replace(/[^0-9.]/g, ""))}
                placeholder="75"
                autoFocus
              />
            </Field>
          )}

          <SectionLabel>Frequency</SectionLabel>
          <div className="mb-4">
            <Segmented
              value={freq}
              onChange={setFreq}
              options={[
                { value: "one_time", label: "One-time" },
                { value: "monthly", label: "Monthly" },
              ]}
            />
          </div>

          <DemoNote>No real payment is processed in this prototype.</DemoNote>
        </>
      )}
    </Sheet>
  );
}

function ServiceSheet({ service, onClose }: { service: Service | null; onClose: () => void }) {
  const { submitSlotRequest, submitFormRequest, backend } = useOrg();
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [alt, setAlt] = useState("");
  const [notes, setNotes] = useState("");
  const [done, setDone] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!service) return null;

  const fixed = service.scheduling === "fixed_slots";
  const valid = (fixed ? !!date && !!time : date.trim().length >= 3) && backend === "ready";

  const close = () => {
    onClose();
    setTimeout(() => {
      setDone(false);
      setDate("");
      setTime("");
      setAlt("");
      setNotes("");
      setRequestId(null);
      setError(null);
    }, 200);
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      if (fixed) {
        const slot = service.slots?.find((s) => s.date === date);
        const value = slot?.timeValues?.[slot.times.indexOf(time)];
        if (!slot?.isoDate || !value) throw new Error("Please pick a date and time again.");
        const r = await submitSlotRequest(service.id, slot.isoDate, value);
        setRequestId(r.id);
      } else {
        const r = await submitFormRequest({
          serviceId: service.id,
          preferredDate: date,
          alternateDate: alt,
          notes,
        });
        setRequestId(r.id);
      }
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Sheet
      open={!!service}
      onClose={close}
      title={done ? "Request received" : service.name}
      footer={
        done ? (
          <Button full onClick={close}>
            Done
          </Button>
        ) : (
          <Button full disabled={!valid || busy} onClick={submit}>
            {busy ? "Sending…" : fixed ? "Request This Time" : "Request Reservation"}
          </Button>
        )
      }
    >
      {done && requestId ? (
        <RequestStatus requestId={requestId} />
      ) : (
        <>
          <div className="mb-4 flex items-baseline justify-between gap-3">
            <span className="text-[1.3rem] font-semibold text-forest-800">
              {service.priceLabel}
            </span>
            <span className="text-[0.8rem] text-charcoal-muted">{service.durationLabel}</span>
          </div>

          <p className="mb-4 text-[0.88rem] leading-relaxed text-charcoal-muted">
            {service.description}
          </p>

          <dl className="mb-5 divide-y divide-forest-100 rounded-xl border border-forest-100 bg-white">
            <div className="flex justify-between gap-4 px-4 py-2.5">
              <dt className="text-[0.8rem] text-charcoal-muted">Location</dt>
              <dd className="text-right text-[0.82rem] text-charcoal">{service.location}</dd>
            </div>
            <div className="flex justify-between gap-4 px-4 py-2.5">
              <dt className="text-[0.8rem] text-charcoal-muted">Scheduling</dt>
              <dd className="text-right text-[0.82rem] text-charcoal">
                {fixed ? "Fixed time slots" : "Request a date"}
              </dd>
            </div>
          </dl>

          <SectionLabel>What to know</SectionLabel>
          <ul className="mb-5 space-y-1.5">
            {service.thingsToKnow.map((t) => (
              <li key={t} className="flex gap-2 text-[0.83rem] leading-relaxed text-charcoal-muted">
                <span aria-hidden="true" className="text-forest-400">
                  •
                </span>
                {t}
              </li>
            ))}
          </ul>

          {fixed ? (
            <>
              <SectionLabel>Pick a date</SectionLabel>
              <div className="mb-4 space-y-2">
                {service.slots?.map((s) => (
                  <button
                    key={s.date}
                    onClick={() => {
                      setDate(s.date);
                      setTime("");
                    }}
                    className={`block w-full rounded-xl border px-4 py-2.5 text-left text-[0.85rem] transition ${
                      date === s.date
                        ? "border-forest-600 bg-forest-50 font-medium text-forest-800"
                        : "border-forest-100 bg-white text-charcoal hover:border-forest-200"
                    }`}
                  >
                    {s.date}
                  </button>
                ))}
              </div>

              {date && (
                <>
                  <SectionLabel>Pick a time</SectionLabel>
                  <div className="mb-4 grid grid-cols-3 gap-2">
                    {service.slots
                      ?.find((s) => s.date === date)
                      ?.times.map((t) => (
                        <button
                          key={t}
                          onClick={() => setTime(t)}
                          className={`rounded-xl border py-2.5 text-[0.8rem] font-medium transition ${
                            time === t
                              ? "border-forest-600 bg-forest-800 text-ivory"
                              : "border-forest-200 bg-white text-charcoal hover:border-forest-400"
                          }`}
                        >
                          {t}
                        </button>
                      ))}
                  </div>
                </>
              )}
            </>
          ) : (
            <>
              <SectionLabel>Request a date</SectionLabel>
              <Field label="Preferred date">
                <input
                  className={inputClass}
                  value={date}
                  maxLength={60}
                  onChange={(e) => setDate(e.target.value)}
                  placeholder="e.g. Saturday, November 21"
                />
              </Field>
              <Field label="Alternate date" hint="Optional">
                <input
                  className={inputClass}
                  value={alt}
                  maxLength={60}
                  onChange={(e) => setAlt(e.target.value)}
                  placeholder="e.g. Sunday, November 22"
                />
              </Field>
              <Field
                label="Details"
                hint="Where (temple or home, and which town), language, guest count, anything else."
              >
                <textarea
                  className={inputClass}
                  rows={3}
                  maxLength={800}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. At our home in Orange, in Hindi, about 15 guests"
                />
              </Field>
            </>
          )}

          {fixed && service.slots && service.slots.length === 0 && (
            <p className="mb-4 text-[0.82rem] text-charcoal-muted">No open times in the next two weeks.</p>
          )}
          {error && <p className="mb-3 text-[0.8rem] text-terracotta-600">{error}</p>}
          <DemoNote>
            {fixed
              ? "Your chosen time is checked against the priests' real calendar. The temple office approves before it's booked. Nothing is charged and no email is sent."
              : "AI reads your request and checks priest availability. The temple office approves before anything is booked. Nothing is charged and no email is sent."}
          </DemoNote>
        </>
      )}
    </Sheet>
  );
}

function EventSheet({
  event,
  onClose,
  onVolunteer,
}: {
  event: Event | null;
  onClose: () => void;
  onVolunteer: (o: VolunteerOpportunity) => void;
}) {
  const { rsvp, myRsvpEventIds, opportunities } = useOrg();
  const [guests, setGuests] = useState(1);
  const [done, setDone] = useState(false);

  if (!event) return null;

  const already = myRsvpEventIds.includes(event.id);
  const eventRoles = opportunities.filter((o) => event.volunteerOpportunityIds.includes(o.id));

  const close = () => {
    onClose();
    setTimeout(() => {
      setDone(false);
      setGuests(1);
    }, 200);
  };

  return (
    <Sheet
      open={!!event}
      onClose={close}
      title={done ? "You're going" : event.name}
      footer={
        done ? (
          <Button full onClick={close}>
            Done
          </Button>
        ) : (
          <Button
            full
            onClick={() => {
              rsvp(event.id, guests);
              setDone(true);
            }}
          >
            {already ? "Update RSVP" : "RSVP"}
          </Button>
        )
      }
    >
      {done ? (
        <DoneState
          title="RSVP confirmed."
          lines={[
            { label: "Event", value: event.name },
            { label: "When", value: `${event.date} · ${event.time}` },
            { label: "Party size", value: String(guests) },
          ]}
          note="Demo only — your RSVP is kept in this browser tab (not saved on the server) and no reminder email is sent."
        />
      ) : (
        <>
          <div
            className="mb-4 h-28 w-full rounded-2xl"
            style={{ background: event.image }}
            aria-hidden="true"
          />

          <p className="mb-1 text-[0.86rem] font-medium text-forest-800">
            {event.date} · {event.time}
          </p>
          <p className="mb-4 text-[0.8rem] text-charcoal-muted">{event.location}</p>

          <p className="mb-5 text-[0.88rem] leading-relaxed text-charcoal-muted">
            {event.description}
          </p>

          {already && (
            <div className="mb-4">
              <Badge tone="green">You've already RSVP'd — submitting again updates it</Badge>
            </div>
          )}

          <Field label="How many people, including you?">
            <div className="flex items-center gap-3">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setGuests((g) => Math.max(1, g - 1))}
                aria-label="Fewer guests"
              >
                −
              </Button>
              <span className="min-w-8 text-center text-[1rem] font-semibold text-charcoal">
                {guests}
              </span>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setGuests((g) => Math.min(20, g + 1))}
                aria-label="More guests"
              >
                +
              </Button>
            </div>
          </Field>

          {eventRoles.length > 0 && (
            <>
              <SectionLabel>Volunteer for this event</SectionLabel>
              <div className="mb-4 space-y-2">
                {eventRoles.map((o) => (
                  <button
                    key={o.id}
                    onClick={() => onVolunteer(o)}
                    className="block w-full rounded-xl border border-forest-100 bg-white px-4 py-3 text-left transition hover:border-forest-200"
                  >
                    <p className="text-[0.86rem] font-semibold text-charcoal">{o.role}</p>
                    <p className="text-[0.76rem] text-charcoal-muted">
                      {o.window} · {o.spotsTotal - o.spotsFilled} spots left
                    </p>
                  </button>
                ))}
              </div>
            </>
          )}

          <DemoNote>Add to Calendar and reminders are not wired up in this prototype.</DemoNote>
        </>
      )}
    </Sheet>
  );
}

function VolunteerSheet({
  opportunity,
  onClose,
}: {
  opportunity: VolunteerOpportunity | null;
  onClose: () => void;
}) {
  const { signUpVolunteer, myOpportunityIds } = useOrg();
  const [done, setDone] = useState(false);

  if (!opportunity) return null;

  const already = myOpportunityIds.includes(opportunity.id);
  const left = opportunity.spotsTotal - opportunity.spotsFilled;
  const full = left <= 0;

  const close = () => {
    onClose();
    setTimeout(() => setDone(false), 200);
  };

  return (
    <Sheet
      open={!!opportunity}
      onClose={close}
      title={done ? "You're signed up" : opportunity.role}
      footer={
        done ? (
          <Button full onClick={close}>
            Done
          </Button>
        ) : (
          <Button
            full
            disabled={full || already}
            onClick={() => {
              signUpVolunteer(opportunity.id);
              setDone(true);
            }}
          >
            {already ? "Already signed up" : full ? "This shift is full" : "Sign Up"}
          </Button>
        )
      }
    >
      {done ? (
        <DoneState
          title="You're signed up."
          lines={[
            { label: "Role", value: opportunity.role },
            { label: "Event", value: opportunity.eventName },
            { label: "Shift", value: opportunity.window },
          ]}
          note="Demo only — the shift is kept in this browser tab (not saved on the server) and no reminder is sent."
        />
      ) : (
        <>
          <p className="mb-1 text-[0.86rem] font-medium text-forest-800">
            {opportunity.eventName}
          </p>
          <p className="mb-4 text-[0.8rem] text-charcoal-muted">{opportunity.window}</p>

          <p className="mb-5 text-[0.88rem] leading-relaxed text-charcoal-muted">
            {opportunity.description}
          </p>

          <div className="mb-2 flex items-baseline justify-between">
            <span className="text-[0.8rem] text-charcoal-muted">Spots filled</span>
            <span className="text-[0.82rem] font-medium text-charcoal">
              {opportunity.spotsFilled} of {opportunity.spotsTotal}
            </span>
          </div>
          <div className="mb-5">
            <Progress filled={opportunity.spotsFilled} total={opportunity.spotsTotal} />
          </div>

          {already && (
            <div className="mb-4">
              <Badge tone="green">You're already on this shift</Badge>
            </div>
          )}

          <DemoNote>Demo only — volunteer sign-ups are kept in this browser tab, not on the server.</DemoNote>
        </>
      )}
    </Sheet>
  );
}

function InfoSheet({
  open,
  onClose,
  org,
}: {
  open: boolean;
  onClose: () => void;
  org: ReturnType<typeof useOrg>["organization"];
}) {
  return (
    <Sheet open={open} onClose={onClose} title={`About ${org.name}`}>
      <p className="mb-5 text-[0.88rem] leading-relaxed text-charcoal-muted">{org.about}</p>

      <SectionLabel>Hours</SectionLabel>
      <Card className="mb-5 divide-y divide-forest-100">
        {org.hours.map((h) => (
          <div key={h.label} className="flex justify-between gap-4 px-4 py-2.5">
            <span className="text-[0.8rem] text-charcoal-muted">{h.label}</span>
            <span className="text-right text-[0.8rem] text-charcoal">{h.value}</span>
          </div>
        ))}
      </Card>

      <SectionLabel>Find us</SectionLabel>
      <Card className="mb-5 p-4">
        <p className="text-[0.85rem] text-charcoal">{org.address}</p>
        <p className="mt-2 text-[0.82rem] text-charcoal-muted">{org.phone}</p>
        <p className="text-[0.82rem] text-charcoal-muted">{org.email}</p>
      </Card>

      <SectionLabel>Leadership</SectionLabel>
      <Card className="mb-5 divide-y divide-forest-100">
        {org.leadership.map((l) => (
          <div key={l.name} className="flex justify-between gap-4 px-4 py-2.5">
            <span className="text-[0.84rem] text-charcoal">{l.name}</span>
            <span className="text-[0.78rem] text-charcoal-muted">{l.role}</span>
          </div>
        ))}
      </Card>

      <SectionLabel>Visiting</SectionLabel>
      <ul className="mb-5 space-y-1.5">
        {org.visitorInfo.map((v) => (
          <li key={v} className="flex gap-2 text-[0.83rem] leading-relaxed text-charcoal-muted">
            <span aria-hidden="true" className="text-forest-400">
              •
            </span>
            {v}
          </li>
        ))}
      </ul>

      <SectionLabel>FAQs</SectionLabel>
      <Card className="mb-4 divide-y divide-forest-100">
        {org.faqs.map((f) => (
          <div key={f.q} className="px-4 py-3">
            <p className="text-[0.85rem] font-semibold text-charcoal">{f.q}</p>
            <p className="mt-1 text-[0.81rem] leading-relaxed text-charcoal-muted">{f.a}</p>
          </div>
        ))}
      </Card>

      <DemoNote>Shanti Mandir is a fictional organization created for this prototype.</DemoNote>
    </Sheet>
  );
}
