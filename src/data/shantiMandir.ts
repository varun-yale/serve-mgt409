/**
 * Mock data for the sample organization.
 *
 * Shanti Mandir is fictional. Events and services here are only a fallback for
 * when the backend is down; the live versions (with real dates and slots) come
 * from the SERVE API. Donations, volunteering and RSVPs remain in-browser demo data.
 */

import type { OrganizationData } from "../types";

const ORG_ID = "org_shanti_mandir";
const MEMBER_ID = "mem_arjun_patel";

export const shantiMandir: OrganizationData = {
  organization: {
    id: ORG_ID,
    name: "Shanti Mandir",
    kind: "temple",
    tagline: "A place to gather, serve, and belong.",
    about:
      "Shanti Mandir has served families in the greater New Haven area for over thirty years. We offer daily worship, festival celebrations, cultural education for children, and a community kitchen that serves anyone who walks through our doors.",
    heroImage:
      "linear-gradient(140deg, #3a2f1b 0%, #b8842a 50%, #edb54c 100%)",
    address: "480 Willow Bend Road, New Haven, CT 06511",
    phone: "(203) 555-0142",
    email: "hello@shantimandir.example",
    hours: [
      { label: "Monday – Friday", value: "7:00 AM – 12:00 PM, 5:00 – 8:30 PM" },
      { label: "Saturday", value: "7:00 AM – 8:30 PM" },
      { label: "Sunday", value: "7:00 AM – 9:00 PM" },
      { label: "Festival days", value: "Extended hours — see Events" },
    ],
    leadership: [
      { name: "Pandit Ramesh Sharma", role: "Head Priest" },
      { name: "Pandit Anil Dube", role: "Associate Priest" },
      { name: "Meena Iyer", role: "Board President" },
      { name: "Sanjay Rao", role: "Volunteer Coordinator" },
    ],
    faqs: [
      {
        q: "Do I need to be a member to attend?",
        a: "No. Everyone is welcome at any service, class, or community meal, member or not.",
      },
      {
        q: "What should I wear?",
        a: "Modest, comfortable clothing. Shoes are removed before entering the main hall; cubbies are by the entrance.",
      },
      {
        q: "Can I bring children?",
        a: "Always. We run a youth cultural class on Saturdays and children are welcome at every service.",
      },
      {
        q: "How do I request a service for a specific date?",
        a: "Book through the Services tab. Request-based services let you propose a preferred and alternate date.",
      },
    ],
    visitorInfo: [
      "Free parking in the main lot; overflow parking across Willow Bend Road on festival days.",
      "The main hall and community kitchen are both wheelchair accessible via the east entrance.",
      "Prasad is served after morning and evening worship.",
      "Photography is welcome in common areas, but please ask before photographing a service.",
    ],
    donationFunds: [
      { id: "fund_general", name: "General Fund", blurb: "Operations and upkeep" },
      { id: "fund_annadanam", name: "Annadanam", blurb: "Community meals" },
      { id: "fund_education", name: "Education", blurb: "Youth and cultural programs" },
      { id: "fund_festival", name: "Festival Fund", blurb: "Festival celebrations and programming" },
    ],
  },

  member: {
    id: MEMBER_ID,
    organizationId: ORG_ID,
    name: "Arjun Patel",
    email: "arjun.patel@example.com",
    joinedOn: "March 2021",
    family: [
      { name: "Priya Patel", relation: "Spouse" },
      { name: "Aarav Patel", relation: "Child" },
      { name: "Kavya Patel", relation: "Child" },
    ],
    notifications: [
      { id: "n_events", label: "Upcoming events and festivals", enabled: true },
      { id: "n_booking", label: "Service booking confirmations", enabled: true },
      { id: "n_volunteer", label: "Volunteer shift reminders", enabled: true },
      { id: "n_donation", label: "Donation receipts", enabled: true },
      { id: "n_news", label: "Monthly community newsletter", enabled: false },
    ],
  },

  events: [
    {
      id: "evt_diwali",
      organizationId: ORG_ID,
      name: "Diwali Celebration",
      date: "Saturday, October 24",
      time: "5:00 PM",
      location: "Main Hall & Courtyard",
      summary: "Lamp lighting, music, and a community dinner for all ages.",
      description:
        "Our largest gathering of the year. The evening opens with a lamp lighting in the courtyard, followed by devotional music, a children's performance, and a full community dinner. Bring family and friends — no registration required.",
      image: "linear-gradient(135deg, #c98a21 0%, #f4cd77 100%)",
      volunteerOpportunityIds: ["vol_diwali_setup", "vol_diwali_food", "vol_diwali_cleanup"],
    },
    {
      id: "evt_garba",
      organizationId: ORG_ID,
      name: "Navratri Garba Night",
      date: "Friday, October 10",
      time: "7:30 PM",
      location: "Community Hall",
      summary: "Nine nights of music and dance — night four, open to everyone.",
      description:
        "Live dhol and traditional garba circles. Beginners are genuinely welcome; volunteers lead the first circle slowly to teach the steps. Light refreshments served at intermission.",
      image: "linear-gradient(135deg, #5a4824 0%, #d4a949 100%)",
      volunteerOpportunityIds: [],
    },
    {
      id: "evt_lunch",
      organizationId: ORG_ID,
      name: "Sunday Community Lunch",
      date: "Sunday, October 11",
      time: "12:30 PM",
      location: "Community Kitchen",
      summary: "A free vegetarian meal, served every Sunday to anyone who comes.",
      description:
        "Annadanam is at the heart of what we do. Every Sunday our kitchen volunteers prepare and serve a free vegetarian lunch. There is no cost and no expectation — come eat with us.",
      image: "linear-gradient(135deg, #b07f22 0%, #f8e3b4 100%)",
      volunteerOpportunityIds: ["vol_lunch_prep", "vol_lunch_serve", "vol_lunch_cleanup"],
    },
    {
      id: "evt_gita",
      organizationId: ORG_ID,
      name: "Bhagavad Gita Discussion",
      date: "Wednesday, October 14",
      time: "7:00 PM",
      location: "Library Room",
      summary: "An open weekly discussion group — no preparation needed.",
      description:
        "A conversational study group working slowly through the text. Pandit Anil Dube facilitates, but the format is discussion rather than lecture. Newcomers can join at any point.",
      image: "linear-gradient(135deg, #2b2419 0%, #b8842a 100%)",
      volunteerOpportunityIds: [],
    },
    {
      id: "evt_youth",
      organizationId: ORG_ID,
      name: "Youth Cultural Class",
      date: "Saturday, October 17",
      time: "10:00 AM",
      location: "Classroom B",
      summary: "Language, music, and dance for children ages 5–14.",
      description:
        "A weekly class rotating through language basics, devotional music, and classical dance. Taught by community volunteers. Registration is per term, but visitors may sit in on a session first.",
      image: "linear-gradient(135deg, #edb54c 0%, #8c6417 100%)",
      volunteerOpportunityIds: [],
    },
  ],

  services: [
    {
      id: "svc_archana",
      organizationId: ORG_ID,
      name: "Archana",
      category: "Daily Services",
      priceCents: 2500,
      priceLabel: "$25",
      durationMinutes: 15,
      durationLabel: "Approx. 15 minutes",
      summary: "A short personal offering with your name and intention.",
      description:
        "A brief personal offering performed by a priest, who recites your name, birth star, and intention. Commonly requested for birthdays, anniversaries, exam results, or simply gratitude.",
      location: "Main Hall",
      thingsToKnow: [
        "Arrive about ten minutes early and check in at the front desk.",
        "Bring the full name and birth star of anyone being named, if you know it.",
        "Offerings of flowers or fruit are welcome but never required.",
      ],
      scheduling: "fixed_slots",
      slots: [
        { date: "Thursday, October 9", times: ["8:00 AM", "8:30 AM", "6:00 PM", "6:30 PM"] },
        { date: "Friday, October 10", times: ["8:00 AM", "8:30 AM", "6:00 PM"] },
        { date: "Saturday, October 11", times: ["9:00 AM", "9:30 AM", "10:00 AM", "5:30 PM"] },
      ],
      enabled: true,
      popular: true,
    },
    {
      id: "svc_abhishekam",
      organizationId: ORG_ID,
      name: "Abhishekam",
      category: "Daily Services",
      priceCents: 5100,
      priceLabel: "$51",
      durationMinutes: 30,
      durationLabel: "Approx. 30 minutes",
      summary: "A ceremonial bathing ritual with water, milk, and honey.",
      description:
        "A ceremonial bathing of the deity accompanied by chanting. Families often sponsor an abhishekam to mark a milestone or dedicate the merit to a relative.",
      location: "Main Hall",
      thingsToKnow: [
        "Seating is limited to about eight people in the inner hall.",
        "The ritual runs on a fixed schedule and begins promptly.",
        "Prasad is distributed to your party afterward.",
      ],
      scheduling: "fixed_slots",
      slots: [
        { date: "Friday, October 10", times: ["7:30 AM", "6:30 PM"] },
        { date: "Saturday, October 11", times: ["7:30 AM", "11:00 AM", "6:30 PM"] },
        { date: "Sunday, October 12", times: ["7:30 AM", "11:00 AM"] },
      ],
      enabled: true,
      popular: true,
    },
    {
      id: "svc_satyanarayan",
      organizationId: ORG_ID,
      name: "Satyanarayan Puja",
      category: "Special Pujas",
      priceCents: 15100,
      priceLabel: "$151",
      durationMinutes: 60,
      durationLabel: "Approx. 60 minutes",
      summary: "A full household puja, usually sponsored by one family.",
      description:
        "A longer ceremony traditionally performed on a full moon or to mark the fulfilment of a vow. One family sponsors the puja and may invite guests; the priest will walk you through each step as it happens.",
      location: "Main Hall or your home",
      thingsToKnow: [
        "Requires scheduling — propose a preferred and an alternate date.",
        "A materials list is emailed to you once the date is confirmed.",
        "Can be performed at your home for an additional travel fee.",
      ],
      scheduling: "request_based",
      enabled: true,
      popular: true,
    },
    {
      id: "svc_griha",
      organizationId: ORG_ID,
      name: "Griha Pravesh",
      category: "Life Events",
      priceCents: 25100,
      priceLabel: "Starting at $251",
      durationMinutes: null,
      durationLabel: "Varies — date request required",
      summary: "A house blessing performed at your new home.",
      description:
        "A housewarming ceremony performed at your residence before you move in. Scope and duration depend on the size of the home and which rituals you include; a priest will call you to plan the details.",
      location: "Your home",
      thingsToKnow: [
        "Please request at least three weeks ahead where possible.",
        "Travel within 25 miles is included in the base price.",
        "An auspicious time window will be suggested for your chosen date.",
      ],
      scheduling: "request_based",
      enabled: true,
    },
    {
      id: "svc_naming",
      organizationId: ORG_ID,
      name: "Namakaranam",
      category: "Life Events",
      priceCents: 10100,
      priceLabel: "$101",
      durationMinutes: 45,
      durationLabel: "Approx. 45 minutes",
      summary: "A naming ceremony for a newborn child.",
      description:
        "A ceremony formally giving a child their name, typically held in the first weeks after birth. Families usually invite close relatives; the hall accommodates about thirty guests.",
      location: "Main Hall",
      thingsToKnow: [
        "Requires scheduling — propose a preferred and an alternate date.",
        "Let us know your expected guest count when requesting.",
      ],
      scheduling: "request_based",
      enabled: true,
    },
    {
      id: "svc_counsel",
      organizationId: ORG_ID,
      name: "Priest Consultation",
      category: "Priest Services",
      priceCents: 0,
      priceLabel: "No charge",
      durationMinutes: 30,
      durationLabel: "Approx. 30 minutes",
      summary: "A private conversation with a priest.",
      description:
        "A confidential meeting to discuss a personal matter, plan a ceremony, or ask questions about practice. There is no charge for consultations.",
      location: "Library Room",
      thingsToKnow: [
        "Conversations are confidential.",
        "Available in English, Hindi, Gujarati, and Tamil.",
      ],
      scheduling: "fixed_slots",
      slots: [
        { date: "Thursday, October 9", times: ["4:00 PM", "4:30 PM", "5:00 PM"] },
        { date: "Monday, October 13", times: ["4:00 PM", "4:30 PM"] },
      ],
      enabled: true,
    },
  ],

  // Service bookings now live in the backend database.
  bookings: [],

  opportunities: [
    {
      id: "vol_diwali_setup",
      organizationId: ORG_ID,
      eventId: "evt_diwali",
      eventName: "Diwali Celebration",
      role: "Setup Crew",
      window: "3:00 PM – 5:00 PM",
      spotsTotal: 15,
      spotsFilled: 11,
      description:
        "Arrange seating in the main hall, set up the courtyard lamps, and help stage the children's performance area.",
    },
    {
      id: "vol_diwali_food",
      organizationId: ORG_ID,
      eventId: "evt_diwali",
      eventName: "Diwali Celebration",
      role: "Food Service",
      window: "6:00 PM – 8:00 PM",
      spotsTotal: 20,
      spotsFilled: 14,
      description:
        "Serve the community dinner from the buffet line, keep stations stocked, and help guests find seating.",
    },
    {
      id: "vol_diwali_cleanup",
      organizationId: ORG_ID,
      eventId: "evt_diwali",
      eventName: "Diwali Celebration",
      role: "Cleanup",
      window: "9:00 PM – 10:00 PM",
      spotsTotal: 12,
      spotsFilled: 7,
      description:
        "Break down seating, clear the courtyard, and reset the hall for Sunday morning worship.",
    },
    {
      id: "vol_lunch_prep",
      organizationId: ORG_ID,
      eventId: "evt_lunch",
      eventName: "Sunday Community Lunch",
      role: "Kitchen Prep",
      window: "9:30 AM – 12:00 PM",
      spotsTotal: 10,
      spotsFilled: 7,
      description:
        "Chop vegetables, cook rice and dal, and plate prasad alongside the kitchen lead.",
    },
    {
      id: "vol_lunch_serve",
      organizationId: ORG_ID,
      eventId: "evt_lunch",
      eventName: "Sunday Community Lunch",
      role: "Serving",
      window: "12:30 PM – 1:30 PM",
      spotsTotal: 12,
      spotsFilled: 7,
      description: "Serve plates, refill the line, and make sure every guest is seated and fed.",
    },
    {
      id: "vol_lunch_cleanup",
      organizationId: ORG_ID,
      eventId: "evt_lunch",
      eventName: "Sunday Community Lunch",
      role: "Cleanup",
      window: "1:30 PM – 2:30 PM",
      spotsTotal: 8,
      spotsFilled: 4,
      description: "Wash, dry, and reset the kitchen and dining hall.",
    },
    {
      id: "vol_cleanup_temple",
      organizationId: ORG_ID,
      eventId: "evt_lunch",
      eventName: "Monthly Temple Cleanup",
      role: "General Cleanup",
      window: "Saturday, 8:00 AM – 11:00 AM",
      spotsTotal: 10,
      spotsFilled: 6,
      description:
        "Polish brass, dust the hall, tidy the library, and tend the courtyard garden beds.",
    },
  ],

  volunteerSignups: [
    {
      id: "vs_1",
      organizationId: ORG_ID,
      memberId: MEMBER_ID,
      memberName: "Arjun Patel",
      opportunityId: "vol_lunch_serve",
      role: "Serving",
      eventName: "Sunday Community Lunch",
      window: "12:30 PM – 1:30 PM",
      signedUpOn: "September 28",
    },
    {
      id: "vs_2",
      organizationId: ORG_ID,
      memberId: "mem_meena",
      memberName: "Meena Iyer",
      opportunityId: "vol_diwali_setup",
      role: "Setup Crew",
      eventName: "Diwali Celebration",
      window: "3:00 PM – 5:00 PM",
      signedUpOn: "September 22",
    },
    {
      id: "vs_3",
      organizationId: ORG_ID,
      memberId: "mem_sanjay",
      memberName: "Sanjay Rao",
      opportunityId: "vol_diwali_food",
      role: "Food Service",
      eventName: "Diwali Celebration",
      window: "6:00 PM – 8:00 PM",
      signedUpOn: "September 24",
    },
  ],

  donations: [
    {
      id: "dn_1",
      organizationId: ORG_ID,
      memberId: MEMBER_ID,
      memberName: "Arjun Patel",
      fundId: "fund_annadanam",
      fundName: "Annadanam",
      amountCents: 5100,
      frequency: "monthly",
      date: "October 1",
    },
    {
      id: "dn_2",
      organizationId: ORG_ID,
      memberId: MEMBER_ID,
      memberName: "Arjun Patel",
      fundId: "fund_general",
      fundName: "General Fund",
      amountCents: 10100,
      frequency: "one_time",
      date: "August 14",
    },
    {
      id: "dn_3",
      organizationId: ORG_ID,
      memberId: "mem_meena",
      memberName: "Meena Iyer",
      fundId: "fund_festival",
      fundName: "Festival Fund",
      amountCents: 25100,
      frequency: "one_time",
      date: "September 30",
    },
    {
      id: "dn_4",
      organizationId: ORG_ID,
      memberId: "mem_lata",
      memberName: "Lata Desai",
      fundId: "fund_education",
      fundName: "Education",
      amountCents: 7500,
      frequency: "monthly",
      date: "September 29",
    },
  ],

  announcements: [
    {
      id: "an_1",
      organizationId: ORG_ID,
      title: "Diwali volunteer registration is now open.",
      body: "We need about forty volunteers across setup, food service, and cleanup. Shifts are two hours each — sign up through the Volunteer tab.",
      postedOn: "October 2",
    },
    {
      id: "an_2",
      organizationId: ORG_ID,
      title: "Youth cultural class enrollment is open.",
      body: "Fall term runs through December for ages five to fourteen. Sibling discounts are available; speak with Meena after Sunday lunch.",
      postedOn: "September 27",
    },
  ],

  rsvps: [
    {
      id: "rsvp_1",
      organizationId: ORG_ID,
      memberId: MEMBER_ID,
      eventId: "evt_lunch",
      eventName: "Sunday Community Lunch",
      date: "Sunday, October 11",
      guests: 4,
    },
  ],
};
