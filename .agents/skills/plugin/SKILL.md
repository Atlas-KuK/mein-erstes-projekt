---
name: plugin
description: Manage plugins/skills for this project and globally. Use for 'plugin list', 'plugin install', 'plugin remove', or whenever the user asks to install / add / remove a Claude Code skill from a GitHub repo, Gist, URL, local path, or pasted content — including skills they discovered on Instagram, TikTok, YouTube, or a blog (user pastes the link or content from the post).
user-invocable: true
---

# Plugin Management

This skill handles plugin/skill management commands.

## Subcommands

### plugin list

List all installed plugins/skills from `skills-lock.json`.

**Instructions:**

1. Read the file `skills-lock.json` in the project root using the Read tool.
2. Parse the `skills` object.
3. Display the installed plugins in a formatted list showing:
   - Plugin name
   - Source (e.g. `obra/superpowers`)
   - Source type (e.g. `github`)
4. Also list globally installed skills by listing directories under `~/.claude/skills/` (if the directory exists). Show them under a separate "Global" heading.
5. If no plugins are installed in either location, say "No plugins installed."

**Example output:**

```
Installed plugins (project, 1):

  using-superpowers
    source: obra/superpowers (github)

Installed plugins (global, 1):

  plugin
    path: ~/.claude/skills/plugin
```

Execute these instructions now for the `plugin list` command.

### plugin install

Install a Claude Code skill from an external source.

**Supported sources:**

- GitHub repository URL — e.g. `https://github.com/<owner>/<repo>` (optionally `/tree/<branch>/<subpath>` to pick a subfolder)
- GitHub file URL — e.g. `https://github.com/<owner>/<repo>/blob/<branch>/<path>/SKILL.md`
- Gist URL — e.g. `https://gist.github.com/<user>/<id>`
- Raw file URL — e.g. `https://raw.githubusercontent.com/...`
- Local absolute path to a folder containing `SKILL.md`
- Skill content pasted directly into the chat (SKILL.md text, optionally with additional file blocks)

**Unsupported sources (explain and ask for an alternative):**

- Instagram, TikTok, YouTube, Facebook, X/Twitter links. These platforms do not allow programmatic access to post content. Ask the user to paste instead:
  - the GitHub/Gist link that the post references, OR
  - the SKILL.md text directly from the post description.

**Instructions:**

1. **Determine the source.** If the user did not provide one, ask. Accept any supported source above. Reject unsupported social-media URLs with the explanation above.

2. **Fetch the content** into a temp working directory `/tmp/plugin-install-<epoch>/`:
   - GitHub repo root: `git clone --depth 1 <url> /tmp/plugin-install-<epoch>/src` using the Bash tool. Locate `SKILL.md` — first at the repo root, otherwise the single `SKILL.md` under the tree. If multiple, ask the user which one.
   - GitHub `tree` URL with subpath: same as above, then `cd` into the subpath.
   - GitHub `blob` URL to a SKILL.md: translate `github.com/<o>/<r>/blob/<branch>/<path>` to `raw.githubusercontent.com/<o>/<r>/<branch>/<path>` and fetch with WebFetch. Also fetch every file referenced by the SKILL.md (e.g. `scripts/foo.sh`, `references/bar.md`) from the same repo.
   - Gist URL: WebFetch the gist's raw files.
   - Raw URL: WebFetch directly.
   - Local path: Read the folder's contents with Glob + Read.
   - Pasted content: write the SKILL.md text to the temp dir as-is.

3. **Validate structure.** The source must produce a folder (real or virtual) containing a `SKILL.md` whose YAML frontmatter has at minimum `name` and `description`. If not, report exactly what is missing and stop.

