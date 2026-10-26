import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, DemoNote, Field, Sheet, Wordmark, inputClass } from "../components/ui";

const NAV = [
  { label: "Product", href: "#product" },
  { label: "For Organizations", href: "#organizations" },
  { label: "How It Works", href: "#how" },
  { label: "About", href: "#about" },
];

const FEATURES = [
  {
    name: "Donations",
    line: "Support your community in seconds.",
    body: "One-time or recurring giving, with members choosing the fund or initiative they want to support.",
  },
  {
    name: "Events",
    line: "Never miss what's happening.",
    body: "Services, festivals, classes, and community gatherings in a single shared calendar.",
  },
  {
    name: "Services",
    line: "Book services without the back-and-forth.",
    body: "Members browse what's offered, see pricing and detail, request or reserve, and get confirmation.",
  },
  {
    name: "Scheduling",
    line: "Scheduling that works for everyone.",
    body: "Offer fixed appointment slots, or let members propose dates and times for review.",
  },
  {
    name: "Volunteering",
    line: "Turn willingness into action.",
    body: "Open roles, shift windows, and remaining spots — with sign-up in a single tap.",
  },
  {
    name: "Community Information",
    line: "Everything members need to know.",
    body: "Hours, directions, announcements, leadership contacts, policies, and FAQs.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Join your community",
    body: "A member joins or selects their organization and immediately has a digital home.",
  },
  {
    n: "02",
    title: "Access everything",
    body: "Events, services, donations, volunteering, and announcements all live in one place.",
  },
  {
    n: "03",
    title: "Stay connected",
    body: "Confirmations, reminders, and new ways to participate arrive as things change.",
  },
];

const SCATTERED = [
  "Outdated website",
  "Spreadsheets",
  "Paper forms",
  "Email chains",
  "Messaging groups",
  "Separate payment app",
  "Manual scheduling",
  "Sign-up forms",
];

const ADMIN_METRICS = [
  { label: "Service payments", value: "$8,420" },
  { label: "Donations", value: "$12,750" },
  { label: "Service reservations", value: "46" },
  { label: "Volunteer signups", value: "128" },
  { label: "Upcoming events", value: "6" },
];

