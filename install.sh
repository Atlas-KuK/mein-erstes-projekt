#!/usr/bin/env bash
# Makes the 'plugin' skill globally available by copying it to ~/.claude/skills/plugin/.
# After running this once on a machine, the skill is available in every Claude Code
# session, in any repo, now and in the future. It enables commands like:
#   plugin list
#   plugin install <github-url | gist-url | raw-url | local-path | pasted content>
#   plugin remove <name>
#
# Re-run this script after pulling updates to the skill to refresh the global copy.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$SCRIPT_DIR/.agents/skills/plugin"
DEST="$HOME/.claude/skills/plugin"

if [ ! -d "$SRC" ]; then
    echo "Error: source skill not found at $SRC" >&2
    exit 1
fi

if [ ! -f "$SRC/SKILL.md" ]; then
    echo "Error: $SRC is missing SKILL.md" >&2
    exit 1
fi

mkdir -p "$(dirname "$DEST")"

if [ -e "$DEST" ]; then
    printf 'Global plugin skill already exists at %s\nOverwrite? (y/N) ' "$DEST"
    read -r ans
    case "$ans" in
        y|Y|yes|Yes) rm -rf "$DEST" ;;
        *) echo "Aborted."; exit 0 ;;
    esac
fi

cp -r "$SRC" "$DEST"
echo "Installed global plugin skill to $DEST"
echo
echo "Start a new Claude Code session to pick it up, then use:"
echo "  plugin list"
echo "  plugin install <source>"
echo "  plugin remove <name>"
