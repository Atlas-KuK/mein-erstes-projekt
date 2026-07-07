#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storage.py

Preis-Historie in SQLite (Datei angebote.db neben diesem Modul).
Jeder Abruf speichert die gefundenen Angebote mit Datum - so entsteht
ueber die Wochen eine Historie, aus der man Preistrends ablesen kann.

Nur stdlib.
"""

import os
import sqlite3
from datetime import date

_HERE = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(_HERE, "angebote.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS angebote (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    erfasst_am  TEXT NOT NULL,      -- Datum des Abrufs, YYYY-MM-DD
    plz         TEXT NOT NULL,
    suchbegriff TEXT,
    produkt     TEXT NOT NULL,
    haendler    TEXT,
    preis       REAL,
    grundpreis  REAL,
    einheit     TEXT,
    gueltig_von TEXT,
    gueltig_bis TEXT,
    UNIQUE(erfasst_am, plz, produkt, haendler, preis, einheit)
);
CREATE INDEX IF NOT EXISTS idx_angebote_produkt ON angebote(produkt);
CREATE INDEX IF NOT EXISTS idx_angebote_datum   ON angebote(erfasst_am);
"""


def _connect(db_file=None):
    # timeout: wartet kurz, falls gerade ein anderer Prozess schreibt
    # (Web-App und Cron-Sammler koennen gleichzeitig laufen).
    conn = sqlite3.connect(db_file or DB_FILE, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def save_offers(offers, plz, suchbegriff, db_file=None, erfasst_am=None):
    """
    Speichert eine Liste geparster Angebote (dicts aus marktguru_client).
    Doppelte Eintraege desselben Tages werden ignoriert (UNIQUE).
    Gibt die Anzahl NEU gespeicherter Zeilen zurueck.
    """
    heute = erfasst_am or date.today().isoformat()
    neu = 0
    with _connect(db_file) as conn:
        for o in offers:
            cur = conn.execute(
                """INSERT OR IGNORE INTO angebote
                   (erfasst_am, plz, suchbegriff, produkt, haendler,
                    preis, grundpreis, einheit, gueltig_von, gueltig_bis)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (heute, str(plz), suchbegriff, o.get("produkt"),
                 o.get("haendler"), o.get("preis"), o.get("grundpreis"),
                 o.get("einheit"), o.get("gueltig_von"), o.get("gueltig_bis")))
            neu += cur.rowcount
    return neu


def history(query, plz=None, limit=500, db_file=None):
    """
    Alle gespeicherten Eintraege, deren Produkt ODER Suchbegriff zum
    Suchwort passt - neueste zuerst.
    """
    like = f"%{query.strip()}%"
    sql = ("SELECT * FROM angebote WHERE (produkt LIKE ? COLLATE NOCASE "
           "OR suchbegriff LIKE ? COLLATE NOCASE)")
    args = [like, like]
    if plz:
        sql += " AND plz = ?"
        args.append(str(plz))
    sql += " ORDER BY erfasst_am DESC, preis ASC LIMIT ?"
    args.append(int(limit))
    with _connect(db_file) as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def trend(query, plz=None, db_file=None):
    """
    Trend pro (Produkt, Haendler): erster/letzter erfasster Preis,
    Minimum, Maximum, Anzahl Datenpunkte, Zeitraum.
    Sortiert nach staerkster Preisaenderung.
    """
    like = f"%{query.strip()}%"
    sql = ("SELECT erfasst_am, produkt, haendler, preis FROM angebote "
           "WHERE (produkt LIKE ? COLLATE NOCASE "
           "OR suchbegriff LIKE ? COLLATE NOCASE) AND preis IS NOT NULL")
    args = [like, like]
    if plz:
        sql += " AND plz = ?"
        args.append(str(plz))
    sql += " ORDER BY erfasst_am ASC"
    with _connect(db_file) as conn:
        rows = conn.execute(sql, args).fetchall()

    # In Python pro (Produkt, Haendler) aggregieren - so gilt der
    # PLZ-Filter garantiert auch fuer ersten/letzten Preis.
    gruppen = {}
    for r in rows:
        g = gruppen.setdefault((r["produkt"], r["haendler"]), {
            "produkt": r["produkt"], "haendler": r["haendler"],
            "datenpunkte": 0, "von": r["erfasst_am"], "bis": r["erfasst_am"],
            "min_preis": r["preis"], "max_preis": r["preis"],
            "erster_preis": r["preis"], "letzter_preis": r["preis"],
        })
        g["datenpunkte"] += 1
        g["bis"] = r["erfasst_am"]              # rows sind aufsteigend sortiert
        g["letzter_preis"] = r["preis"]
        g["min_preis"] = min(g["min_preis"], r["preis"])
        g["max_preis"] = max(g["max_preis"], r["preis"])

    ergebnis = list(gruppen.values())
    for g in ergebnis:
        ep, lp = g["erster_preis"], g["letzter_preis"]
        g["aenderung_prozent"] = (round((lp - ep) / ep * 100, 1)
                                  if ep else None)
    ergebnis.sort(key=lambda g: abs(g["aenderung_prozent"] or 0), reverse=True)
    return ergebnis


def stats(db_file=None):
    """Kleine Gesamtstatistik fuer die Startseite."""
    with _connect(db_file) as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS eintraege,
                      COUNT(DISTINCT produkt) AS produkte,
                      COUNT(DISTINCT haendler) AS haendler,
                      MIN(erfasst_am) AS seit,
                      MAX(erfasst_am) AS letzter_lauf
               FROM angebote""").fetchone()
        return dict(row)
