/** Reusable SERVE primitives. Every page composes these. */

import { useEffect } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

/* ---------------- brand mark ---------------- */

import logo from "../assets/serve-logo.jpg";

/**
 * The SERVE logo.
 *
 * The source art is a 760×652 tile with the wordmark floating in the middle and
 * a lot of amber padding around it. Rather than ship a second cropped asset, we
 * window in on the letterforms: `BOX` is the visible band, `IMG` is how large
 * the full image must be drawn for that band to fill it, and `OFF` shifts the
 * image so the band lands on the letters. Ratios come from the artwork, so all
 * four numbers scale together and the mark never distorts.
 */
const LOGO = {
  boxW: 118,
  boxH: 32,
  imgW: 193,
  imgH: 154,
  offX: 38,
  offY: 64,
};

export function Wordmark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const scale = { sm: 0.82, md: 1, lg: 1.6 }[size];
  return (
    <span
      role="img"
      aria-label="SERVE"
      className="inline-block overflow-hidden align-middle"
      style={{ width: LOGO.boxW * scale, height: LOGO.boxH * scale }}
    >
      <img
        src={logo}
        alt=""
        aria-hidden="true"
        className="max-w-none"
        style={{
          width: LOGO.imgW * scale,
          height: LOGO.imgH * scale,
          marginLeft: -LOGO.offX * scale,
          marginTop: -LOGO.offY * scale,
        }}
      />
    </span>
  );
}

/* ---------------- button ---------------- */

type Variant = "primary" | "secondary" | "ghost" | "gold" | "danger";
type Size = "sm" | "md" | "lg";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-forest-800 text-ivory hover:bg-forest-700 active:bg-forest-900 shadow-sm",
  secondary:
    "bg-white text-forest-800 border border-forest-200 hover:border-forest-400 hover:bg-forest-50",
  ghost: "text-forest-800 hover:bg-forest-50",
  gold: "bg-gold-400 text-charcoal hover:bg-gold-500 shadow-sm",
  danger:
    "bg-white text-terracotta-600 border border-terracotta-100 hover:bg-terracotta-100",
};

const SIZES: Record<Size, string> = {
  sm: "px-3 py-1.5 text-[0.8rem]",
  md: "px-4 py-2.5 text-[0.9rem]",
  lg: "px-6 py-3.5 text-[0.95rem]",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  full?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  full,
  className = "",
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-full font-medium transition
        disabled:cursor-not-allowed disabled:opacity-45
        ${VARIANTS[variant]} ${SIZES[size]} ${full ? "w-full" : ""} ${className}`}
      {...rest}
    />
  );
}

/* ---------------- surfaces ---------------- */

export function Card({
  children,
  className = "",
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "article" | "section" | "li";
}) {
  return (
    <Tag
      className={`rounded-2xl border border-forest-100 bg-white shadow-[0_1px_2px_rgba(34,32,29,0.04)] ${className}`}
    >
      {children}
    </Tag>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "green" | "gold" | "terracotta" | "muted";
}) {
  const tones = {
    neutral: "bg-forest-50 text-forest-700 border-forest-100",
    green: "bg-forest-100 text-forest-800 border-forest-200",
    gold: "bg-gold-200/60 text-[#7a5a16] border-gold-200",
    terracotta: "bg-terracotta-100 text-terracotta-600 border-terracotta-100",
    muted: "bg-ivory-200 text-charcoal-muted border-forest-100",
  }[tone];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[0.7rem] font-medium ${tones}`}
    >
      {children}
    </span>
  );
}

