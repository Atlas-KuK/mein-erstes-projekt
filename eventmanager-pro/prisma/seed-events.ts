// Seed-Daten: Jahresübersicht 2026 (88 Events)
// Basiert auf den Excel-Planungsdaten von Polikarpos Karafoulidis.

import type {
  EventKategorie, EventOrt, IndoorOutdoor,
  EventStatusTyp, Prioritaet,
} from '@prisma/client';

export interface SeedEvent {
  name: string;
  datum: string;              // ISO YYYY-MM-DD
  datumBis?: string;
  kategorie: EventKategorie;
  ort: EventOrt;
  ortDetails?: string;
  flaeche?: string;
  indoorOutdoor?: IndoorOutdoor;
  anlass?: string;
  status?: EventStatusTyp;
  prioritaet?: Prioritaet;
  cateringJa?: boolean;
  eventJa?: boolean;
  socialMediaNoetig?: boolean;
  auftraggeber?: string;
  ansprechpartner?: string;
  personenanzahl?: number;
  preisProPerson?: number;
  bemerkungen?: string;
  einlass?: string;           // HH:MM
  start?: string;
  ende?: string;
}

// ---------------------------------------------------------------------------
// Regelmäßige Events 2026
// ---------------------------------------------------------------------------

const regelmaessig: SeedEvent[] = [];

// 80er Hits Party - monatlich in Schänke 1998 (Samstage)
const achtzigerTermine = [
  '2026-01-31', '2026-02-28', '2026-03-28', '2026-04-25',
  '2026-05-30', '2026-06-27', '2026-07-25', '2026-08-29',
  '2026-09-26', '2026-10-31',
];
achtzigerTermine.forEach((d) => regelmaessig.push({
  name: '80er Hits Party',
  datum: d,
  kategorie: 'Party_Musik',
  ort: 'Schaenke_1998',
  indoorOutdoor: 'Indoor',
  status: 'Bestaetigt',
  socialMediaNoetig: true,
  eventJa: true,
  start: '21:00',
  einlass: '20:30',
}));

// BINGO-Abende - monatlich (Freitags)
const bingoTermine = [
  '2026-01-16', '2026-02-20', '2026-03-20', '2026-04-17',
  '2026-05-15', '2026-06-19', '2026-09-18', '2026-10-16',
  '2026-11-20', '2026-12-11',
];
bingoTermine.forEach((d) => regelmaessig.push({
  name: 'BINGO-Abend',
  datum: d,
  kategorie: 'Spieleabend',
  ort: 'Mettgenpin_1877',
  indoorOutdoor: 'Indoor',
  status: 'Bestaetigt',
  einlass: '19:00',
  start: '19:30',
  socialMediaNoetig: true,
}));

// Quizabende - monatlich (Donnerstags)
const quizTermine = [
  '2026-01-22', '2026-02-19', '2026-03-19', '2026-04-23',
  '2026-05-21', '2026-06-18', '2026-09-24', '2026-10-22',
  '2026-11-19',
];
quizTermine.forEach((d) => regelmaessig.push({
  name: 'Quizabend',
  datum: d,
  kategorie: 'Spieleabend',
  ort: 'Mettgenpin_1877',
  indoorOutdoor: 'Indoor',
  status: 'Bestaetigt',
  einlass: '19:00',
  start: '19:30',
}));

// Afterwork Vibes - monatlich (Donnerstags)
const afterworkTermine = [
  '2026-01-29', '2026-02-26', '2026-03-26', '2026-04-30',
  '2026-05-28', '2026-06-25', '2026-09-17', '2026-10-29',
  '2026-11-26',
];
afterworkTermine.forEach((d) => regelmaessig.push({
  name: 'Afterwork Vibes',
  datum: d,
  kategorie: 'Afterwork',
  ort: 'Mettgenpin_1877',
  indoorOutdoor: 'Beides',
  status: 'Bestaetigt',
  start: '17:00',
  socialMediaNoetig: true,
}));