export default function Landing() {
  const [demoOpen, setDemoOpen] = useState(false);
  const [sent, setSent] = useState(false);
  const [org, setOrg] = useState("");

  return (
    <div className="min-h-screen bg-ivory">
      {/* ---------------- nav ---------------- */}
      <header className="sticky top-0 z-30 border-b border-forest-100 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3.5">
          <Link to="/" aria-label="SERVE home">
            <Wordmark />
          </Link>

          <nav className="hidden items-center gap-7 md:flex">
            {NAV.map((n) => (
              <a
                key={n.label}
                href={n.href}
                className="text-[0.86rem] text-charcoal-muted transition hover:text-forest-800"
              >
                {n.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setDemoOpen(true)}>
              Request a Demo
            </Button>
            <Link to="/app">
              <Button size="sm">View Demo</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ---------------- hero ---------------- */}
      <section className="relative overflow-hidden bg-white">
        <div
          className="pointer-events-none absolute inset-0 opacity-70"
          style={{
            background:
              "radial-gradient(760px 440px at 82% -10%, var(--color-gold-200), transparent 65%), radial-gradient(620px 420px at 6% 8%, var(--color-forest-50), transparent 68%)",
          }}
          aria-hidden="true"
        />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-5 py-16 md:py-24 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <Badge tone="gold">Community, made simpler.</Badge>
            <h1 className="mt-5 text-[2.3rem] font-semibold leading-[1.1] tracking-[-0.02em] text-forest-800 sm:text-[3.1rem]">
              Everything your community needs, in one place.
            </h1>
            <p className="mt-5 max-w-xl text-[1.02rem] leading-relaxed text-charcoal-muted">
              SERVE helps religious organizations manage donations, events, services,
              scheduling, and volunteering through one simple digital home.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/app">
                <Button size="lg">View Demo</Button>
              </Link>
              <Button size="lg" variant="secondary" onClick={() => setDemoOpen(true)}>
                Bring SERVE to Your Community
              </Button>
            </div>

            <p className="mt-6 text-[0.78rem] text-charcoal-muted">
              Prototype with sample data — no account needed.
            </p>
          </div>

          <PhoneMockup />
        </div>
      </section>

      {/* ---------------- problem ---------------- */}
      <section id="product" className="border-y border-forest-100 bg-ivory">
        <div className="mx-auto max-w-6xl px-5 py-16 md:py-20">
          <div className="max-w-2xl">
            <h2 className="text-[1.8rem] font-semibold leading-tight tracking-[-0.01em] text-forest-800 sm:text-[2.2rem]">
              Your community shouldn't need five different tools.
            </h2>
            <p className="mt-4 text-[0.98rem] leading-relaxed text-charcoal-muted">
              Most organizations run on a patchwork that nobody chose on purpose — it
              accumulated. Members learn which tool does what, and staff re-enter the same
              information in several places.
            </p>
          </div>

          <div className="mt-10 grid items-center gap-8 lg:grid-cols-[1fr_auto_0.8fr]">
            <div>
              <p className="mb-3 text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-charcoal-muted">
                Before SERVE
              </p>
              <div className="flex flex-wrap gap-2">
                {SCATTERED.map((s) => (
                  <span
                    key={s}
                    className="rounded-lg border border-dashed border-forest-200 bg-white px-3 py-2 text-[0.8rem] text-charcoal-muted"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div className="hidden text-2xl text-forest-200 lg:block" aria-hidden="true">
              →
            </div>

            <div>
              <p className="mb-3 text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-charcoal-muted">
                After SERVE
              </p>
              <Card className="px-6 py-7">
                <Wordmark />
                <p className="mt-3 text-[0.85rem] leading-relaxed text-charcoal-muted">
                  One place for members. One dashboard for the people who run things.
                </p>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- features ---------------- */}
      <section className="bg-white">
        <div className="mx-auto max-w-6xl px-5 py-16 md:py-20">
          <h2 className="text-[1.8rem] font-semibold tracking-[-0.01em] text-forest-800 sm:text-[2.1rem]">
            Six things, handled.
          </h2>
          <p className="mt-3 max-w-xl text-[0.95rem] text-charcoal-muted">
            Each organization configures its own services, funds, events, and volunteer roles.
          </p>

          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <Card key={f.name} className="p-6 transition hover:border-forest-200">
                <p className="text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-terracotta-500">
                  {f.name}
                </p>
                <h3 className="mt-2.5 text-[1.02rem] font-semibold leading-snug text-forest-800">
                  {f.line}
                </h3>
                <p className="mt-2 text-[0.86rem] leading-relaxed text-charcoal-muted">{f.body}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- how it works ---------------- */}
      <section id="how" className="border-y border-forest-100 bg-forest-800 text-ivory">
        <div className="mx-auto max-w-6xl px-5 py-16 md:py-20">
          <h2 className="text-[1.8rem] font-semibold tracking-[-0.01em] sm:text-[2.1rem]">
            How it works
          </h2>
          <div className="mt-10 grid gap-8 md:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n}>
                <p className="text-[0.8rem] font-semibold tracking-[0.14em] text-gold-400">{s.n}</p>
                <h3 className="mt-3 text-[1.1rem] font-semibold">{s.title}</h3>
                <p className="mt-2 text-[0.88rem] leading-relaxed text-forest-100/80">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- for organizations ---------------- */}
      <section id="organizations" className="bg-ivory">
        <div className="mx-auto max-w-6xl px-5 py-16 md:py-20">
          <div className="grid gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
            <div>
              <h2 className="text-[1.8rem] font-semibold leading-tight tracking-[-0.01em] text-forest-800 sm:text-[2.1rem]">
                Built for communities. Designed for the people who run them.
              </h2>
              <p className="mt-4 text-[0.95rem] leading-relaxed text-charcoal-muted">
                Religious organizations are usually run by a small staff and a lot of
                volunteers. SERVE centralizes service requests, payments, volunteer rosters,
                event information, member communication, schedules, and basic reporting — so
                the administrative work shrinks instead of spreading.
              </p>
              <div className="mt-7">
                <Link to="/app">
                  <Button variant="secondary">See the member experience</Button>
                </Link>
              </div>
            </div>

            <Card className="overflow-hidden">
              <div className="flex items-center justify-between gap-3 border-b border-forest-100 px-5 py-3.5">
                <p className="text-[0.82rem] font-semibold text-forest-800">This Month</p>
                <Badge tone="gold">Sample demo figures</Badge>
              </div>
              <div className="grid gap-px bg-forest-100 sm:grid-cols-2">
                {ADMIN_METRICS.map((m) => (
                  <div key={m.label} className="bg-white px-5 py-4">
                    <p className="text-[1.45rem] font-semibold tracking-[-0.01em] text-forest-800">
                      {m.value}
                    </p>
                    <p className="mt-0.5 text-[0.78rem] text-charcoal-muted">{m.label}</p>
                  </div>
                ))}
              </div>
              <div className="grid gap-px bg-forest-100 sm:grid-cols-2">
                <MiniList
                  title="Recent bookings"
                  rows={[
                    "Arjun Patel · Abhishekam",
                    "Meena Iyer · Archana",
                    "Sanjay Rao · Satyanarayan Puja",
                  ]}
                />
                <MiniList
                  title="Volunteer coverage"
                  rows={["Diwali Setup · 11/15", "Food Service · 14/20", "Cleanup · 7/12"]}
                />
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* ---------------- about / cta ---------------- */}
      <section id="about" className="border-t border-forest-100 bg-white">
        <div className="mx-auto max-w-3xl px-5 py-16 text-center md:py-20">
          <h2 className="text-[1.7rem] font-semibold tracking-[-0.01em] text-forest-800 sm:text-[2rem]">
            The digital infrastructure for faith-based communities.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-[0.95rem] leading-relaxed text-charcoal-muted">
            SERVE is starting with Hindu temples, and is built on generic organization
            concepts so churches, mosques, synagogues, and Buddhist centers can run on the
            same foundation. The organization is the customer; the community member is the
            end user.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link to="/app">
              <Button size="lg">View Demo</Button>
            </Link>
            <Button size="lg" variant="secondary" onClick={() => setDemoOpen(true)}>
              Request a Demo
            </Button>
          </div>
        </div>
      </section>

      <footer className="border-t border-forest-100 bg-ivory">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-5 py-8 sm:flex-row">
          <Wordmark size="sm" />
          <p className="text-center text-[0.76rem] text-charcoal-muted">
            Prototype with sample data. Shanti Mandir is fictional.
          </p>
          <Link to="/admin" className="text-[0.76rem] text-charcoal-muted transition hover:text-forest-800">
            Admin dashboard →
          </Link>
        </div>
      </footer>

      {/* ---------------- request a demo ---------------- */}
      <Sheet
        open={demoOpen}
        onClose={() => {
          setDemoOpen(false);
          setSent(false);
          setOrg("");
        }}
        title={sent ? "Request received" : "Request a Demo"}
        footer={
          sent ? (
            <Button full onClick={() => setDemoOpen(false)}>
              Close
            </Button>
          ) : (
            <Button full disabled={!org.trim()} onClick={() => setSent(true)}>
              Send request
            </Button>
          )
        }
      >
        {sent ? (
          <div className="animate-rise text-center">
            <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-forest-100 text-2xl text-forest-700">
              ✓
            </div>
            <h4 className="mb-2 text-lg font-semibold text-forest-800">
              Thanks — we'll be in touch.
            </h4>
            <p className="mb-5 text-[0.87rem] leading-relaxed text-charcoal-muted">
              We'd walk {org.trim()} through SERVE and set up a sample organization with your
              own services and events.
            </p>
            <DemoNote>
              Demo only — nothing was submitted and no email was sent. Wiring this to Resend
              is a next step.
            </DemoNote>
          </div>
        ) : (
          <>
            <p className="mb-5 text-[0.87rem] leading-relaxed text-charcoal-muted">
              Tell us about your community and we'll prepare a walkthrough.
            </p>
            <Field label="Organization name">
              <input
                className={inputClass}
                value={org}
                onChange={(e) => setOrg(e.target.value)}
                placeholder="e.g. Shanti Mandir"
              />
            </Field>
            <Field label="Your role" hint="Optional">
              <input className={inputClass} placeholder="Board member, priest, administrator…" />
            </Field>
            <DemoNote>
              This form is simulated for the prototype — it doesn't send anything.
            </DemoNote>
          </>
        )}
      </Sheet>
    </div>
  );
}

function MiniList({ title, rows }: { title: string; rows: string[] }) {
  return (
    <div className="bg-white px-5 py-4">
      <p className="mb-2 text-[0.7rem] font-semibold uppercase tracking-[0.12em] text-charcoal-muted">
        {title}
      </p>
      <ul className="space-y-1.5">
        {rows.map((r) => (
          <li key={r} className="text-[0.82rem] text-charcoal">
            {r}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Static hero mockup of the member home screen. */
function PhoneMockup() {
  return (
    <div className="mx-auto w-full max-w-[290px]">
      <div className="rounded-[2.4rem] border border-forest-200 bg-white p-2.5 shadow-[0_28px_60px_-20px_rgba(59,47,22,0.32)]">
        <div className="overflow-hidden rounded-[1.9rem] bg-ivory">
          <div
            className="relative px-4 pb-5 pt-9 text-ivory"
            style={{
              background: "linear-gradient(140deg, #3b2f16 0%, #c9962f 50%, #f9c74f 100%)",
            }}
          >
            <p className="text-[0.66rem] uppercase tracking-[0.14em] opacity-80">Welcome back</p>
            <p className="mt-1 text-[1.15rem] font-semibold">Shanti Mandir</p>
          </div>

          <div className="grid grid-cols-4 gap-1.5 px-3 py-3">
            {["Donate", "Book", "Events", "Volunteer"].map((a) => (
              <div
                key={a}
                className="rounded-xl border border-forest-100 bg-white px-1 py-2.5 text-center text-[0.56rem] font-medium text-forest-800"
              >
                {a}
              </div>
            ))}
          </div>

          <div className="space-y-2 px-3 pb-4">
            <p className="text-[0.56rem] font-semibold uppercase tracking-[0.12em] text-charcoal-muted">
              Upcoming
            </p>
            {[
              ["Diwali Celebration", "Sat, Oct 24 · 5:00 PM"],
              ["Sunday Community Lunch", "Sun, Oct 11 · 12:30 PM"],
            ].map(([t, d]) => (
              <div key={t} className="rounded-xl border border-forest-100 bg-white px-3 py-2">
                <p className="text-[0.68rem] font-semibold text-charcoal">{t}</p>
                <p className="text-[0.58rem] text-charcoal-muted">{d}</p>
              </div>
            ))}
            <div className="rounded-xl border border-forest-100 bg-white px-3 py-2">
              <p className="text-[0.68rem] font-semibold text-charcoal">Archana · $25</p>
              <div className="mt-1.5 h-1 w-full rounded-full bg-forest-100">
                <div className="h-full w-2/3 rounded-full bg-forest-600" />
              </div>
            </div>
          </div>

          <div className="flex justify-around border-t border-forest-100 bg-white px-2 py-2">
            {["Home", "Events", "Services", "Volunteer", "Profile"].map((t, i) => (
              <span
                key={t}
                className={`text-[0.5rem] ${
                  i === 0 ? "font-semibold text-forest-800" : "text-charcoal-muted"
                }`}
              >
                {t}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
