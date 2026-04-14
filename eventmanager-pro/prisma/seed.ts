import { PrismaClient, Prisma } from '@prisma/client';
import { hashPassword, generateInitialPassword } from '../src/lib/auth';
import { seedEvents, SeedEvent } from './seed-events';

const prisma = new PrismaClient();

// ---------------------------------------------------------------------------
// Helfer
// ---------------------------------------------------------------------------

const WOCHENTAGE = [
  'Sonntag', 'Montag', 'Dienstag', 'Mittwoch',
  'Donnerstag', 'Freitag', 'Samstag',
];
const MONATE = [
  'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
  'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember',
];

function kalenderwoche(d: Date): number {
  // ISO-8601 Woche
  const target = new Date(d.valueOf());
  const dayNr = (d.getDay() + 6) % 7;
  target.setDate(target.getDate() - dayNr + 3);
  const firstThursday = target.valueOf();
  target.setMonth(0, 1);
  if (target.getDay() !== 4) {
    target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
  }
  return 1 + Math.ceil((firstThursday - target.valueOf()) / 604800000);
}

function combineDateTime(dateStr: string, timeStr?: string): Date | null {
  if (!timeStr) return null;
  return new Date(`${dateStr}T${timeStr}:00`);
}

function eventIdFor(dateStr: string, seq: number): string {
  return `E${dateStr.replaceAll('-', '')}-${String(seq).padStart(3, '0')}`;
}

// ---------------------------------------------------------------------------
// Admin-User
// ---------------------------------------------------------------------------

async function seedAdmin(): Promise<string> {
  const email = 'polikarpos@luckyevent.de';
  const existing = await prisma.user.findUnique({ where: { email } });
  if (existing) {
    console.log(`[seed] Admin existiert bereits: ${email}`);
    return existing.id;
  }

  const passwort = generateInitialPassword(16);
  const admin = await prisma.user.create({
    data: {
      email,
      name: 'Polikarpos Karafoulidis',
      rolle: 'Admin',
      firma: 'Lucky Event',
      passwortHash: await hashPassword(passwort),
      dsgvoAkzeptiertAm: new Date(),
    },
  });

  console.log('');
  console.log('════════════════════════════════════════════════════════════');
  console.log('  ADMIN-ACCOUNT ANGELEGT – NOTIERE DIESES PASSWORT!');
  console.log('════════════════════════════════════════════════════════════');
  console.log(`  E-Mail:   ${email}`);
  console.log(`  Passwort: ${passwort}`);
  console.log('════════════════════════════════════════════════════════════');
  console.log('  (Wird beim nächsten Seed NICHT erneut gezeigt)');
  console.log('');
  return admin.id;
}

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

async function seedEventsData(erstelltVonId: string) {
  // Vorhandene Events prüfen
  const existing = await prisma.event.count();
  if (existing > 0) {
    console.log(`[seed] Überspringe Events: ${existing} bereits vorhanden`);
    return;
  }

  // Events nach Datum sortieren, um laufende Nummer pro Tag zu bilden
  const sorted = [...seedEvents].sort((a, b) => a.datum.localeCompare(b.datum));
  const counterPerDay = new Map<string, number>();

  for (const e of sorted) {
    const datum = new Date(`${e.datum}T00:00:00`);
    const seq = (counterPerDay.get(e.datum) ?? 0) + 1;
    counterPerDay.set(e.datum, seq);

    const eventData: Prisma.EventCreateInput = {
      eventId: eventIdFor(e.datum, seq),
      name: e.name,
      datum,
      datumBis: e.datumBis ? new Date(`${e.datumBis}T00:00:00`) : null,
      wochentag: WOCHENTAGE[datum.getDay()],
      monat: MONATE[datum.getMonth()],
      kalenderwoche: kalenderwoche(datum),
      kategorie: e.kategorie,
      ort: e.ort,
      ortDetails: e.ortDetails ?? null,
      flaeche: e.flaeche ?? null,
      indoorOutdoor: e.indoorOutdoor ?? null,
      anlass: e.anlass ?? null,
      status: e.status ?? 'Anfrage',
      prioritaet: e.prioritaet ?? 'Mittel',
      cateringJa: e.cateringJa ?? false,
      eventJa: e.eventJa ?? true,
      socialMediaNoetig: e.socialMediaNoetig ?? false,
      auftraggeber: e.auftraggeber ?? null,
      ansprechpartner: e.ansprechpartner ?? null,
      personenanzahl: e.personenanzahl ?? null,
      preisProPerson: e.preisProPerson !== undefined
        ? new Prisma.Decimal(e.preisProPerson) : null,
      gesamtpreis: (e.preisProPerson !== undefined && e.personenanzahl !== undefined)
        ? new Prisma.Decimal(e.preisProPerson * e.personenanzahl)
        : null,
      einlass: combineDateTime(e.datum, e.einlass),
      start: combineDateTime(e.datum, e.start),
      ende: combineDateTime(e.datum, e.ende),
      bemerkungen: e.bemerkungen ?? null,
      erstelltVon: { connect: { id: erstelltVonId } },
      statusCheckliste: { create: {} },
    };

    await prisma.event.create({ data: eventData });
  }

  console.log(`[seed] ${sorted.length} Events angelegt`);
}

