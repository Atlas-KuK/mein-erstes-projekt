-- CreateEnum
CREATE TYPE "Rolle" AS ENUM ('Admin', 'Teamleitung', 'Mitarbeiter', 'Kunde', 'Partner');

-- CreateEnum
CREATE TYPE "EventKategorie" AS ENUM ('Party_Musik', 'Spieleabend', 'Live_Musik', 'Feier_Privat', 'Catering', 'WM_Sport', 'Stadtfest_Messe', 'Afterwork', 'Feiertag_Brauchtum', 'Kuenstlercatering', 'Sonstiges');

-- CreateEnum
CREATE TYPE "EventOrt" AS ENUM ('Mettgenpin_1877', 'Schaenke_1998', 'Extern', 'Foodtruck');

-- CreateEnum
CREATE TYPE "IndoorOutdoor" AS ENUM ('Indoor', 'Outdoor', 'Beides');

-- CreateEnum
CREATE TYPE "EventStatusTyp" AS ENUM ('Anfrage', 'Offen', 'In_Bearbeitung', 'Bestaetigt', 'Abgelehnt', 'Abgeschlossen', 'Storniert');

-- CreateEnum
CREATE TYPE "Prioritaet" AS ENUM ('Hoch', 'Mittel', 'Niedrig');

-- CreateEnum
CREATE TYPE "Freigabestatus" AS ENUM ('Offen', 'Freigegeben', 'Zurueckgestellt');

-- CreateEnum
CREATE TYPE "Lieferart" AS ENUM ('Lieferung', 'Abholung', 'Vor_Ort');

-- CreateEnum
CREATE TYPE "ChecklistStatus" AS ENUM ('Offen', 'Erledigt', 'N_A');