/** Spots-filled meter for volunteer roles. */
export function Progress({ filled, total }: { filled: number; total: number }) {
  const pct = total === 0 ? 0 : Math.round((filled / total) * 100);
  const full = filled >= total;
  return (
    <div
      className="h-1.5 w-full overflow-hidden rounded-full bg-forest-100"
      role="progressbar"
      aria-valuenow={filled}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-label={`${filled} of ${total} spots filled`}
    >
      <div
        className={`h-full rounded-full transition-[width] duration-500 ${
          full ? "bg-forest-400" : "bg-forest-600"
        }`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-charcoal-muted">
      {children}
    </h2>
  );
}

export function DemoNote({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-xl border border-dashed border-gold-200 bg-gold-200/25 px-3 py-2 text-[0.74rem] leading-relaxed text-[#7a5a16]">
      {children}
    </p>
  );
}

/* ---------------- sheet / modal ---------------- */

/**
 * Bottom sheet on mobile, centered dialog on desktop — the pattern that
 * translates to a native app later.
 */
export function Sheet({
  open,
  onClose,
  title,
  children,
  footer,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <button
        className="animate-fade absolute inset-0 bg-charcoal/35 backdrop-blur-[2px]"
        onClick={onClose}
        aria-label="Close"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="animate-sheet relative flex max-h-[88vh] w-full max-w-md flex-col
          rounded-t-3xl bg-ivory shadow-2xl sm:max-h-[86vh] sm:rounded-3xl"
      >
        <header className="flex items-center justify-between gap-3 border-b border-forest-100 px-5 py-4">
          <h3 className="text-[1.05rem] font-semibold text-forest-800">{title}</h3>
          <button
            onClick={onClose}
            className="grid h-8 w-8 place-items-center rounded-full text-charcoal-muted transition hover:bg-forest-50"
            aria-label="Close"
          >
            ✕
          </button>
        </header>

        <div className="scroll-area flex-1 overflow-y-auto px-5 py-4">{children}</div>

        {footer && (
          <footer className="border-t border-forest-100 bg-white px-5 py-4">{footer}</footer>
        )}
      </div>
    </div>
  );
}

/** Success state shown after a simulated action. */
export function DoneState({
  title,
  lines,
  note,
}: {
  title: string;
  lines: { label: string; value: string }[];
  note: string;
}) {
  return (
    <div className="animate-rise text-center">
      <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-full bg-forest-100 text-2xl text-forest-700">
        ✓
      </div>
      <h4 className="mb-1 text-lg font-semibold text-forest-800">{title}</h4>

      <dl className="my-5 divide-y divide-forest-100 rounded-2xl border border-forest-100 bg-white text-left">
        {lines.map((l) => (
          <div key={l.label} className="flex items-baseline justify-between gap-4 px-4 py-2.5">
            <dt className="text-[0.8rem] text-charcoal-muted">{l.label}</dt>
            <dd className="text-right text-[0.85rem] font-medium text-charcoal">{l.value}</dd>
          </div>
        ))}
      </dl>

      <DemoNote>{note}</DemoNote>
    </div>
  );
}

/* ---------------- form fields ---------------- */

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="mb-4 block">
      <span className="mb-1.5 block text-[0.78rem] font-medium text-charcoal">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-[0.72rem] text-charcoal-muted">{hint}</span>}
    </label>
  );
}

export const inputClass =
  "w-full rounded-xl border border-forest-200 bg-white px-3.5 py-2.5 text-[0.88rem] text-charcoal " +
  "placeholder:text-charcoal-muted/60 focus:border-forest-600 focus:outline-none";

/** Two-state segmented control. */
export function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="inline-flex w-full rounded-full border border-forest-200 bg-white p-1">
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          aria-pressed={value === o.value}
          className={`flex-1 rounded-full px-4 py-2 text-[0.82rem] font-medium transition ${
            value === o.value
              ? "bg-forest-800 text-ivory"
              : "text-charcoal-muted hover:text-forest-800"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
}) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={onChange}
      className={`relative h-6 w-11 flex-none rounded-full transition ${
        checked ? "bg-forest-600" : "bg-forest-100"
      }`}
    >
      <span
        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-[left] ${
          checked ? "left-[1.4rem]" : "left-0.5"
        }`}
      />
    </button>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <Card className="px-4 py-8 text-center text-[0.85rem] text-charcoal-muted">{children}</Card>
  );
}
