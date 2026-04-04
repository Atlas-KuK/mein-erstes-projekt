"""
OneDrive Upload via Microsoft Graph API.

Authentifizierung: OAuth2 Client Credentials Flow (App-only)
Benötigt eine Azure App-Registrierung mit Berechtigung Files.ReadWrite.All.

Schritte in Azure Portal:
  1. Azure Active Directory → App-Registrierungen → Neue Registrierung
  2. Zertifikate & Geheimnisse → Neuer geheimer Clientschlüssel
  3. API-Berechtigungen → Microsoft Graph → Anwendungsberechtigungen → Files.ReadWrite.All
  4. Administratoreinwilligung erteilen
  5. ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET, ONEDRIVE_TENANT_ID in .env eintragen

Für persönliche Konten (Delegated Flow) – siehe Kommentar unten.
"""
from __future__ import annotations

import logging
from pathlib import Path

import requests

from config import (
    ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET,
    ONEDRIVE_TENANT_ID, ONEDRIVE_FOLDER, ONEDRIVE_USER,
)

log = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


class OneDriveError(Exception):
    pass


class OneDriveClient:
    def __init__(self):
        self._token: str | None = None

    # ------------------------------------------------------------------
    # Token-Management
    # ------------------------------------------------------------------

    def _get_token(self) -> str:
        if self._token:
            return self._token

        url = TOKEN_URL.format(tenant=ONEDRIVE_TENANT_ID)
        resp = requests.post(url, data={
            "grant_type":    "client_credentials",
            "client_id":     ONEDRIVE_CLIENT_ID,
            "client_secret": ONEDRIVE_CLIENT_SECRET,
            "scope":         "https://graph.microsoft.com/.default",
        }, timeout=30)
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def _drive_url(self) -> str:
        """Basis-URL für den OneDrive des konfigurierten Benutzers."""
        if ONEDRIVE_USER.lower() == "me":
            return f"{GRAPH_BASE}/me/drive"
        return f"{GRAPH_BASE}/users/{ONEDRIVE_USER}/drive"

    # ------------------------------------------------------------------
    # Ordner sicherstellen
    # ------------------------------------------------------------------

    def _ensure_folder(self, folder_path: str) -> str:
        """
        Erstellt den Zielordner falls er nicht existiert.
        Gibt die Drive-Item-ID zurück.
        """
        parts = [p for p in folder_path.strip("/").split("/") if p]
        parent_id = "root"
        drive_url = self._drive_url()

        for part in parts:
            url = f"{drive_url}/items/{parent_id}/children"
            resp = requests.get(
                url,
                headers=self._headers(),
                params={"$filter": f"name eq '{part}' and folder ne null"},
                timeout=30,
            )
            resp.raise_for_status()
            items = resp.json().get("value", [])

            if items:
                parent_id = items[0]["id"]
            else:
                # Ordner anlegen
                create_resp = requests.post(
                    url,
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json={
                        "name": part,
                        "folder": {},
                        "@microsoft.graph.conflictBehavior": "rename",
                    },
                    timeout=30,
                )
                create_resp.raise_for_status()
                parent_id = create_resp.json()["id"]
                log.info("OneDrive-Ordner erstellt: %s", part)

        return parent_id

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload(self, local_path: Path, remote_folder: str | None = None) -> str:
        """
        Lädt eine Datei nach OneDrive hoch.
        Gibt die öffentliche oder direkte URL der Datei zurück.
        """
        if not all([ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET, ONEDRIVE_TENANT_ID]):
            raise OneDriveError(
                "OneDrive nicht konfiguriert. "
                "Bitte ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET und "
                "ONEDRIVE_TENANT_ID in der .env-Datei setzen."
            )

        folder = remote_folder or ONEDRIVE_FOLDER
        folder_id = self._ensure_folder(folder)
        drive_url = self._drive_url()
        filename = local_path.name
        file_size = local_path.stat().st_size

        if file_size <= 4 * 1024 * 1024:
            return self._simple_upload(local_path, folder_id, filename, drive_url)
        else:
            return self._resumable_upload(local_path, folder_id, filename, drive_url)

    def _simple_upload(self, local_path: Path, folder_id: str,
                       filename: str, drive_url: str) -> str:
        """Einfacher Upload für Dateien bis 4 MB."""
        upload_url = f"{drive_url}/items/{folder_id}:/{filename}:/content"
        with open(local_path, "rb") as fh:
            resp = requests.put(
                upload_url,
                headers={
                    **self._headers(),
                    "Content-Type": "application/pdf",
                },
                data=fh,
                timeout=120,
            )
        resp.raise_for_status()
        item = resp.json()
        web_url = item.get("webUrl", "")
        log.info("OneDrive Upload erfolgreich: %s", web_url)
        return web_url

    def _resumable_upload(self, local_path: Path, folder_id: str,
                          filename: str, drive_url: str) -> str:
        """Resumable Upload für große Dateien (> 4 MB)."""
        session_url = f"{drive_url}/items/{folder_id}:/{filename}:/createUploadSession"
        sess_resp = requests.post(
            session_url,
            headers={**self._headers(), "Content-Type": "application/json"},
            json={"item": {"@microsoft.graph.conflictBehavior": "rename"}},
            timeout=30,
        )
        sess_resp.raise_for_status()
        upload_url = sess_resp.json()["uploadUrl"]

        chunk_size = 5 * 1024 * 1024  # 5 MB
        file_size = local_path.stat().st_size
        uploaded = 0

        with open(local_path, "rb") as fh:
            while uploaded < file_size:
                chunk = fh.read(chunk_size)
                end = uploaded + len(chunk) - 1
                resp = requests.put(
                    upload_url,
                    headers={
                        "Content-Range": f"bytes {uploaded}-{end}/{file_size}",
                        "Content-Length": str(len(chunk)),
                    },
                    data=chunk,
                    timeout=120,
                )
                if resp.status_code in (200, 201):
                    item = resp.json()
                    web_url = item.get("webUrl", "")
                    log.info("OneDrive Upload abgeschlossen: %s", web_url)
                    return web_url
                elif resp.status_code != 202:
                    resp.raise_for_status()
                uploaded += len(chunk)

        raise OneDriveError("Upload nicht abgeschlossen")


# Singleton-Instanz
_client: OneDriveClient | None = None


def upload_to_onedrive(local_path: Path) -> str:
    """Öffentliche Funktion: lädt eine Datei nach OneDrive hoch."""
    global _client
    if _client is None:
        _client = OneDriveClient()
    return _client.upload(local_path)
