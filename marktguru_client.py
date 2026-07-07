#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marktguru_client.py

Wiederverwendbarer Client fuer die marktguru-Angebots-API.
Wird von app.py (Web-Oberflaeche), collect.py (Cron-Sammler) und
marktguru_test.py benutzt.

Key-Beschaffung, Reihenfolge:
  1. Umgebungsvariablen MARKTGURU_API_KEY / MARKTGURU_CLIENT_KEY
  2. Datei marktguru_keys.txt (apikey=... / clientkey=... oder zwei Zeilen)
  3. Automatische Extraktion aus der marktguru-Webseite (HTML + JS-Bundles)

Nur stdlib + requests.
"""

import os
import re
import time

import requests

BASE_URL = "https://api.marktguru.de/api/v1/offers/search"
HOME_URL = "https://www.marktguru.de"
REQUEST_TIMEOUT = 20

# Datei liegt neben diesem Modul, damit Cron-Jobs mit beliebigem
# Arbeitsverzeichnis funktionieren.
_HERE = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.path.join(_HERE, "marktguru_keys.txt")
PRODUCTS_FILE = os.path.join(_HERE, "produkte.txt")

# Echter Browser-User-Agent, sonst blocken die marktguru-Server gerne.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


class MarktguruError(Exception):
    """Fehler, den der Aufrufer dem Nutzer anzeigen kann."""


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------
def load_keys_from_file(path=KEYS_FILE):
    """
    Liest API-Key / Client-Key aus einer Datei.
    Akzeptiert 'apikey=...' / 'clientkey=...' ODER einfach zwei Zeilen
    (erste = apikey, zweite = clientkey). Gibt (api, client) oder (None, None).
    """
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
                if low.startswith(("apikey", "x-apikey")):
                    api_key = line.split("=", 1)[-1].strip().strip('"')
                elif low.startswith(("clientkey", "x-clientkey")):
                    client_key = line.split("=", 1)[-1].strip().strip('"')
                else:
                    plain.append(line)
    except OSError:
        return None, None
    if not api_key and len(plain) >= 1:
        api_key = plain[0]
    if not client_key and len(plain) >= 2:
        client_key = plain[1]
    return api_key, client_key


def _scan_for_keys(text):
    """Sucht apiKey/clientKey (base64-artig, 20+ Zeichen) in HTML/JS."""
    val = r'["\']([A-Za-z0-9+/=_\-]{20,})["\']'
    api = _first_match([r'apiKey\s*[:=]\s*' + val,
                        r'x-apikey["\']?\s*[:=]\s*' + val], text)
    client = _first_match([r'clientKey\s*[:=]\s*' + val,
                           r'x-clientkey["\']?\s*[:=]\s*' + val], text)
    return api, client


def _first_match(patterns, text):
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return None


def _extract_script_urls(html):
    urls = []
    for m in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I):
        if m.startswith("//"):
            m = "https:" + m
        elif m.startswith("/"):
            m = HOME_URL.rstrip("/") + m
        elif not m.startswith("http"):
            m = HOME_URL.rstrip("/") + "/" + m
        if m not in urls:
            urls.append(m)
    return urls


def extract_keys_from_web(session=None):
    """Startseite + JS-Bundles nach den Keys durchsuchen."""
    session = session or requests.Session()
    session.headers.setdefault("User-Agent", UA)
    r = session.get(HOME_URL, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    api_key, client_key = _scan_for_keys(r.text)
    if api_key and client_key:
        return api_key, client_key
    for url in _extract_script_urls(r.text):
        try:
            jr = session.get(url, timeout=REQUEST_TIMEOUT)
            if jr.status_code != 200:
                continue
        except requests.RequestException:
            continue
        a, c = _scan_for_keys(jr.text)
        api_key = api_key or a
        client_key = client_key or c
        if api_key and client_key:
            return api_key, client_key
    return api_key, client_key


def get_keys():
    """
    Beschafft die Keys (env -> Datei -> Web). Wirft MarktguruError,
    wenn nichts gefunden wurde.
    """
    api = os.environ.get("MARKTGURU_API_KEY")
    client = os.environ.get("MARKTGURU_CLIENT_KEY")
    if api and client:
        return api, client

    api, client = load_keys_from_file()
    if api and client:
        return api, client

    try:
        api, client = extract_keys_from_web()
    except requests.RequestException as e:
        raise MarktguruError(
            f"Keys konnten nicht beschafft werden ({type(e).__name__}: {e}). "
            f"Bitte Datei '{KEYS_FILE}' anlegen - Anleitung siehe README/"
            f"Skript-Kommentar.") from e
    if api and client:
        return api, client
    raise MarktguruError(
        "Keine API-Keys gefunden. Bitte Datei 'marktguru_keys.txt' anlegen "
        "(Browser: F12 -> Netzwerk -> Suche auf marktguru.de starten -> "
        "Header x-apikey / x-clientkey kopieren).")


# ---------------------------------------------------------------------------
# Produktliste
# ---------------------------------------------------------------------------
def load_products(path=PRODUCTS_FILE):
    """
    Produktliste einlesen: eine Zeile = ein Suchbegriff,
    '#'-Zeilen sind Kategorie-Ueberschriften.
    Gibt {Kategorie: [begriffe]} oder None (Datei fehlt/leer).
    """
    if not os.path.exists(path):
        return None
    terms = {}
    current = "Allgemein"
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
    terms = {k: v for k, v in terms.items() if v}
    return terms or None


# ---------------------------------------------------------------------------
# Suche + Parsen
# ---------------------------------------------------------------------------
class Client:
    """Haelt Session + Keys und fuehrt Suchen aus."""

    def __init__(self, api_key=None, client_key=None):
        if not (api_key and client_key):
            api_key, client_key = get_keys()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": UA,
            "Accept": "application/json",
            "x-apikey": api_key,
            "x-clientkey": client_key,
        })

    def search(self, query, zip_code, limit=25, offset=0, retries=2):
        """
        Eine Suche. Gibt Liste geparster Angebote (dicts) zurueck.
        Wirft MarktguruError bei dauerhaftem Fehler.
        """
        params = {"as": "web", "limit": limit, "offset": offset,
                  "q": query, "zipCode": str(zip_code)}
        last_err = None
        for attempt in range(retries + 1):
            try:
                r = self.session.get(BASE_URL, params=params,
                                     timeout=REQUEST_TIMEOUT)
            except requests.RequestException as e:
                last_err = f"{type(e).__name__}: {e}"
                time.sleep(1 + attempt)
                continue
            if r.status_code == 200:
                try:
                    data = r.json()
                except ValueError as e:
                    raise MarktguruError(f"Antwort kein JSON: {e}") from e
                results = data.get("results") if isinstance(data, dict) else data
                return [p for p in (parse_offer(o) for o in (results or []))
                        if p and p["produkt"]]
            # 429/5xx: kurz warten und nochmal versuchen
            if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            snippet = (r.text or "")[:200].replace("\n", " ")
            raise MarktguruError(f"HTTP {r.status_code}: {snippet}")
        raise MarktguruError(f"Request fehlgeschlagen: {last_err}")


def _get_first(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, "", [], {}):
            return d.get(k)
    return default


def parse_offer(offer):
    """Ein rohes Result-Objekt -> flaches dict mit unseren Feldern."""
    if not isinstance(offer, dict):
        return None

    product_node = offer.get("product") if isinstance(offer.get("product"), dict) else {}
    brand_node = offer.get("brand") if isinstance(offer.get("brand"), dict) else {}
    unit_node = offer.get("unit") if isinstance(offer.get("unit"), dict) else {}

    brand_name = _get_first(brand_node, "name", "title", default="") or ""
    prod_name = _get_first(product_node, "name", "title", default="") or ""
    produkt = " ".join(p for p in (brand_name, prod_name) if p).strip()
    if not produkt:
        produkt = (_get_first(offer, "title", "name", "productName",
                              "description") or "")

    preis = _get_first(offer, "price", "offerPrice", "currentPrice")
    grundpreis = _get_first(offer, "referencePrice", "basePrice", "unitPrice")

    unit_short = _get_first(unit_node, "shortName", "name", default="") or ""
    menge = offer.get("volume") or offer.get("quantity")
    if unit_short and menge not in (None, "", 0):
        einheit = f"{_fmt_num(menge)} {unit_short}"
    elif unit_short:
        einheit = unit_short
    else:
        einheit = str(_get_first(offer, "quantity", "amount", "packaging",
                                 default="") or "")

    gueltig_von = gueltig_bis = ""
    vd = offer.get("validityDates")
    if isinstance(vd, list) and vd and isinstance(vd[0], dict):
        gueltig_von = _iso_date(_get_first(vd[0], "from", "validFrom", "start"))
        gueltig_bis = _iso_date(_get_first(vd[0], "to", "validTo", "end"))
    if not gueltig_bis:
        gueltig_bis = _iso_date(_get_first(offer, "validTo", "validUntil",
                                           "endDate"))

    haendler = ""
    advs = offer.get("advertisers")
    if isinstance(advs, list) and advs:
        first = advs[0]
        if isinstance(first, dict):
            haendler = _get_first(first, "name", "title", default="") or ""
        elif isinstance(first, str):
            haendler = first

    beschreibung = str(offer.get("description") or "").strip()

    return {
        "produkt": str(produkt).strip(),
        "haendler": str(haendler).strip(),
        "preis": preis,
        "grundpreis": grundpreis,
        "einheit": einheit.strip(),
        "gueltig_von": gueltig_von,
        "gueltig_bis": gueltig_bis,
        "beschreibung": beschreibung,
    }


def _fmt_num(n):
    """2.0 -> '2', 0.5 -> '0.5'."""
    try:
        f = float(n)
        return str(int(f)) if f == int(f) else str(f)
    except (TypeError, ValueError):
        return str(n)


def _iso_date(value):
    """'2026-06-13T21:59:00Z' -> '2026-06-13' (sortierbar). Sonst ''."""
    if not value:
        return ""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(value))
    return m.group(1) if m else str(value).strip()


def fmt_date_de(iso):
    """'2026-06-13' -> '13.06.2026' fuer die Anzeige."""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso or ""))
    return f"{m.group(3)}.{m.group(2)}.{m.group(1)}" if m else (iso or "")