4. **Safety scan.** Grep the skill files for risky patterns and list every match (file + line + matched text) to the user. Flag:
   - `curl ... \| (sh|bash)` or `wget ... \| (sh|bash)` — remote code execution
   - `rm -rf` combined with variables or `/` roots
   - `eval` applied to network input, env, or file contents
   - Hard-coded secrets — patterns like `sk-[A-Za-z0-9]{20,}`, `ghp_[A-Za-z0-9]{20,}`, `AKIA[0-9A-Z]{16}`, `-----BEGIN .*PRIVATE KEY-----`
   - `sudo`, `chmod 777`, or writes to `/etc/`, `~/.ssh/`, `~/.aws/`, `~/.gnupg/`
   - Base64-encoded blobs longer than 200 characters (possible obfuscation)
   - Outbound HTTP(S) calls to hosts other than the declared source
   - Exfil patterns — reads of `~/.env`, `~/.bashrc`, browser profile dirs, keychain

5. **Show for review.** Print to the user:
   - `name` and `description` from the frontmatter
   - full SKILL.md content
   - list of additional files with line counts
   - full contents of small scripts (< 100 lines); for larger files, show the first 50 lines plus a one-line summary and total line count
   - the safety-scan report (or "no risky patterns detected")

6. **Ask where to install.** Present the user these choices explicitly:
   - `project` — `.agents/skills/<name>/` in the current repo (this session only; committed to the repo)
   - `global` — `~/.claude/skills/<name>/` (available in every Claude Code session on this machine, across all repos, now and in the future)
   - `both`
   Do not pick silently. The user's earlier "install it everywhere" intent maps to `both`, but still confirm for this specific skill.

7. **Ask for explicit confirmation.** Ask literally: "Install `<name>` to <chosen location(s)>? (y/n)". Proceed only on an explicit affirmative. Treat anything else as "no".

8. **Install.**
   - Ensure destination parent directories exist (`mkdir -p`).
   - If the destination already exists, ask: `overwrite` / `skip` / `rename to <suggested>`. Do not silently overwrite.
   - Copy files preserving the folder structure with `cp -r`.
   - Do NOT run `chmod +x` on any file automatically. If the skill's own SKILL.md tells the user to run a script, they will chmod it themselves after reviewing.
   - For `project` installs: update `skills-lock.json` in the repo root. Add an entry:
     ```json
     "<name>": {
       "source": "<the original source string the user gave>",
       "sourceType": "github" | "gist" | "url" | "local" | "pasted"
     }
     ```
     Preserve the rest of the file and its formatting (2-space indent, trailing newline).
   - For `global` installs: no lockfile update (the global location is its own source of truth; `plugin list` enumerates it via directory listing).

9. **Confirm success.** Print the final installation path(s). Remind the user:
   - Project skills load immediately from `.agents/skills/` in this repo.
   - Global skills are picked up on the next Claude Code session start.
   - Claude.ai web chat skills are managed separately via the Claude.ai UI — this installer does not touch that surface.

Execute these instructions now for the `plugin install` command.

### plugin remove

Remove an installed skill.

**Instructions:**

1. Parse or ask which skill to remove.
2. Refuse by default to remove these core skills: `plugin`, `using-superpowers`. If the user explicitly includes `--force` in their message, allow removal but warn about the consequences (loss of the installer itself, loss of the superpowers framework).
3. Check both locations:
   - Project: `.agents/skills/<name>/`
   - Global: `~/.claude/skills/<name>/`
4. Report which locations contain the skill and ask which to remove (`project`, `global`, `both`).
5. Ask for explicit confirmation: "Remove `<name>` from <chosen location(s)>? This deletes the directory. (y/n)". Proceed only on yes.
6. `rm -rf` the confirmed directories only. Never touch paths outside `.agents/skills/` or `~/.claude/skills/`.
7. For project removal: update `skills-lock.json` by removing the entry, preserving formatting.
8. Confirm with the user what was removed.

Execute these instructions now for the `plugin remove` command.

## Safety Rules (apply to all subcommands)

- Never install without showing the content and getting an explicit y/n confirmation from the user.
- Never execute any script from the skill during install — only copy files.
- Never silently overwrite an existing installation.
- Never install into arbitrary paths — only `.agents/skills/<name>/` in the current repo or `~/.claude/skills/<name>/`.
- Never fetch content from Instagram, TikTok, YouTube, Facebook, or X/Twitter — explain why and ask for an alternative source link or pasted text.
- Never `chmod +x` files automatically.
- Never commit changes to git automatically — leave files staged for the user to review.
