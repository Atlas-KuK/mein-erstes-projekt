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

## Knowledge Base Rule
- `KNOWLEDGE_BASE.md` is the living memory of this repo (context behind decisions, code pointers, configs, problems & solutions).
- After any non-trivial work on a sub-project, update `KNOWLEDGE_BASE.md`:
  - Add new decisions with their rationale to section "Kontext hinter den Entscheidungen"
  - Update code pointers if structure changed
  - Append new problems + fixes to "Aufgetauchte Probleme & Lösungen"
  - Bump the "Letzte Aktualisierung"-Datum at the top
- Read `KNOWLEDGE_BASE.md` at the start of a session to restore context.

## Testing
- No test framework configured — test manually in browser
- Check responsiveness with browser dev tools (mobile/tablet breakpoints)
