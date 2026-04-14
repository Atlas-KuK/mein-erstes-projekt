# Project: mein-erstes-projekt

## Tech Stack
- Pure HTML5, CSS3, Vanilla JavaScript (ES6)
- No build tools, no package manager, no framework
- Single-page static website (German content)

## Project Structure
- `index.html` — main page (header, hero, about cards, contact form, footer)
- `style.css` — responsive styles with flexbox, gradients, media queries
- `script.js` — smooth scrolling, CTA button, form handling

## Running the Project
- Open `index.html` directly in a browser — no dev server needed
- No build step, no install step

## Code Rules
- Keep it vanilla JS — no frameworks unless the project outgrows this setup
- CSS: use existing custom properties and naming conventions
- JS: use ES6+ (const/let, arrow functions, template literals)
- No external dependencies without discussion

## Sync Rule
- When a change is made to one CLAUDE.md, always ask if the same change should be applied to the other

## Testing
- No test framework configured — test manually in browser
- Check responsiveness with browser dev tools (mobile/tablet breakpoints)

## claude-mem & `<private>`-Tags

Das Plugin `claude-mem@thedotmack` ist user-weit aktiviert und speichert
Tool-Nutzung + Prompts persistent (SQLite + Chroma). Gilt nur für Claude
Code, nicht für Chrome-Extension oder claude.ai-Chat.

- Web-UI: http://localhost:37777
- Suche: `/mem-search`
- Worker: `npx claude-mem start` (systemd-User-Unit:
  `~/.config/systemd/user/claude-mem.service`)
- Globale Konventionen: `~/.claude/CLAUDE.md`

### `<private>`-Tags

Inhalte, die **nicht** in die persistente Memory sollen, immer in
`<private>…</private>` einschließen. Der Hook entfernt die Tags samt
Inhalt, bevor Daten Worker oder DB erreichen; Claude sieht sie während
der Session aber normal.

Standardmäßig in `<private>` einschließen:

- API-Keys, Tokens, Passwörter, Secrets
- Interne Hostnamen, Produktions-URLs, Connection-Strings
- Persönliche Notizen, Brainstorming, temporäre Kontexte
- Große Log-Dumps, die nur für die aktuelle Sitzung relevant sind

Syntax-Regeln:

- Multiline erlaubt, mehrere Blöcke pro Nachricht OK
- Tag muss korrekt geschlossen sein: `<private>…</private>`
- Kein Ersatz für echtes Secrets-Management — nur eine Speicher-Sperre

Beispiel:

```
<private>
API_KEY=sk-proj-abc123
Host: internal-db-prod.firma.de
</private>

Teste die Verbindung.
```

Verifikation:

```bash
sqlite3 ~/.claude-mem/claude-mem.db \
  "SELECT prompt_text FROM user_prompts ORDER BY created_at_epoch DESC LIMIT 1;"
```

Privater Inhalt darf dort nicht auftauchen. Fehler-Log:
`~/.claude-mem/silent.log`.
