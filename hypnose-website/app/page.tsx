import Link from "next/link";

/**
 * Landing Page – Phase-1-Skelett
 *
 * Inhalte sind Platzhalter und werden in den nächsten Iterationen ersetzt:
 * - Name/Marke
 * - Methodenbeschreibung & Über-mich-Text
 * - Finale Preise (Hypnovita-Move: transparent kommunizieren)
 * - Testimonials
 * - FAQ
 * - Kontaktformular-Backend (vorerst nur mailto:)
 */

const services = [
  {
    title: "Einzelsitzung",
    description:
      "Individuelles Coaching — persönlich in Hemer oder online per Zoom. Für Themen wie Stress, Ängste, Selbstvertrauen, Zielerreichung.",
    highlight: "1:1",
  },
  {
    title: "Gruppensitzung",
    description:
      "Gemeinsam in geschütztem Rahmen tiefer eintauchen. Für kleine Gruppen, Workshops und Firmen-Events.",
    highlight: "Gruppe",
  },
  {
    title: "Online-Programm",
    description:
      "Strukturierte Begleitung per Zoom über mehrere Wochen — für nachhaltige Veränderung von zu Hause aus.",
    highlight: "Online",
  },
];

export default function Home() {
  return (
    <>
      {/* Navigation */}
      <header className="w-full border-b border-[color:var(--border)]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <Link
            href="/"
            className="text-lg font-semibold tracking-tight text-[color:var(--accent)]"
          >
            {/* TODO: Marken-/Logoname */}
            Hypnose Coaching
          </Link>
          <nav className="hidden gap-8 text-sm text-[color:var(--muted)] sm:flex">
            <a href="#angebot" className="hover:text-foreground">
              Angebot
            </a>
            <a href="#ueber-mich" className="hover:text-foreground">
              Über mich
            </a>
            <a href="#kontakt" className="hover:text-foreground">
              Kontakt
            </a>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="mx-auto flex max-w-6xl flex-col items-start gap-6 px-6 py-24 sm:py-32">
        <span className="rounded-full border border-[color:var(--border)] px-3 py-1 text-xs uppercase tracking-wider text-[color:var(--muted)]">
          Hemer · Online · Zoom
        </span>
        <h1 className="max-w-3xl text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">
          Veränderung, die bleibt — durch{" "}
          <span className="text-[color:var(--accent)]">Hypnose Coaching</span>.
        </h1>
        <p className="max-w-2xl text-lg leading-8 text-[color:var(--muted)]">
          Einzel-, Gruppen- und Online-Sitzungen für Menschen, die echte
          Veränderung wollen. Persönlich in 58675 Hemer oder deutschlandweit per
          Zoom.
        </p>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row">
          <a
            href="#kontakt"
            className="inline-flex h-12 items-center justify-center rounded-full bg-[color:var(--accent)] px-7 text-sm font-semibold text-black transition-colors hover:bg-[color:var(--accent-hover)]"
          >
            Kostenloses Erstgespräch
          </a>
          <a
            href="#angebot"
            className="inline-flex h-12 items-center justify-center rounded-full border border-[color:var(--border)] px-7 text-sm font-medium text-foreground transition-colors hover:bg-[color:var(--surface)]"
          >
            Angebote ansehen
          </a>
        </div>
      </section>

      {/* Angebote */}
      <section
        id="angebot"
        className="border-t border-[color:var(--border)] bg-[color:var(--surface)]"
      >
        <div className="mx-auto max-w-6xl px-6 py-24">
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Mein Angebot
          </h2>
          <p className="mt-3 max-w-2xl text-[color:var(--muted)]">
            Drei Wege, mit mir zu arbeiten — wähle das Format, das zu dir passt.
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {services.map((s) => (
              <article
                key={s.title}
                className="flex flex-col gap-4 rounded-2xl border border-[color:var(--border)] bg-background p-7 transition-colors hover:border-[color:var(--accent)]"
              >
                <span className="text-xs font-medium uppercase tracking-wider text-[color:var(--accent)]">
                  {s.highlight}
                </span>
                <h3 className="text-xl font-semibold">{s.title}</h3>
                <p className="text-[color:var(--muted)]">{s.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Über mich (Teaser) */}
      <section id="ueber-mich" className="mx-auto max-w-6xl px-6 py-24">
        <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Über mich
        </h2>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-[color:var(--muted)]">
          {/* TODO: Persönliche Geschichte, Qualifikationen, Methodenansatz */}
          Platzhalter — hier kommt deine Geschichte: Wer bist du, warum machst
          du Hypnose Coaching, für wen arbeitest du?
        </p>
      </section>

      {/* Kontakt */}
      <section
        id="kontakt"
        className="border-t border-[color:var(--border)] bg-[color:var(--surface)]"
      >
        <div className="mx-auto max-w-3xl px-6 py-24 text-center">
          <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Lass uns sprechen
          </h2>
          <p className="mt-4 text-[color:var(--muted)]">
            Kostenloses und unverbindliches Erstgespräch — per E-Mail, Telefon
            oder Zoom.
          </p>
          <a
            href="mailto:hallo@example.de"
            className="mt-8 inline-flex h-12 items-center justify-center rounded-full bg-[color:var(--accent)] px-8 text-sm font-semibold text-black transition-colors hover:bg-[color:var(--accent-hover)]"
          >
            Termin anfragen
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[color:var(--border)]">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-10 text-sm text-[color:var(--muted)] sm:flex-row sm:justify-between">
          <p>© {new Date().getFullYear()} Hypnose Coaching · 58675 Hemer</p>
          <nav className="flex gap-6">
            <a href="#" className="hover:text-foreground">
              Impressum
            </a>
            <a href="#" className="hover:text-foreground">
              Datenschutz
            </a>
          </nav>
        </div>
      </footer>
    </>
  );
}