// ---------------------------------------------------------------------------
// Detail-Eventblätter (4 Events)
// ---------------------------------------------------------------------------

async function seedDetailEventblaetter() {
  // 1) Runkel – Foodtruck Firmenevent
  const runkel = await prisma.event.findFirst({
    where: { name: { contains: 'Runkel' } },
  });
  if (runkel) {
    await prisma.eventCatering.upsert({
      where: { eventId: runkel.id },
      update: {},
      create: {
        eventId: runkel.id,
        personenanzahl: 60,
        speisen: [
          'Gyros (Drehspieß, Selbstschnitt)',
          'Currywurst mit Pommes',
          'Falafel vegetarisch',
          'Pommes frites',
          'Krautsalat',
        ].join('\n'),
        getraenke: 'Kunde stellt Getränke selbst',
        lieferungAbholung: 'Vor_Ort',
        equipment: '3 Stehtische, Stromanschluss 16-32A, Stellfläche 6x4m',
        allergene: 'Glutenfreie Variante auf Anfrage',
        kuechenhinweise: 'Foodtruck komplett ausgestattet, Gasflaschen-Reserve mitnehmen',
        servicehinweise: 'Ausgabe direkt am Truck, 17:00 Start',
      },
    });
    await prisma.eventAblauf.upsert({
      where: { eventId: runkel.id },
      update: {},
      create: {
        eventId: runkel.id,
        zielDesEvents: 'Lexware-Firmensommerfest',
        ablaufplan: '15:00 Anreise/Aufbau\n17:00 Gäste-Eintreffen, Ausgabe\n18:30 Hauptandrang\n21:00 Ende\n21:30 Abbau',
        technikBedarf: 'Stromanschluss 16-32A am Stellplatz',
        personalbedarf: '1 Fahrer, 1 Koch, 1 Ausgabe',
        dekoAusstattung: 'Truck-Branding Mettgenpin',
      },
    });
    await prisma.eventArbeitsanweisung.upsert({
      where: { eventId: runkel.id },
      update: {},
      create: {
        eventId: runkel.id,
        kueche: 'Fleisch vorgegart mitnehmen, Gyros-Spieß frisch, Pommes-Fritteuse heißlaufen lassen',
        logistikFahrer: 'Abfahrt 14:00, Tankfüllung checken, Gasflaschen-Reserve',
        service: 'Ausgabefenster sauber halten, Nachschub-Rhythmus 15 Min',
        einkauf: 'Tag zuvor: 15kg Gyros, 60 Pita, 10kg Pommes, 3kg Falafel',
        nachbereitung: 'Truck reinigen, Restbestände inventieren',
      },
    });
  }

  // 2) Boro – Steffis Geburtstag
  const boro = await prisma.event.findFirst({
    where: { name: { contains: 'Boro' } },
  });
  if (boro) {
    await prisma.eventCatering.upsert({
      where: { eventId: boro.id },
      update: {},
      create: {
        eventId: boro.id,
        personenanzahl: 25,
        speisen: [
          'Gyros (Selbstschnitt vom Drehspieß)',
          'Pita-Brot',
          'Zaziki',
          'Krautsalat',
          'Bauernsalat',
          'Oliven',
          'Peperoni',
          'Zwiebeln',
          'Rosmarinkartoffeln',
          'Djuvec-Reis',
        ].join('\n'),
        lieferungAbholung: 'Abholung',
        equipment: 'Porzellan, Besteck, 3 Chafing Dishes, Messer',
        allergene: 'Enthält Knoblauch, Milchprodukte',
        kuechenhinweise: 'Gasflasche vorhanden. 2-3 Packungen Pita zusätzlich einpacken',
        servicehinweise: 'Abholung 16:00 durch Kunden',
      },
    });
  }

  // 3) Ruberg – Tennisplatz
  const ruberg = await prisma.event.findFirst({
    where: { name: { contains: 'Ruberg' } },
  });
  if (ruberg) {
    await prisma.eventCatering.upsert({
      where: { eventId: ruberg.id },
      update: {},
      create: {
        eventId: ruberg.id,
        personenanzahl: 75,
        speisen: [
          'Pita 2 Go',
          'Taxiteller',
          'Pommes',
          'Zaziki',
          'Krautsalat',
          'Bauernsalat',
        ].join('\n'),
        lieferungAbholung: 'Vor_Ort',
        equipment: 'Imbiss Hercules, mobile Ausstattung',
        kuechenhinweise: 'Feste Personenzahl 14 Tage vorher bestätigen',
        servicehinweise: '18:00 Start, 18:30-22:00 Essen',
      },
    });
    await prisma.eventAblauf.upsert({
      where: { eventId: ruberg.id },
      update: {},
      create: {
        eventId: ruberg.id,
        ablaufplan: '16:00 Anreise/Aufbau\n18:00 Offizieller Start\n18:30–22:00 Essen\n22:30 Abbau',
        personalbedarf: '1 Fahrer, 2 Ausgabe, 1 Grill',
        offenePunkte: '- Finale Personenzahl (14 Tage vorher)\n- Wetter-Fallback',
      },
    });
  }

  // 4) Dämmer – 90. Geburtstag
  const daemmer = await prisma.event.findFirst({
    where: { name: { contains: 'Dämmer' } },
  });
  if (daemmer) {
    await prisma.eventCatering.upsert({
      where: { eventId: daemmer.id },
      update: {},
      create: {
        eventId: daemmer.id,
        personenanzahl: 35,
        speisen: [
          'Hähnchengeschnetzeltes',
          'Schweinefilet-Medaillons mit Béarnaise',
          'Kaisergemüse',
          'Rosmarinkartoffeln',
          'Pommes',
          'Zaziki',
          'Krautsalat',
          'Gemischter Salat',
          'Oliven, Peperoni',
          '—',
          'Torten: 2× Blech (Apfel + Erdbeer) + Sahne',
          '1× Felsenmeertorte Heermann mit "90."',
        ].join('\n'),
        getraenke: 'Kaffee normal UND entkoffeiniert',
        lieferungAbholung: 'Vor_Ort',
        allergene: 'Laktose-Info bei Torten',
        servicehinweise: '11:30 Einlass, 12:20 Essen',
      },
    });
    await prisma.eventAblauf.upsert({
      where: { eventId: daemmer.id },
      update: {},
      create: {
        eventId: daemmer.id,
        zielDesEvents: '90. Geburtstag Doris Dämmer – herzliche Familienfeier',
        ablaufplan: [
          '11:30 Einlass, Sekt-Empfang',
          '12:20 Essen',
          '14:30 Kaffee & Torten',
          '15:00 Fallschirmsprung der Jubilarin (!)',
          '17:00 Ausklang',
        ].join('\n'),
        personalbedarf: '2 Service, 1 Küche',
        dekoAusstattung: 'Tische eingedeckt, Blumenschmuck, "90"-Banner',
        offenePunkte: '- Landezone-Abstimmung Fallschirmsprung\n- Kaffeeauswahl bestätigen',
      },
    });
    await prisma.eventArbeitsanweisung.upsert({
      where: { eventId: daemmer.id },
      update: {},
      create: {
        eventId: daemmer.id,
        kueche: 'Hähnchengeschnetzeltes warmhalten, Medaillons à la minute. Béarnaise frisch.',
        service: 'Sekt-Empfang 11:30, Essen 12:20, Torten 14:30. Kaffee nachfüllen.',
        einkauf: '35 Portionen einkalkulieren. Torte Heermann 2 Tage vorher bestellen.',
        deko: '"90" Banner, Blumen in Gold/Weiß, Tischkarten',
        nachbereitung: 'Gesellschaftsraum um 17:30 reinigen',
      },
    });
  }

  console.log('[seed] Detail-Eventblätter für Runkel, Boro, Ruberg, Dämmer angelegt');
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function main() {
  console.log('[seed] Starte Seed für EventManager Pro...');
  const adminId = await seedAdmin();
  await seedEventsData(adminId);
  await seedDetailEventblaetter();
  console.log('[seed] Fertig.');
}

main()
  .catch((err) => {
    console.error('[seed] Fehler:', err);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
