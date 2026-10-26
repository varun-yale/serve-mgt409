/**
 * Organization store.
 *
 * Events, services, service requests and bookings come from the SERVE backend
 * (SQLite) and survive a refresh. Donations, volunteer signups, RSVPs and
 * notification toggles are still in-memory demo state for this browser tab only.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { shantiMandir } from "./data/shantiMandir";
import { api, fmtDate, fmtTime } from "./api";
import type {
  ApiBooking,
  Donation,
  DonationFrequency,
  Event,
  EventRsvp,
  MemberRequest,
  OrganizationData,
  Service,
  VolunteerSignup,
} from "./types";

let seq = 1;
const nextId = (prefix: string) => `${prefix}_${Date.now().toString(36)}${seq++}`;

interface PortalPayload {
  today: string;
  demo_notice: string;
  events: (Omit<Event, "date" | "time"> & { isoDate: string; startTime: string; endTime: string })[];
  services: (Omit<Service, "slots"> & { slots: { date: string; times: string[] }[] | null })[];
  requests: MemberRequest[];
  bookings: ApiBooking[];
}

export type BackendState = "loading" | "ready" | "offline";

interface StoreValue extends OrganizationData {
  backend: BackendState;
  backendError: string | null;
  today: string | null;
  /** Service requests for the demo member, from the backend. */
  requests: MemberRequest[];
  /** Confirmed/cancelled bookings for the demo member, from the backend. */
  serviceBookings: ApiBooking[];
  refresh: () => Promise<void>;
  submitAIRequest: (text: string) => Promise<MemberRequest>;
  submitFormRequest: (input: {
    serviceId: string;
    preferredDate: string;
    alternateDate?: string;
    notes?: string;
  }) => Promise<MemberRequest>;
  submitSlotRequest: (serviceId: string, isoDate: string, time: string) => Promise<MemberRequest>;
  replyToRequest: (requestId: string, text: string) => Promise<MemberRequest>;
  fetchRequest: (requestId: string) => Promise<MemberRequest>;
  signUpVolunteer: (opportunityId: string) => VolunteerSignup | null;
  cancelVolunteerSignup: (signupId: string) => void;
  donate: (fundId: string, amountCents: number, frequency: DonationFrequency) => Donation;
  rsvp: (eventId: string, guests: number) => EventRsvp;
  cancelRsvp: (rsvpId: string) => void;
  toggleNotification: (notificationId: string) => void;
  /** Opportunity ids the current member has taken. */
  myOpportunityIds: string[];
  /** Event ids the current member has RSVP'd to. */
  myRsvpEventIds: string[];
}

const StoreContext = createContext<StoreValue | null>(null);

