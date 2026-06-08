#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marktguru_test.py

Eigenständiges Test-Skript: prueft, ob strukturierte Einzelhandels-Angebote von
marktguru fuer PLZ 58675 (Hemer) abgerufen werden koennen.

Kontext: Gastronomie-Einkauf. Fokus: Softdrinks, Alkohol, Gemuese.
Wichtigster Haendler: Marktkauf Hemer.

API:
  GET https://api.marktguru.de/api/v1/offers/search
  Query: as=web, limit=25, offset=0, q=<suchbegriff>, zipCode=58675
  Pflicht-Header: x-apikey, x-clientkey

Nur stdlib + requests.
"""

import csv
import json
import re
import sys
import time
from collections import Counter, defaultdict

import requests

# ---------------------------------------------------------------------------
# Manuelle Keys (Fallback).
#
# Wenn die automatische Extraktion aus der marktguru-Webseite scheitert, hier
# zwei Konstanten setzen. Sind beide gesetzt (nicht leer), wird die Extraktion
# komplett uebersprungen.
#
# So bekommst du die Keys manuell:
#   1. https://www.marktguru.de im Browser oeffnen.
#   2. F12 -> Tab "Netzwerk" (Network) -> Filter auf "api.marktguru.de".
#   3. Auf der Seite eine Suche starten (z.B. "cola").
#   4. Den Request an api.marktguru.de anklicken -> Reiter "Header".
#   5. Unter "Request Headers" die Werte von  x-apikey  und  x-clientkey
#      kopieren und hier eintragen.
# ---------------------------------------------------------------------------
API_KEY = ""        # <- hier x-apikey eintragen, um Auto-Extraktion zu ueberspringen
CLIENT_KEY = ""     # <- hier x-clientkey eintragen

# Alternativ koennen die Keys in einer eigenen Datei stehen, damit man das
# Programm aktualisieren kann, ohne die Keys neu eintragen zu muessen.
# Format der Datei (zwei Zeilen genuegen):
#     apikey=DEIN_X_APIKEY
#     clientkey=DEIN_X_CLIENTKEY
KEYS_FILE = "marktguru_keys.txt"

# Produktliste: steht in einer eigenen Textdatei, damit du sie bequem pflegen
# kannst, ohne im Programm-Code etwas zu aendern. Eine Zeile = ein Suchbegriff.
# Zeilen, die mit '#' beginnen, sind Kategorie-Ueberschriften.
# Fehlt die Datei, werden die DEFAULT_SEARCH_TERMS unten benutzt.
PRODUCTS_FILE = "produkte.txt"

ZIP_CODE = "58675"          # Hemer
BASE_URL = "https://api.marktguru.de/api/v1/offers/search"
HOME_URL = "https://www.marktguru.de"
REQUEST_TIMEOUT = 20
SLEEP_BETWEEN = 0.3         # Sekunden Pause zwischen den Suchanfragen

# Echter Browser-User-Agent, sonst blocken die marktguru-Server gerne.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# Fallback, falls produkte.txt fehlt.
DEFAULT_SEARCH_TERMS = {
    "Softdrinks": ["coca cola", "fanta", "sprite", "mezzo mix"],
    "Alkohol":    ["krombacher", "veltins", "warsteiner", "jaegermeister",
                   "aperol", "wodka"],
    "Gemuese":    ["tomaten", "zwiebeln", "paprika", "gurke", "salat"],
}

CSV_FILE = "marktguru_angebote.csv"

# Marker, ob das rohe JSON-Schema schon einmal ausgegeben wurde.
_schema_dumped = False


# ---------------------------------------------------------------------------
# Dateien einlesen (Produkte + Keys)
# ---------------------------------------------------------------------------
def load_products(path):
    """
    Liest die Produktliste aus einer Textdatei.
    Aufbau:
        # Kategorie
        suchbegriff
        noch ein suchbegriff
    Gibt ein dict {Kategorie: [begriffe]} zurueck. Fehlt die Datei oder ist sie
    leer, wird None zurueckgegeben (dann nutzt der Aufrufer die Defaults).
    """
    import os
    if not os.path.exists(path):
        return None
    terms = {}
    current = "Allgemein"
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#"):
                    name = line.lstrip("#").strip()
                    if name:
                        current = name
                    continue
                terms.setdefault(current, []).append(line)
    except Exception as e:
        print(f"[produkte] FEHLER beim Lesen von '{path}': "
              f"{type(e).__name__}: {e}")
        return None
    # Leere Kategorien entfernen.
    terms = {k: v for k, v in terms.items() if v}
    return terms or None


def load_keys_from_file(path):
    """
    Liest API_KEY / CLIENT_KEY aus einer Datei.
    Akzeptiert 'apikey=...' / 'clientkey=...' ODER einfach zwei Zeilen
    (erste = apikey, zweite = clientkey). Gibt (api, client) oder (None, None).
    """
    import os
    if not os.path.exists(path):
        return None, None
    api_key = client_key = None
    plain = []
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                low = line.lower()
                if low.startswith("apikey") or low.startswith("x-apikey"):
                    api_key = line.split("=", 1)[-1].strip().strip('"')
                elif low.startswith("clientkey") or low.startswith("x-clientkey"):
                    client_key = line.split("=", 1)[-1].strip().strip('"')
                else:
                    plain.append(line)
    except Exception as e:
        print(f"[keys] FEHLER beim Lesen von '{path}': "
              f"{type(e).__name__}: {e}")
        return None, None
    # Fallback: zwei nackte Zeilen ohne 'apikey='/'clientkey='.
    if not api_key and len(plain) >= 1:
        api_key = plain[0]
    if not client_key and len(plain) >= 2:
        client_key = plain[1]
    return api_key, client_key


# ---------------------------------------------------------------------------
# Key-Beschaffung
# ---------------------------------------------------------------------------
def fetch_keys(session):
    """
    Liefert (api_key, client_key).

    Reihenfolge:
      1. Wenn beide Konstanten gesetzt sind -> direkt zurueck (keine Extraktion).
      2. Sonst Startseite laden, Script-URLs extrahieren, in HTML + JS-Bundles
         per Regex nach apiKey / clientKey suchen.
    """
    if API_KEY and CLIENT_KEY:
        print("[keys] Verwende manuell gesetzte Konstanten "
              "(Extraktion uebersprungen).")
        return API_KEY, CLIENT_KEY

    file_api, file_client = load_keys_from_file(KEYS_FILE)
    if file_api and file_client:
        print(f"[keys] Verwende Keys aus Datei '{KEYS_FILE}' "
              "(Extraktion uebersprungen).")
        return file_api, file_client

    print(f"[keys] Lade Startseite {HOME_URL} ...")
    try:
        r = session.get(HOME_URL, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print(f"[keys] FEHLER beim Laden der Startseite: "
              f"{type(e).__name__}: {e}")
        return None, None

    # Zuerst direkt im HTML nach Keys suchen.
    api_key, client_key = _scan_for_keys(html)
    if api_key and client_key:
        print("[keys] Keys direkt im HTML der Startseite gefunden.")
        return api_key, client_key

    # Script-URLs aus dem HTML ziehen.
    script_urls = _extract_script_urls(html)
    print(f"[keys] {len(script_urls)} Script-URL(s) gefunden, durchsuche JS ...")

    for url in script_urls:
        try:
            jr = session.get(url, timeout=REQUEST_TIMEOUT)
            if jr.status_code != 200:
                continue
            js = jr.text
        except Exception as e:
            print(f"[keys]   uebersprungen {url}: {type(e).__name__}: {e}")
            continue

        a, c = _scan_for_keys(js)
        api_key = api_key or a
        client_key = client_key or c
        if api_key and client_key:
            print(f"[keys] Keys gefunden in JS-Bundle: {url}")
            return api_key, client_key

    if api_key or client_key:
        print(f"[keys] Nur teilweise gefunden "
              f"(apiKey={'ja' if api_key else 'nein'}, "
              f"clientKey={'ja' if client_key else 'nein'}).")
    else:
        print("[keys] Keine Keys aus HTML/JS extrahierbar.")
    return api_key, client_key


def _extract_script_urls(html):
    """Alle <script src=...> URLs absolut machen."""
    urls = []
    for m in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I):
        if m.startswith("//"):
            m = "https:" + m
        elif m.startswith("/"):
            m = HOME_URL.rstrip("/") + m
        elif not m.startswith("http"):
            m = HOME_URL.rstrip("/") + "/" + m
        urls.append(m)
    # Duplikate raus, Reihenfolge erhalten.
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _scan_for_keys(text):
    """
    Sucht in beliebigem Text nach apiKey / clientKey.
    Erwartet base64-artige Strings (ca. 20+ Zeichen).
    """
    val = r'["\']([A-Za-z0-9_\-]{20,})["\']'
    api_patterns = [
        r'apiKey\s*[:=]\s*' + val,
        r'x-apikey["\']?\s*[:=]\s*' + val,
        r'API_KEY\s*[:=]\s*' + val,
    ]
    client_patterns = [
        r'clientKey\s*[:=]\s*' + val,
        r'x-clientkey["\']?\s*[:=]\s*' + val,
        r'CLIENT_KEY\s*[:=]\s*' + val,
    ]
    api_key = _first_match(api_patterns, text)
    client_key = _first_match(client_patterns, text)
    return api_key, client_key


def _first_match(patterns, text):
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Suche
# ---------------------------------------------------------------------------
def search_term(session, headers, term):
    """
    Fuehrt eine Suche aus. Gibt die Liste der Result-Objekte zurueck (ggf. leer).
    Wirft NICHT - Fehler werden gefangen und als leere Liste behandelt.
    """
    params = {
        "as": "web",
        "limit": 25,
        "offset": 0,
        "q": term,
        "zipCode": ZIP_CODE,
    }
    try:
        r = session.get(BASE_URL, headers=headers, params=params,
                        timeout=REQUEST_TIMEOUT)
    except Exception as e:
        print(f"  [{term}] Request-FEHLER: {type(e).__name__}: {e}")
        return []

    if r.status_code != 200:
        snippet = (r.text or "")[:200].replace("\n", " ")
        print(f"  [{term}] HTTP {r.status_code}: {snippet}")
        return []

    try:
        data = r.json()
    except Exception as e:
        print(f"  [{term}] JSON-Parse-FEHLER: {type(e).__name__}: {e}")
        return []

    # marktguru liefert ueblicherweise {"results":[...]} - defensiv abfangen.
    if isinstance(data, dict):
        results = (data.get("results") or data.get("offers")
                   or data.get("data") or [])
    elif isinstance(data, list):
        results = data
    else:
        results = []
    return results


def maybe_dump_schema(result_obj):
    """Beim allerersten Treffer das rohe JSON des ersten Result-Objekts zeigen."""
    global _schema_dumped
    if _schema_dumped:
        return
    _schema_dumped = True
    print("\n" + "=" * 70)
    print("ROHES JSON DES ERSTEN TREFFERS (zur Feldnamen-Inspektion)")
    print("=" * 70)
    print(json.dumps(result_obj, indent=2, ensure_ascii=False))
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Feld-Extraktion (defensiv)
# ---------------------------------------------------------------------------
def _get_first(d, *keys, default=None):
    """Erstes vorhandenes, nicht-leeres Feld aus mehreren moeglichen Namen."""
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, "", [], {}):
            return d.get(k)
    return default


def parse_offer(offer):
    """Ein Result-Objekt -> dict mit den Feldern, die wir brauchen."""
    if not isinstance(offer, dict):
        return None

    # marktguru verschachtelt Produkt/Marke/Einheit in Unter-Objekte.
    product_node = offer.get("product") if isinstance(offer.get("product"), dict) else {}
    brand_node = offer.get("brand") if isinstance(offer.get("brand"), dict) else {}
    unit_node = offer.get("unit") if isinstance(offer.get("unit"), dict) else {}

    # Produktname: Marke + Produktname kombinieren (z.B. "Coca-Cola Original
    # Taste"). Fallback auf den Werbetext (description), falls nichts da ist.
    brand_name = _get_first(brand_node, "name", "title", default="") or ""
    prod_name = _get_first(product_node, "name", "title", default="") or ""
    produkt = " ".join(p for p in (brand_name, prod_name) if p).strip()
    if not produkt:
        produkt = (_get_first(offer, "title", "name", "productName",
                              "description") or "")

    preis = _get_first(offer, "price", "offerPrice", "currentPrice",
                       "priceValue", "salePrice")

    # Grundpreis (Preis pro Einheit) - fuer Gastro-Vergleich nuetzlich.
    grundpreis = _get_first(offer, "referencePrice", "basePrice", "unitPrice",
                            "pricePerUnit")

    # Einheit: unit ist ein Objekt {shortName, name}. Mit Menge/Volumen
    # kombinieren -> z.B. "2 l" statt rohem dict.
    unit_short = _get_first(unit_node, "shortName", "name", default="") or ""
    menge = offer.get("volume") or offer.get("quantity")
    if unit_short and menge not in (None, "", 0):
        einheit = f"{_fmt_num(menge)} {unit_short}"
    elif unit_short:
        einheit = unit_short
    else:
        einheit = (_get_first(offer, "quantity", "amount", "packaging",
                              "unitText", default="") or "")

    gueltig_bis = _get_first(offer, "validTo", "validUntil", "endDate",
                             "validityEndDate", "dateEnd")
    # Marktguru-Schema: validityDates: [{"from":..,"to":..}]
    if not gueltig_bis:
        vd = offer.get("validityDates")
        if isinstance(vd, list) and vd and isinstance(vd[0], dict):
            gueltig_bis = _get_first(vd[0], "to", "validTo", "end")
    gueltig_bis = _fmt_date(gueltig_bis)

    # Haendler aus advertisers[0].name
    haendler = ""
    advs = offer.get("advertisers")
    if isinstance(advs, list) and advs:
        first = advs[0]
        if isinstance(first, dict):
            haendler = _get_first(first, "name", "title", default="") or ""
        elif isinstance(first, str):
            haendler = first
    if not haendler:
        haendler = _get_first(offer, "advertiserName", "retailer", "shop",
                              default="") or ""

    return {
        "produkt": str(produkt).strip(),
        "haendler": str(haendler).strip(),
        "preis": preis,
        "grundpreis": grundpreis,
        "einheit": str(einheit).strip() if einheit else "",
        "gueltig_bis": gueltig_bis,
    }


def _fmt_num(n):
    """2.0 -> '2', 0.5 -> '0.5' (haengt keine unnoetige .0 an)."""
    try:
        f = float(n)
        return str(int(f)) if f == int(f) else str(f)
    except (TypeError, ValueError):
        return str(n)


def _fmt_date(value):
    """ISO-Datum '2026-06-13T21:59:00Z' -> '13.06.2026'. Sonst Rohwert."""
    if not value:
        return ""
    s = str(value)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(3)}.{m.group(2)}.{m.group(1)}"
    return s.strip()


# ---------------------------------------------------------------------------
# Hauptlauf
# ---------------------------------------------------------------------------
def main():
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "application/json"})

    api_key, client_key = fetch_keys(session)
    if not (api_key and client_key):
        print("\n[ABBRUCH] Konnte keine API-Keys beschaffen. "
              "Bitte API_KEY / CLIENT_KEY oben im Skript manuell setzen "
              "(siehe Kommentar).")
        # Trotzdem versuchen wir NICHT blind weiter - ohne Keys ist alles 401.
        return 1

    print(f"[keys] apiKey={_mask(api_key)}  clientKey={_mask(client_key)}")

    # Produktliste laden: bevorzugt aus produkte.txt, sonst Defaults.
    search_terms = load_products(PRODUCTS_FILE)
    if search_terms:
        anzahl = sum(len(v) for v in search_terms.values())
        print(f"[produkte] {anzahl} Suchbegriffe aus '{PRODUCTS_FILE}' geladen "
              f"({len(search_terms)} Kategorien).")
    else:
        search_terms = DEFAULT_SEARCH_TERMS
        print(f"[produkte] '{PRODUCTS_FILE}' nicht gefunden - "
              "verwende eingebaute Standardliste.")

    headers = {
        "x-apikey": api_key,
        "x-clientkey": client_key,
        "User-Agent": UA,
        "Accept": "application/json",
    }

    rows = []                       # alle geparsten, deduplizierten Treffer
    seen = set()                    # (produkt, haendler, preis)
    per_category = defaultdict(list)
    haendler_counter = Counter()

    for kategorie, terms in search_terms.items():
        for term in terms:
            print(f"[suche] {kategorie} / '{term}' ...")
            results = search_term(session, headers, term)
            print(f"  -> {len(results)} Roh-Treffer")

            for offer in results:
                if isinstance(offer, dict):
                    maybe_dump_schema(offer)
                parsed = parse_offer(offer)
                if not parsed or not parsed["produkt"]:
                    continue

                key = (parsed["produkt"].lower(),
                       parsed["haendler"].lower(),
                       str(parsed["preis"]))
                if key in seen:
                    continue
                seen.add(key)

                parsed["kategorie"] = kategorie
                parsed["suchbegriff"] = term
                rows.append(parsed)
                per_category[kategorie].append(parsed)
                if parsed["haendler"]:
                    haendler_counter[parsed["haendler"]] += 1

            time.sleep(SLEEP_BETWEEN)

    print_grouped(per_category)
    write_csv(rows)
    print_summary(haendler_counter, len(rows))
    return 0


def _mask(s):
    if not s:
        return "<leer>"
    return s[:4] + "..." + s[-4:] if len(s) > 10 else s[:2] + "..."


def print_grouped(per_category):
    print("\n" + "#" * 70)
    print("# ANGEBOTE GRUPPIERT NACH KATEGORIE")
    print("#" * 70)
    for kategorie, items in per_category.items():
        print(f"\n=== {kategorie} ({len(items)} Treffer) ===")
        for it in items:
            preis = it["preis"]
            preis_s = f"{preis}" if preis is not None else "?"
            print(f"  - {it['produkt'][:50]:50s} | {it['haendler'][:20]:20s} "
                  f"| {preis_s:>8} | {it['einheit'][:15]:15s} "
                  f"| bis {it['gueltig_bis']}")
        if not items:
            print("  (keine Treffer)")


def write_csv(rows):
    try:
        with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Kategorie", "Suchbegriff", "Produkt", "Haendler",
                        "Preis", "Einheit", "Gueltig_bis"])
            for r in rows:
                w.writerow([r["kategorie"], r["suchbegriff"], r["produkt"],
                            r["haendler"], r["preis"], r["einheit"],
                            r["gueltig_bis"]])
        print(f"\n[csv] {len(rows)} Zeilen geschrieben -> {CSV_FILE} "
              f"(UTF-8 mit BOM, Semikolon-Trenner)")
    except Exception as e:
        print(f"[csv] FEHLER beim Schreiben: {type(e).__name__}: {e}")


def print_summary(haendler_counter, total):
    print("\n" + "#" * 70)
    print("# ZUSAMMENFASSUNG")
    print("#" * 70)
    print(f"Gesamt (dedupliziert): {total} Treffer")
    print(f"Verschiedene Haendler: {len(haendler_counter)}")

    if haendler_counter:
        print("\nHaendler nach Trefferzahl:")
        for name, cnt in haendler_counter.most_common():
            print(f"  {cnt:4d}  {name}")

    # Marktkauf explizit hervorheben (auch Schreibvarianten abfangen).
    marktkauf = sum(c for n, c in haendler_counter.items()
                    if "marktkauf" in n.lower())
    print("\n" + "-" * 40)
    if marktkauf > 0:
        print(f">>> MARKTKAUF: {marktkauf} Treffer gefunden "
              f"(wichtigster Laden) <<<")
    else:
        print(">>> MARKTKAUF: KEINE Treffer fuer Marktkauf gefunden <<<")
    print("-" * 40)


if __name__ == "__main__":
    sys.exit(main())