// Wohnzimmerkonzerte - alle 2 Monate
const wohnzimmerTermine = [
  '2026-02-07', '2026-04-11', '2026-06-06',
  '2026-09-05', '2026-11-07', '2026-12-05',
];
wohnzimmerTermine.forEach((d) => regelmaessig.push({
  name: 'Wohnzimmerkonzert',
  datum: d,
  kategorie: 'Live_Musik',
  ort: 'Mettgenpin_1877',
  flaeche: 'Gesellschaftsraum',
  indoorOutdoor: 'Indoor',
  status: 'Bestaetigt',
  einlass: '19:00',
  start: '20:00',
  socialMediaNoetig: true,
  prioritaet: 'Hoch',
}));

// ---------------------------------------------------------------------------
// Feiertage / Brauchtum
// ---------------------------------------------------------------------------

const feiertage: SeedEvent[] = [
  {
    name: 'Silvester-Party',
    datum: '2025-12-31',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Schaenke_1998',
    indoorOutdoor: 'Indoor',
    status: 'Bestaetigt',
    socialMediaNoetig: true,
    prioritaet: 'Hoch',
    einlass: '20:00',
    start: '21:00',
    anlass: 'Jahreswechsel 2025/2026',
  },
  {
    name: 'Valentinstag-Dinner',
    datum: '2026-02-14',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Indoor',
    status: 'Offen',
    cateringJa: true,
    socialMediaNoetig: true,
    einlass: '18:00',
  },
  {
    name: 'Weiberfastnacht',
    datum: '2026-02-12',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Schaenke_1998',
    indoorOutdoor: 'Indoor',
    status: 'Bestaetigt',
    socialMediaNoetig: true,
  },
  {
    name: 'Rosenmontag-Party',
    datum: '2026-02-16',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Schaenke_1998',
    indoorOutdoor: 'Indoor',
    status: 'Bestaetigt',
    socialMediaNoetig: true,
  },
  {
    name: 'Tanz in den Mai',
    datum: '2026-04-30',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Schaenke_1998',
    indoorOutdoor: 'Beides',
    status: 'Bestaetigt',
    socialMediaNoetig: true,
    prioritaet: 'Hoch',
  },
  {
    name: 'Muttertags-Brunch',
    datum: '2026-05-10',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Offen',
    einlass: '10:00',
    start: '11:00',
  },
  {
    name: 'Vatertag am Foodtruck',
    datum: '2026-05-14',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Foodtruck',
    indoorOutdoor: 'Outdoor',
    cateringJa: true,
    status: 'Bestaetigt',
  },
  {
    name: 'Halloween-Party',
    datum: '2026-10-31',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Schaenke_1998',
    indoorOutdoor: 'Indoor',
    status: 'Offen',
    socialMediaNoetig: true,
  },
  {
    name: 'Nikolaus-Abend',
    datum: '2026-12-06',
    kategorie: 'Feiertag_Brauchtum',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Indoor',
    status: 'Offen',
  },
];

// ---------------------------------------------------------------------------
// WM 2026 (11.06.–19.07.2026)
// ---------------------------------------------------------------------------

