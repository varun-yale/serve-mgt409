/**
 * SERVE core domain types.
 *
 * Everything is keyed to an `Organization` — never to "temple". The sample
 * organization happens to be a Hindu temple, but churches, mosques, synagogues
 * and other communities use the identical shapes.
 */

export type OrganizationKind =
  | "temple"
  | "church"
  | "mosque"
  | "synagogue"
  | "buddhist_center"
  | "other";

export interface Organization {
  id: string;
  name: string;
  kind: OrganizationKind;
  tagline: string;
  about: string;
  heroImage: string;
  address: string;
  phone: string;
  email: string;
  hours: { label: string; value: string }[];
  leadership: { name: string; role: string }[];
  faqs: { q: string; a: string }[];
  visitorInfo: string[];
  /** Donation funds this organization has chosen to offer. */
  donationFunds: DonationFund[];
}

export interface Member {
  id: string;
  organizationId: string;
  name: string;
  email: string;
  joinedOn: string;
  family: { name: string; relation: string }[];
  notifications: { id: string; label: string; enabled: boolean }[];
}

export interface Event {
  id: string;
  organizationId: string;
  name: string;
  date: string;
  time: string;
  location: string;
  summary: string;
  description: string;
  image: string;
  /** YYYY-MM-DD when loaded from the backend. */
  isoDate?: string;
  /** Volunteer opportunity ids attached to this event. */
  volunteerOpportunityIds: string[];
}

export type SchedulingMode = "fixed_slots" | "request_based";

export interface Service {
  id: string;
  organizationId: string;
  name: string;
  category: string;
  priceCents: number;
  priceLabel: string;
  durationMinutes: number | null;
  durationLabel: string;
  summary: string;
  description: string;
  location: string;
  thingsToKnow: string[];
  scheduling: SchedulingMode;
  /** Offered slots when scheduling is `fixed_slots` (display date + YYYY-MM-DD + HH:MM times). */
  slots?: { date: string; isoDate?: string; times: string[]; timeValues?: string[] }[] | null;
  locationMode?: "temple" | "home" | "either";
  enabled: boolean;
  popular?: boolean;
}

export type BookingStatus = "pending" | "confirmed" | "completed" | "cancelled";
export type PaymentStatus = "unpaid" | "paid" | "refunded";

export interface Booking {
  id: string;
  organizationId: string;
  memberId: string;
  memberName: string;
  serviceId: string;
  serviceName: string;
  date: string;
  time?: string;
  status: BookingStatus;
  payment: PaymentStatus;
  amountCents: number;
  notes?: string;
}

export interface VolunteerOpportunity {
  id: string;
  organizationId: string;
  eventId: string;
  eventName: string;
  role: string;
  window: string;
  spotsTotal: number;
  spotsFilled: number;
  description: string;
}

export interface VolunteerSignup {
  id: string;
  organizationId: string;
  memberId: string;
  memberName: string;
  opportunityId: string;
  role: string;
  eventName: string;
  window: string;
  signedUpOn: string;
}

export type DonationFrequency = "one_time" | "monthly";

export interface DonationFund {
  id: string;
  name: string;
  blurb: string;
}

export interface Donation {
  id: string;
  organizationId: string;
  memberId: string;
  memberName: string;
  fundId: string;
  fundName: string;
  amountCents: number;
  frequency: DonationFrequency;
  date: string;
}

export interface Announcement {
  id: string;
  organizationId: string;
  title: string;
  body: string;
  postedOn: string;
}

export interface EventRsvp {
  id: string;
  organizationId: string;
  memberId: string;
  eventId: string;
  eventName: string;
  date: string;
  guests: number;
}

/** Everything the member portal and admin dashboard read from. */
export interface OrganizationData {
  organization: Organization;
  member: Member;
  events: Event[];
  services: Service[];
  bookings: Booking[];
  opportunities: VolunteerOpportunity[];
  volunteerSignups: VolunteerSignup[];
  donations: Donation[];
  announcements: Announcement[];
  rsvps: EventRsvp[];
}

export const formatMoney = (cents: number): string =>
  `$${(cents / 100).toLocaleString("en-US", {
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  })}`;

/* ---------------- backend: service requests ---------------- */

export type RequestStatus =
  | "processing"
  | "pending_review"
  | "needs_info"
  | "approved"
  | "rejected"
  | "failed"
  | "cancelled";

export interface ApiBooking {
  id: string;
  request_id: string | null;
  member_id: string;
  member_name: string;
  service_id: string;
  service_name: string;
  priest_id: string;
  priest_name: string;
  date: string;
  start_time: string;
  end_time: string;
  location_type: "temple" | "home";
  city: string | null;
  city_display: string | null;
  language: string | null;
  base_price_cents: number;
  travel_fee_cents: number;
  total_cents: number;
  status: "confirmed" | "cancelled" | "completed";
  payment: string;
  approved_by: string | null;
  created_at: string;
}

export interface MemberRequest {
  id: string;
  source: "ai_request" | "request_form" | "slot_picker";
  status: RequestStatus;
  raw_text: string;
  service_name: string | null;
  member_message: string | null;
  proposed_options: {
    priest_name: string;
    date: string;
    start_time: string;
    end_time: string;
    location_type: string;
    city: string | null;
    total_cents: number;
    travel_fee_cents: number;
  }[];
  booking: ApiBooking | null;
  created_at: string;
  updated_at: string;
}

export const STATUS_LABEL: Record<RequestStatus, string> = {
  processing: "Processing",
  pending_review: "Pending review",
  needs_info: "Needs information",
  approved: "Approved",
  rejected: "Rejected",
  failed: "Needs staff follow-up",
  cancelled: "Cancelled",
};

export const STATUS_TONE: Record<RequestStatus, "neutral" | "green" | "gold" | "terracotta" | "muted"> = {
  processing: "neutral",
  pending_review: "gold",
  needs_info: "terracotta",
  approved: "green",
  rejected: "muted",
  failed: "terracotta",
  cancelled: "muted",
};
