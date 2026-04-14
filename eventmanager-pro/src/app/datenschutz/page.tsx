import Link from 'next/link';

export default function DatenschutzPage() {
  return (
    <main className="min-h-screen px-4 py-8 max-w-3xl mx-auto">
      <Link href="/login" className="btn-ghost text-sm mb-4">← Zurück</Link>
      <h1 className="text-3xl font-bold mb-6">Datenschutzerklärung</h1>

      <div className="prose prose-invert max-w-none space-y-4 text-base-200 text-sm">
        <section>
          <h2 className="text-lg font-semibold">1. Verantwortlicher</h2>
          <p>
            Polikarpos Karafoulidis<br />
            Lucky Event / Mettgenpin 1877 / Schänke 1998<br />
            (Adresse wird hier eingetragen)
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold">2. Zweck der Datenverarbeitung</h2>
          <p>
            Diese Anwendung dient der internen Organisation von Veranstaltungen, Catering und
            Personaleinsätzen sowie der Kommunikation mit Kunden und Partnern.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold">3. Erhobene Daten</h2>
          <p>
            Name, E-Mail, Telefon, Firma, Rolle im System, Event-Zuordnung, Login-Zeitpunkte,
            IP-Adresse beim Login (zur Sicherheitsprotokollierung).
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold">4. Rechte der Nutzer</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Auskunft über gespeicherte Daten (DSGVO-Datenexport auf Anfrage)</li>
            <li>Berichtigung unrichtiger Daten</li>
            <li>Löschung personenbezogener Daten</li>
            <li>Widerruf erteilter Einwilligungen</li>
          </ul>
        </section>

        <section>
          <h2 className="text-lg font-semibold">5. Sicherheit</h2>
          <p>
            Passwörter werden mit bcrypt gehasht. Die Verbindung erfolgt per HTTPS. Es werden
            keine Tracking-Cookies oder externen Analytics eingesetzt.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold">6. Kontakt</h2>
          <p>Fragen zum Datenschutz: polikarpos@luckyevent.de</p>
        </section>
      </div>
    </main>
  );
}
