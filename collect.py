#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect.py

Sammler fuer die Preis-Historie: fragt ALLE Suchbegriffe aus produkte.txt
ab und speichert die Treffer in die Datenbank (angebote.db).

Gedacht fuer einen taeglichen Cron-Job auf dem Server:
    0 7 * * * cd /pfad/zum/projekt && venv/bin/python collect.py >> collect.log 2>&1

Aufruf:
    python collect.py            -> Standard-PLZ (58675)
    python collect.py 58675 58636  -> mehrere PLZ
"""

import sys
import time
from datetime import datetime

import storage
from marktguru_client import Client, MarktguruError, load_products

DEFAULT_PLZ = ["58675"]     # Hemer
SLEEP_BETWEEN = 0.3         # Sekunden Pause zwischen den Anfragen


def main():
    plz_liste = sys.argv[1:] or DEFAULT_PLZ

    produkte = load_products()
    if not produkte:
        print("[collect] FEHLER: produkte.txt fehlt oder ist leer.")
        return 1
    anzahl = sum(len(v) for v in produkte.values())

    print(f"[collect] {datetime.now():%Y-%m-%d %H:%M} - "
          f"{anzahl} Suchbegriffe, PLZ: {', '.join(plz_liste)}")

    try:
        client = Client()
    except MarktguruError as e:
        print(f"[collect] FEHLER bei den Keys: {e}")
        return 1

    gesamt_neu = gesamt_treffer = fehler = 0
    for plz in plz_liste:
        for kategorie, begriffe in produkte.items():
            for begriff in begriffe:
                try:
                    offers = client.search(begriff, plz)
                except MarktguruError as e:
                    print(f"[collect]   {plz} / '{begriff}': FEHLER {e}")
                    fehler += 1
                    time.sleep(SLEEP_BETWEEN)
                    continue
                neu = storage.save_offers(offers, plz, begriff)
                gesamt_treffer += len(offers)
                gesamt_neu += neu
                print(f"[collect]   {plz} / '{begriff}': "
                      f"{len(offers)} Treffer, {neu} neu")
                time.sleep(SLEEP_BETWEEN)

    print(f"[collect] Fertig: {gesamt_treffer} Treffer, "
          f"{gesamt_neu} neu gespeichert, {fehler} Fehler.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
