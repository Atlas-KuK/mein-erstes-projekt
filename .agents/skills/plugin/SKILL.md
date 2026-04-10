---
name: plugin
description: Manage plugins/skills for this project. Use for commands like 'plugin list', 'plugin install', 'plugin remove'.
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
4. If no plugins are installed, say "No plugins installed."

**Example output:**

```
Installed plugins (1):

  using-superpowers
    source: obra/superpowers (github)
```

Execute these instructions now for the `plugin list` command.