export function OrgProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<OrganizationData>(shantiMandir);
  const [backend, setBackend] = useState<BackendState>("loading");
  const [backendError, setBackendError] = useState<string | null>(null);
  const [today, setToday] = useState<string | null>(null);
  const [requests, setRequests] = useState<MemberRequest[]>([]);
  const [serviceBookings, setServiceBookings] = useState<ApiBooking[]>([]);

  const { organization, member } = data;

  const refresh = useCallback(async () => {
    try {
      const p = await api.get<PortalPayload>("/portal");
      const events: Event[] = p.events.map((e) => ({
        ...e,
        date: fmtDate(e.isoDate),
        time: fmtTime(e.startTime),
      }));
      const services: Service[] = p.services.map((s) => ({
        ...s,
        slots: s.slots?.map((sl) => ({
          date: fmtDate(sl.date),
          isoDate: sl.date,
          times: sl.times.map(fmtTime),
          timeValues: sl.times,
        })),
      }));
      setData((d) => ({
        ...d,
        events,
        services,
        // Keep in-memory RSVPs pointing at the real event dates.
        rsvps: d.rsvps.map((r) => ({
          ...r,
          date: events.find((e) => e.id === r.eventId)?.date ?? r.date,
        })),
      }));
      setRequests(p.requests);
      setServiceBookings(p.bookings);
      setToday(p.today);
      setBackend("ready");
      setBackendError(null);
    } catch (err) {
      setBackend("offline");
      setBackendError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const upsertRequest = useCallback((r: MemberRequest) => {
    setRequests((rs) => [r, ...rs.filter((x) => x.id !== r.id)]);
    return r;
  }, []);

  const submitAIRequest = useCallback(
    async (text: string) => upsertRequest(await api.post<MemberRequest>("/requests", { text })),
    [upsertRequest],
  );

  const submitFormRequest = useCallback(
    async (input: { serviceId: string; preferredDate: string; alternateDate?: string; notes?: string }) =>
      upsertRequest(
        await api.post<MemberRequest>("/requests/form", {
          service_id: input.serviceId,
          preferred_date: input.preferredDate,
          alternate_date: input.alternateDate || null,
          notes: input.notes || null,
        }),
      ),
    [upsertRequest],
  );

  const submitSlotRequest = useCallback(
    async (serviceId: string, isoDate: string, time: string) => {
      const r = upsertRequest(
        await api.post<MemberRequest>("/requests/slot", {
          service_id: serviceId,
          date: isoDate,
          start_time: time,
        }),
      );
      void refresh();
      return r;
    },
    [upsertRequest, refresh],
  );

  const replyToRequest = useCallback(
    async (requestId: string, text: string) =>
      upsertRequest(await api.post<MemberRequest>(`/requests/${requestId}/reply`, { text })),
    [upsertRequest],
  );

  const fetchRequest = useCallback(
    async (requestId: string) => {
      const r = await api.get<MemberRequest>(`/requests/${requestId}`);
      setRequests((rs) => rs.map((x) => (x.id === r.id ? r : x)));
      if (r.booking) {
        setServiceBookings((bs) => [r.booking!, ...bs.filter((b) => b.id !== r.booking!.id)]);
      }
      return r;
    },
    [],
  );

  const signUpVolunteer = useCallback(
    (opportunityId: string): VolunteerSignup | null => {
      const opp = data.opportunities.find((o) => o.id === opportunityId);
      if (!opp || opp.spotsFilled >= opp.spotsTotal) return null;

      const signup: VolunteerSignup = {
        id: nextId("vs"),
        organizationId: organization.id,
        memberId: member.id,
        memberName: member.name,
        opportunityId,
        role: opp.role,
        eventName: opp.eventName,
        window: opp.window,
        signedUpOn: "Today",
      };

      setData((d) => ({
        ...d,
        volunteerSignups: [signup, ...d.volunteerSignups],
        opportunities: d.opportunities.map((o) =>
          o.id === opportunityId
            ? { ...o, spotsFilled: Math.min(o.spotsFilled + 1, o.spotsTotal) }
            : o,
        ),
      }));
      return signup;
    },
    [data.opportunities, organization.id, member.id, member.name],
  );

  const cancelVolunteerSignup = useCallback((signupId: string) => {
    setData((d) => {
      const signup = d.volunteerSignups.find((s) => s.id === signupId);
      if (!signup) return d;
      return {
        ...d,
        volunteerSignups: d.volunteerSignups.filter((s) => s.id !== signupId),
        // Give the spot back.
        opportunities: d.opportunities.map((o) =>
          o.id === signup.opportunityId
            ? { ...o, spotsFilled: Math.max(0, o.spotsFilled - 1) }
            : o,
        ),
      };
    });
  }, []);

  const donate = useCallback(
    (fundId: string, amountCents: number, frequency: DonationFrequency): Donation => {
      const fund = organization.donationFunds.find((f) => f.id === fundId);
      const donation: Donation = {
        id: nextId("dn"),
        organizationId: organization.id,
        memberId: member.id,
        memberName: member.name,
        fundId,
        fundName: fund?.name ?? "General Fund",
        amountCents,
        frequency,
        date: "Today",
      };
      setData((d) => ({ ...d, donations: [donation, ...d.donations] }));
      return donation;
    },
    [organization.id, organization.donationFunds, member.id, member.name],
  );

  const rsvp = useCallback(
    (eventId: string, guests: number): EventRsvp => {
      const event = data.events.find((e) => e.id === eventId);
      const entry: EventRsvp = {
        id: nextId("rsvp"),
        organizationId: organization.id,
        memberId: member.id,
        eventId,
        eventName: event?.name ?? "Event",
        date: event?.date ?? "",
        guests,
      };
      setData((d) => ({
        ...d,
        // One RSVP per event — replace any prior one.
        rsvps: [entry, ...d.rsvps.filter((r) => r.eventId !== eventId)],
      }));
      return entry;
    },
    [data.events, organization.id, member.id],
  );

  const cancelRsvp = useCallback((rsvpId: string) => {
    setData((d) => ({ ...d, rsvps: d.rsvps.filter((r) => r.id !== rsvpId) }));
  }, []);

  const toggleNotification = useCallback((notificationId: string) => {
    setData((d) => ({
      ...d,
      member: {
        ...d.member,
        notifications: d.member.notifications.map((n) =>
          n.id === notificationId ? { ...n, enabled: !n.enabled } : n,
        ),
      },
    }));
  }, []);

  const myOpportunityIds = useMemo(
    () =>
      data.volunteerSignups
        .filter((s) => s.memberId === member.id)
        .map((s) => s.opportunityId),
    [data.volunteerSignups, member.id],
  );

  const myRsvpEventIds = useMemo(
    () => data.rsvps.filter((r) => r.memberId === member.id).map((r) => r.eventId),
    [data.rsvps, member.id],
  );

  const value: StoreValue = {
    ...data,
    backend,
    backendError,
    today,
    requests,
    serviceBookings,
    refresh,
    submitAIRequest,
    submitFormRequest,
    submitSlotRequest,
    replyToRequest,
    fetchRequest,
    signUpVolunteer,
    cancelVolunteerSignup,
    donate,
    rsvp,
    cancelRsvp,
    toggleNotification,
    myOpportunityIds,
    myRsvpEventIds,
  };

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useOrg(): StoreValue {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useOrg must be used inside <OrgProvider>");
  return ctx;
}