-- CreateEnum
CREATE TYPE "DateiTyp" AS ENUM ('Angebot', 'Rechnung', 'Canva', 'GoogleDrive', 'Bild', 'Video', 'PDF', 'Kundenkommunikation', 'Sonstiges');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "passwortHash" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "rolle" "Rolle" NOT NULL DEFAULT 'Mitarbeiter',
    "telefon" TEXT,
    "firma" TEXT,
    "aktiv" BOOLEAN NOT NULL DEFAULT true,
    "dsgvoAkzeptiertAm" TIMESTAMP(3),
    "passwortResetToken" TEXT,
    "passwortResetBis" TIMESTAMP(3),
    "twoFactorSecret" TEXT,
    "twoFactorEnabled" BOOLEAN NOT NULL DEFAULT false,
    "refreshTokenHash" TEXT,
    "refreshTokenExpires" TIMESTAMP(3),
    "erstelltAm" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "aktualisiertAm" TIMESTAMP(3) NOT NULL,
    "letzterLogin" TIMESTAMP(3),

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Event" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "datum" DATE NOT NULL,
    "datumBis" DATE,
    "wochentag" TEXT NOT NULL,
    "monat" TEXT NOT NULL,
    "kalenderwoche" INTEGER NOT NULL,
    "kategorie" "EventKategorie" NOT NULL,
    "anlass" TEXT,
    "ort" "EventOrt" NOT NULL,
    "ortDetails" TEXT,
    "flaeche" TEXT,
    "indoorOutdoor" "IndoorOutdoor",
    "wetterfallback" TEXT,
    "aufbau" TIMESTAMP(3),
    "einlass" TIMESTAMP(3),
    "start" TIMESTAMP(3),
    "ende" TIMESTAMP(3),
    "abbau" TIMESTAMP(3),
    "status" "EventStatusTyp" NOT NULL DEFAULT 'Anfrage',
    "prioritaet" "Prioritaet" NOT NULL DEFAULT 'Mittel',
    "freigabestatus" "Freigabestatus" NOT NULL DEFAULT 'Offen',
    "cateringJa" BOOLEAN NOT NULL DEFAULT false,
    "eventJa" BOOLEAN NOT NULL DEFAULT true,
    "socialMediaNoetig" BOOLEAN NOT NULL DEFAULT false,
    "auftraggeber" TEXT,
    "auftraggeberId" TEXT,
    "ansprechpartner" TEXT,
    "bearbeiterInternId" TEXT,
    "provision" TEXT,
    "preisProPerson" DECIMAL(10,2),
    "personenanzahl" INTEGER,
    "gesamtpreis" DECIMAL(10,2),
    "anzahlungErhalten" BOOLEAN NOT NULL DEFAULT false,
    "anzahlungBetrag" DECIMAL(10,2),
    "bemerkungen" TEXT,
    "erstelltAm" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "aktualisiertAm" TIMESTAMP(3) NOT NULL,
    "erstelltVonId" TEXT,

    CONSTRAINT "Event_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventCatering" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "personenanzahl" INTEGER,
    "speisen" TEXT,
    "getraenke" TEXT,
    "lieferungAbholung" "Lieferart",
    "equipment" TEXT,
    "allergene" TEXT,
    "kuechenhinweise" TEXT,
    "servicehinweise" TEXT,
    "offenePunkte" TEXT,
    "aktualisiertAm" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EventCatering_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventAblauf" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "zielDesEvents" TEXT,
    "ablaufplan" TEXT,
    "technikBedarf" TEXT,
    "personalbedarf" TEXT,
    "djMusik" TEXT,
    "dekoAusstattung" TEXT,
    "offenePunkte" TEXT,
    "aktualisiertAm" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EventAblauf_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventMarketing" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "kernbotschaft" TEXT,
    "textbausteine" TEXT,
    "plakatbriefing" TEXT,
    "socialMediaPlan" TEXT,
    "videokonzept" TEXT,
    "regiebuch" TEXT,
    "assetLinks" TEXT,
    "referenzbilder" TEXT,
    "freigabestatus" "ChecklistStatus" NOT NULL DEFAULT 'Offen',
    "deadline" DATE,
    "aktualisiertAm" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EventMarketing_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventArbeitsanweisung" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "kueche" TEXT,
    "service" TEXT,
    "einkauf" TEXT,
    "logistikFahrer" TEXT,
    "technik" TEXT,
    "deko" TEXT,
    "nachbereitung" TEXT,
    "aktualisiertAm" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EventArbeitsanweisung_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventStatusCheckliste" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "angebotStatus" "ChecklistStatus" NOT NULL DEFAULT 'Offen',
    "kundeBestaetigt" BOOLEAN NOT NULL DEFAULT false,
    "anzahlungErhalten" BOOLEAN NOT NULL DEFAULT false,
    "marketingErledigt" "ChecklistStatus" NOT NULL DEFAULT 'Offen',
    "arbeitsanweisungErstellt" "ChecklistStatus" NOT NULL DEFAULT 'Offen',
    "eventblattVollstaendig" BOOLEAN NOT NULL DEFAULT false,
    "aktualisiertAm" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "EventStatusCheckliste_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "EventDatei" (
    "id" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "typ" "DateiTyp" NOT NULL,
    "name" TEXT NOT NULL,
    "url" TEXT,
    "dateiPfad" TEXT,
    "erstelltAm" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "EventDatei_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditLog" (
    "id" TEXT NOT NULL,
    "userId" TEXT,
    "aktion" TEXT NOT NULL,
    "eventId" TEXT,
    "details" JSONB,
    "zeitpunkt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ipAdresse" TEXT,

    CONSTRAINT "AuditLog_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "User_passwortResetToken_key" ON "User"("passwortResetToken");

-- CreateIndex
CREATE INDEX "User_email_idx" ON "User"("email");

-- CreateIndex
CREATE INDEX "User_rolle_idx" ON "User"("rolle");

-- CreateIndex
CREATE UNIQUE INDEX "Event_eventId_key" ON "Event"("eventId");

-- CreateIndex
CREATE INDEX "Event_datum_idx" ON "Event"("datum");

-- CreateIndex
CREATE INDEX "Event_status_idx" ON "Event"("status");

-- CreateIndex
CREATE INDEX "Event_kategorie_idx" ON "Event"("kategorie");

-- CreateIndex
CREATE INDEX "Event_ort_idx" ON "Event"("ort");

-- CreateIndex
CREATE INDEX "Event_bearbeiterInternId_idx" ON "Event"("bearbeiterInternId");

-- CreateIndex
CREATE INDEX "Event_auftraggeberId_idx" ON "Event"("auftraggeberId");

-- CreateIndex
CREATE UNIQUE INDEX "EventCatering_eventId_key" ON "EventCatering"("eventId");

-- CreateIndex
CREATE UNIQUE INDEX "EventAblauf_eventId_key" ON "EventAblauf"("eventId");

-- CreateIndex
CREATE UNIQUE INDEX "EventMarketing_eventId_key" ON "EventMarketing"("eventId");

-- CreateIndex
CREATE UNIQUE INDEX "EventArbeitsanweisung_eventId_key" ON "EventArbeitsanweisung"("eventId");

-- CreateIndex
CREATE UNIQUE INDEX "EventStatusCheckliste_eventId_key" ON "EventStatusCheckliste"("eventId");

-- CreateIndex
CREATE INDEX "EventDatei_eventId_idx" ON "EventDatei"("eventId");

-- CreateIndex
CREATE INDEX "AuditLog_userId_idx" ON "AuditLog"("userId");

-- CreateIndex
CREATE INDEX "AuditLog_eventId_idx" ON "AuditLog"("eventId");

-- CreateIndex
CREATE INDEX "AuditLog_zeitpunkt_idx" ON "AuditLog"("zeitpunkt");

-- AddForeignKey
ALTER TABLE "Event" ADD CONSTRAINT "Event_auftraggeberId_fkey" FOREIGN KEY ("auftraggeberId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Event" ADD CONSTRAINT "Event_bearbeiterInternId_fkey" FOREIGN KEY ("bearbeiterInternId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Event" ADD CONSTRAINT "Event_erstelltVonId_fkey" FOREIGN KEY ("erstelltVonId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventCatering" ADD CONSTRAINT "EventCatering_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "Event"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventAblauf" ADD CONSTRAINT "EventAblauf_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "Event"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventMarketing" ADD CONSTRAINT "EventMarketing_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "Event"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventArbeitsanweisung" ADD CONSTRAINT "EventArbeitsanweisung_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "Event"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventStatusCheckliste" ADD CONSTRAINT "EventStatusCheckliste_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "Event"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "EventDatei" ADD CONSTRAINT "EventDatei_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "Event"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditLog" ADD CONSTRAINT "AuditLog_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditLog" ADD CONSTRAINT "AuditLog_eventId_fkey" FOREIGN KEY ("eventId") REFERENCES "Event"("id") ON DELETE SET NULL ON UPDATE CASCADE;
