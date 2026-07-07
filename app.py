#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py

Web-Oberflaeche fuer die marktguru-Angebotssuche (Flask).

Funktionen:
  - PLZ + Suchbegriff eingeben -> aktuelle Angebote aus dem Umkreis
  - jeder Abruf wird automatisch in der Preis-Historie (SQLite) gespeichert
  - /historie: gespeicherte Preise + Trend pro Produkt/Haendler

Start lokal:      python app.py          (laeuft auf http://localhost:8080)
Start auf Server: siehe DEPLOY_HETZNER.md (gunicorn + systemd)
"""

import html

from flask import Flask, request

import storage
from marktguru_client import Client, MarktguruError, fmt_date_de

app = Flask(__name__)

DEFAULT_PLZ = "58675"   # Hemer

_client = None


def get_client():
    """Client erst beim ersten Zugriff bauen (Keys koennen fehlen)."""
    global _client
    if _client is None:
        _client = Client()
    return _client


# ---------------------------------------------------------------------------
# HTML-Grundgeruest (bewusst schlicht, keine externen Abhaengigkeiten)
# ---------------------------------------------------------------------------
_PAGE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Angebots-Suche</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 60rem;
         padding: 0 1rem; color: #222; }}
  h1 {{ font-size: 1.4rem; }}
  form {{ display: flex; gap: .5rem; flex-wrap: wrap; margin-bottom: 1rem; }}
  input[type=text] {{ padding: .5rem; font-size: 1rem; }}
  button {{ padding: .5rem 1rem; font-size: 1rem; cursor: pointer; }}
  table {{ border-collapse: collapse; width: 100%; font-size: .95rem; }}
  th, td {{ border: 1px solid #ccc; padding: .4rem .6rem; text-align: left; }}
  th {{ background: #f2f2f2; }}
  tr:nth-child(even) {{ background: #fafafa; }}
  .preis {{ text-align: right; white-space: nowrap; }}
  .hinweis {{ color: #666; font-size: .9rem; }}
  .fehler {{ background: #fdd; border: 1px solid #c00; padding: .8rem; }}
  .hoch {{ color: #c00; font-weight: bold; }}
  .runter {{ color: #080; font-weight: bold; }}
  nav a {{ margin-right: 1rem; }}
</style></head><body>
<nav><a href="/">🔍 Suche</a> <a href="/historie">📈 Preis-Historie</a></nav>
<h1>{titel}</h1>
{inhalt}
</body></html>"""


def _esc(s):
    return html.escape(str(s if s is not None else ""))


def _eur(v):
    if v is None:
        return "?"
    try:
        return f"{float(v):.2f} €".replace(".", ",")
    except (TypeError, ValueError):
        return _esc(v)


# ---------------------------------------------------------------------------
# Seiten
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    plz = (request.args.get("plz") or DEFAULT_PLZ).strip()
    q = (request.args.get("q") or "").strip()

    inhalt = f"""
    <form action="/" method="get">
      <input type="text" name="plz" value="{_esc(plz)}" size="6"
             placeholder="PLZ" title="Postleitzahl">
      <input type="text" name="q" value="{_esc(q)}" size="30"
             placeholder="Produkt, z.B. wodka" autofocus>
      <button type="submit">Suchen</button>
    </form>
    <p class="hinweis">Die Suche fragt marktguru live ab (Angebote im Umkreis
    der PLZ) und speichert jeden Treffer automatisch in der Preis-Historie.</p>
    """

    if q:
        try:
            offers = get_client().search(q, plz)
        except MarktguruError as e:
            inhalt += f'<p class="fehler">Fehler: {_esc(e)}</p>'
            return _PAGE.format(titel="Angebots-Suche", inhalt=inhalt)

        neu = storage.save_offers(offers, plz, q)
        inhalt += (f"<p><b>{len(offers)}</b> Angebote fuer "
                   f"&bdquo;{_esc(q)}&ldquo; im Umkreis von {_esc(plz)} "
                   f"<span class='hinweis'>({neu} neu in Historie "
                   f"gespeichert)</span></p>")

        if offers:
            zeilen = "".join(
                f"<tr><td>{_esc(o['produkt'])}</td>"
                f"<td>{_esc(o['haendler'])}</td>"
                f"<td class='preis'>{_eur(o['preis'])}</td>"
                f"<td>{_esc(o['einheit'])}</td>"
                f"<td>{_esc(fmt_date_de(o['gueltig_bis']))}</td></tr>"
                for o in sorted(offers, key=lambda o: (o["preis"] is None,
                                                       o["preis"] or 0)))
            inhalt += ("<table><tr><th>Produkt</th><th>Haendler</th>"
                       "<th>Preis</th><th>Einheit</th><th>gueltig bis</th>"
                       f"</tr>{zeilen}</table>")

    return _PAGE.format(titel="Angebots-Suche", inhalt=inhalt)


@app.route("/historie")
def historie():
    q = (request.args.get("q") or "").strip()
    plz = (request.args.get("plz") or "").strip()

    s = storage.stats()
    inhalt = f"""
    <p class="hinweis">Gespeichert: {s['eintraege'] or 0} Eintraege,
    {s['produkte'] or 0} Produkte, {s['haendler'] or 0} Haendler
    (seit {_esc(fmt_date_de(s['seit']) or '-')}, letzter Lauf
    {_esc(fmt_date_de(s['letzter_lauf']) or '-')}).</p>
    <form action="/historie" method="get">
      <input type="text" name="q" value="{_esc(q)}" size="30"
             placeholder="Produkt, z.B. wodka" autofocus>
      <input type="text" name="plz" value="{_esc(plz)}" size="6"
             placeholder="PLZ (optional)">
      <button type="submit">Historie zeigen</button>
    </form>
    """

    if q:
        trends = storage.trend(q, plz or None)
        if trends:
            inhalt += "<h2>Trend pro Produkt &amp; Haendler</h2>"
            zeilen = ""
            for t in trends:
                ap = t["aenderung_prozent"]
                if ap is None or t["datenpunkte"] < 2:
                    pfeil = "&ndash;"
                elif ap > 0:
                    pfeil = f'<span class="hoch">&#9650; +{ap} %</span>'
                elif ap < 0:
                    pfeil = f'<span class="runter">&#9660; {ap} %</span>'
                else:
                    pfeil = "&#8594; 0 %"
                zeilen += (
                    f"<tr><td>{_esc(t['produkt'])}</td>"
                    f"<td>{_esc(t['haendler'])}</td>"
                    f"<td class='preis'>{_eur(t['erster_preis'])}</td>"
                    f"<td class='preis'>{_eur(t['letzter_preis'])}</td>"
                    f"<td>{pfeil}</td>"
                    f"<td class='preis'>{_eur(t['min_preis'])}</td>"
                    f"<td>{t['datenpunkte']}</td>"
                    f"<td>{_esc(fmt_date_de(t['von']))} &ndash; "
                    f"{_esc(fmt_date_de(t['bis']))}</td></tr>")
            inhalt += ("<table><tr><th>Produkt</th><th>Haendler</th>"
                       "<th>erster Preis</th><th>letzter Preis</th>"
                       "<th>Trend</th><th>Tiefstpreis</th><th>Messungen</th>"
                       f"<th>Zeitraum</th></tr>{zeilen}</table>")

        rows = storage.history(q, plz or None)
        if rows:
            inhalt += f"<h2>Einzelne Eintraege ({len(rows)})</h2>"
            zeilen = "".join(
                f"<tr><td>{_esc(fmt_date_de(r['erfasst_am']))}</td>"
                f"<td>{_esc(r['produkt'])}</td>"
                f"<td>{_esc(r['haendler'])}</td>"
                f"<td class='preis'>{_eur(r['preis'])}</td>"
                f"<td>{_esc(r['einheit'])}</td>"
                f"<td>{_esc(r['plz'])}</td></tr>"
                for r in rows)
            inhalt += ("<table><tr><th>erfasst am</th><th>Produkt</th>"
                       "<th>Haendler</th><th>Preis</th><th>Einheit</th>"
                       f"<th>PLZ</th></tr>{zeilen}</table>")
        else:
            inhalt += (f"<p>Noch keine gespeicherten Preise zu "
                       f"&bdquo;{_esc(q)}&ldquo;. Erst ein paar Suchen oder "
                       f"den Sammler (collect.py) laufen lassen.</p>")

    return _PAGE.format(titel="Preis-Historie", inhalt=inhalt)


if __name__ == "__main__":
    # Nur zum lokalen Testen; auf dem Server gunicorn benutzen.
    app.run(host="127.0.0.1", port=8080, debug=False)