const wm: SeedEvent[] = [
  { name: 'WM 2026 – Eröffnungsspiel Public Viewing', datum: '2026-06-11',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Bestaetigt', socialMediaNoetig: true, prioritaet: 'Hoch' },
  { name: 'WM 2026 – Gruppenphase Deutschland Spiel 1', datum: '2026-06-13',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Bestaetigt', socialMediaNoetig: true, prioritaet: 'Hoch' },
  { name: 'WM 2026 – Gruppenphase Deutschland Spiel 2', datum: '2026-06-18',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Bestaetigt', socialMediaNoetig: true, prioritaet: 'Hoch' },
  { name: 'WM 2026 – Gruppenphase Deutschland Spiel 3', datum: '2026-06-23',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Bestaetigt', socialMediaNoetig: true, prioritaet: 'Hoch' },
  { name: 'WM 2026 – Achtelfinale Public Viewing', datum: '2026-06-30',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Bestaetigt', socialMediaNoetig: true, prioritaet: 'Hoch' },
  { name: 'WM 2026 – Viertelfinale Public Viewing', datum: '2026-07-04',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Bestaetigt', socialMediaNoetig: true, prioritaet: 'Hoch' },
  { name: 'WM 2026 – Halbfinale Public Viewing', datum: '2026-07-14',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Bestaetigt', socialMediaNoetig: true, prioritaet: 'Hoch' },
  { name: 'WM 2026 – Spiel um Platz 3', datum: '2026-07-18',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Offen', socialMediaNoetig: true },
  { name: 'WM 2026 – Finale Public Viewing', datum: '2026-07-19',
    kategorie: 'WM_Sport', ort: 'Schaenke_1998', indoorOutdoor: 'Beides',
    status: 'Bestaetigt', socialMediaNoetig: true, prioritaet: 'Hoch',
    bemerkungen: 'Großer Public-Viewing-Event, Biergarten nutzen' },
];

// ---------------------------------------------------------------------------
// Private Feiern
// ---------------------------------------------------------------------------

const privateFeiern: SeedEvent[] = [
  {
    name: 'Kommunion Sabine Fobbe',
    datum: '2026-05-03',
    kategorie: 'Feier_Privat',
    ort: 'Extern',
    ortDetails: 'Familie Fobbe, Iserlohn',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Fobbe, Sabine',
    personenanzahl: 35,
    preisProPerson: 28,
    prioritaet: 'Mittel',
  },
  {
    name: 'Kommunion David Butzek',
    datum: '2026-05-17',
    kategorie: 'Feier_Privat',
    ort: 'Mettgenpin_1877',
    flaeche: 'Gesellschaftsraum',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Butzek, Familie David',
    personenanzahl: 28,
    preisProPerson: 26,
  },
  {
    name: '90. Geburtstag Doris Dämmer',
    datum: '2026-05-09',
    kategorie: 'Feier_Privat',
    ort: 'Mettgenpin_1877',
    flaeche: 'Gesellschaftsraum',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Dämmer, Claudia',
    ansprechpartner: 'Claudia252516@web.de / 237262001',
    personenanzahl: 35,
    preisProPerson: 25,
    einlass: '11:30',
    start: '12:20',
    prioritaet: 'Hoch',
    bemerkungen: 'Jubilarin macht einen Fallschirmsprung! Torte: Felsenmeertorte Heermann "90."',
  },
  {
    name: 'Geburtstag Kleinert',
    datum: '2026-06-06',
    kategorie: 'Feier_Privat',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Offen',
    auftraggeber: 'Kleinert',
    personenanzahl: 20,
  },
  {
    name: 'Geburtstag Sandy Fischer',
    datum: '2026-08-15',
    kategorie: 'Feier_Privat',
    ort: 'Extern',
    ortDetails: 'Privatadresse Fischer',
    indoorOutdoor: 'Outdoor',
    cateringJa: true,
    status: 'Anfrage',
    auftraggeber: 'Fischer, Sandy',
    personenanzahl: 40,
  },
  {
    name: 'Konfirmation Familie Werner',
    datum: '2026-04-12',
    kategorie: 'Feier_Privat',
    ort: 'Mettgenpin_1877',
    flaeche: 'Gesellschaftsraum',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Werner, Familie',
    personenanzahl: 30,
    preisProPerson: 27,
  },
  {
    name: 'Hochzeit Ihmert',
    datum: '2026-08-22',
    kategorie: 'Feier_Privat',
    ort: 'Extern',
    ortDetails: 'Ihmert',
    indoorOutdoor: 'Beides',
    cateringJa: true,
    eventJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Brautpaar Ihmert',
    personenanzahl: 90,
    preisProPerson: 55,
    prioritaet: 'Hoch',
    socialMediaNoetig: false,
    bemerkungen: 'Großhochzeit, Team-Koordination besonders wichtig',
  },
];

// ---------------------------------------------------------------------------
// Catering extern (inkl. 4 Detail-Events)
// ---------------------------------------------------------------------------

const catering: SeedEvent[] = [
  {
    name: 'Foodtruck – Runkel / Lexware',
    datum: '2026-07-04',
    kategorie: 'Catering',
    ort: 'Foodtruck',
    ortDetails: 'Nikolaus-Groß-Str. 19, 58706 Menden',
    indoorOutdoor: 'Outdoor',
    cateringJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Lexware GmbH & Co. KG',
    ansprechpartner: 'Silvia & Dietmar',
    personenanzahl: 60,
    preisProPerson: 25,
    start: '17:00',
    ende: '21:00',
    prioritaet: 'Hoch',
    bemerkungen: 'Angebot 2025-0042, 1.500€ brutto. 3 Stehtische, Strom 16-32A, Stellfläche 6x4m',
  },
  {
    name: 'Boro – Steffis Geburtstag (Abholung)',
    datum: '2026-04-25',
    kategorie: 'Catering',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Boro, Steffi',
    personenanzahl: 25,
    preisProPerson: 22,
    start: '16:00',
    bemerkungen: 'Abholung 16:00 durch Kunden. Griechisch: Gyros Selbstschnitt, Pita, Zaziki etc.',
  },
  {
    name: 'Ruberg – Tennisplatz Grillen',
    datum: '2026-05-23',
    kategorie: 'Catering',
    ort: 'Extern',
    ortDetails: 'Jägerstraße Tennisplätze Westig',
    indoorOutdoor: 'Outdoor',
    cateringJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Ruberg (Tennisverein Westig)',
    ansprechpartner: 'Telefon: 15170130934',
    personenanzahl: 75,
    preisProPerson: 26.90,
    start: '18:00',
    ende: '22:00',
    bemerkungen: 'Imbiss Hercules. Feste Zahl 14 Tage vorher. 18:30-22:00 Essen',
  },
  {
    name: 'Bornfelder Sommerfest',
    datum: '2026-07-11',
    kategorie: 'Catering',
    ort: 'Extern',
    ortDetails: 'Bornfelder',
    indoorOutdoor: 'Outdoor',
    cateringJa: true,
    status: 'Bestaetigt',
    auftraggeber: 'Bornfelder',
    personenanzahl: 120,
    preisProPerson: 24,
    bemerkungen: 'Provision/Rabatt Bornfelder',
  },
  {
    name: 'Bornfelder Herbstempfang',
    datum: '2026-09-12',
    kategorie: 'Catering',
    ort: 'Extern',
    ortDetails: 'Bornfelder',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Offen',
    auftraggeber: 'Bornfelder',
    personenanzahl: 80,
    preisProPerson: 24,
  },
  {
    name: 'Bornfelder Jahresabschluss',
    datum: '2026-11-28',
    kategorie: 'Catering',
    ort: 'Extern',
    ortDetails: 'Bornfelder',
    indoorOutdoor: 'Indoor',
    cateringJa: true,
    status: 'Offen',
    auftraggeber: 'Bornfelder',
    personenanzahl: 45,
    preisProPerson: 25,
  },
];

// ---------------------------------------------------------------------------
// Konzerte & Live-Musik
// ---------------------------------------------------------------------------

const konzerte: SeedEvent[] = [
  {
    name: 'Andreas Ruhnke – Delta Blues',
    datum: '2026-03-14',
    kategorie: 'Live_Musik',
    ort: 'Mettgenpin_1877',
    flaeche: 'Gesellschaftsraum',
    indoorOutdoor: 'Indoor',
    status: 'Bestaetigt',
    socialMediaNoetig: true,
    prioritaet: 'Hoch',
    einlass: '19:00',
    start: '20:00',
  },
  {
    name: 'Duo Cassidi Live',
    datum: '2026-05-16',
    kategorie: 'Live_Musik',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Beides',
    status: 'Bestaetigt',
    socialMediaNoetig: true,
    einlass: '19:00',
    start: '20:00',
  },
  {
    name: 'Big Band Abend',
    datum: '2026-09-19',
    kategorie: 'Live_Musik',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Indoor',
    status: 'Bestaetigt',
    socialMediaNoetig: true,
    prioritaet: 'Hoch',
    einlass: '18:30',
    start: '19:30',
  },
  {
    name: 'Dieter Voss – Lieder­abend',
    datum: '2026-10-10',
    kategorie: 'Live_Musik',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Indoor',
    status: 'Offen',
    socialMediaNoetig: true,
    einlass: '19:00',
    start: '20:00',
  },
  {
    name: 'Sauerländer Wirtshaus Musikanten',
    datum: '2026-11-14',
    kategorie: 'Live_Musik',
    ort: 'Mettgenpin_1877',
    indoorOutdoor: 'Indoor',
    status: 'Bestaetigt',
    socialMediaNoetig: true,
    einlass: '18:30',
    start: '19:30',
  },
];

// ---------------------------------------------------------------------------
// Stadtfeste, Messen, Künstlercatering
// ---------------------------------------------------------------------------

const stadtfesteMessen: SeedEvent[] = [
  {
    name: 'Handelshof Köln – Messe',
    datum: '2026-04-29',
    kategorie: 'Stadtfest_Messe',
    ort: 'Extern',
    ortDetails: 'Handelshof Köln',
    indoorOutdoor: 'Indoor',
    status: 'Bestaetigt',
    prioritaet: 'Hoch',
    bemerkungen: 'Messestand, Networking',
  },
  {
    name: 'Künstlercatering Tag 1',
    datum: '2026-04-29',
    kategorie: 'Kuenstlercatering',
    ort: 'Extern',
    cateringJa: true,
    status: 'Bestaetigt',
    personenanzahl: 25,
  },
  {
    name: 'Künstlercatering Tag 2',
    datum: '2026-04-30',
    kategorie: 'Kuenstlercatering',
    ort: 'Extern',
    cateringJa: true,
    status: 'Bestaetigt',
    personenanzahl: 25,
  },
  {
    name: 'Kulturnacht Hemer',
    datum: '2026-06-20',
    kategorie: 'Stadtfest_Messe',
    ort: 'Extern',
    ortDetails: 'Innenstadt Hemer',
    indoorOutdoor: 'Outdoor',
    eventJa: true,
    cateringJa: true,
    socialMediaNoetig: true,
    status: 'Bestaetigt',
    prioritaet: 'Hoch',
  },
  {
    name: 'Genuss pur – Foodfestival',
    datum: '2026-08-08',
    kategorie: 'Stadtfest_Messe',
    ort: 'Foodtruck',
    indoorOutdoor: 'Outdoor',
    cateringJa: true,
    socialMediaNoetig: true,
    status: 'Bestaetigt',
    prioritaet: 'Hoch',
  },
  {
    name: 'Hemeraner Herbsttage – Tag 1',
    datum: '2026-09-25',
    kategorie: 'Stadtfest_Messe',
    ort: 'Extern',
    ortDetails: 'Hemer Innenstadt',
    indoorOutdoor: 'Outdoor',
    eventJa: true, cateringJa: true, socialMediaNoetig: true,
    status: 'Bestaetigt', prioritaet: 'Hoch',
  },
  {
    name: 'Hemeraner Herbsttage – Tag 2',
    datum: '2026-09-26',
    kategorie: 'Stadtfest_Messe',
    ort: 'Extern',
    ortDetails: 'Hemer Innenstadt',
    indoorOutdoor: 'Outdoor',
    eventJa: true, cateringJa: true, socialMediaNoetig: true,
    status: 'Bestaetigt', prioritaet: 'Hoch',
  },
  {
    name: 'Hemeraner Herbsttage – Tag 3',
    datum: '2026-09-27',
    kategorie: 'Stadtfest_Messe',
    ort: 'Extern',
    ortDetails: 'Hemer Innenstadt',
    indoorOutdoor: 'Outdoor',
    eventJa: true, cateringJa: true, socialMediaNoetig: true,
    status: 'Bestaetigt', prioritaet: 'Hoch',
  },
  {
    name: 'Hemeraner Herbsttage – Tag 4',
    datum: '2026-09-28',
    kategorie: 'Stadtfest_Messe',
    ort: 'Extern',
    ortDetails: 'Hemer Innenstadt',
    indoorOutdoor: 'Outdoor',
    eventJa: true, cateringJa: true, socialMediaNoetig: true,
    status: 'Bestaetigt', prioritaet: 'Hoch',
  },
];

// ---------------------------------------------------------------------------
// Export
// ---------------------------------------------------------------------------

export const seedEvents: SeedEvent[] = [
  ...regelmaessig,
  ...feiertage,
  ...wm,
  ...privateFeiern,
  ...catering,
  ...konzerte,
  ...stadtfesteMessen,
];
