---
sidebar_position: 7
---

# Profile Commands Reference

This page covers all commands related to [Zaya profiles](../user-guide/profiles.md). For general CLI commands, see [CLI Commands Reference](./cli-commands.md).

## `zaya profile`

```bash
zaya profile <subcommand>
```

Top-level command for managing profiles. Running `zaya profile` without a subcommand shows help.

| Subcommand | Description |
|------------|-------------|
| `list` | List all profiles. |
| `use` | Set the active (default) profile. |
| `create` | Create a new profile. |
| `delete` | Delete a profile. |
| `show` | Show details about a profile. |
| `alias` | Regenerate the shell alias for a profile. |
| `rename` | Rename a profile. |
| `export` | Export a profile to a tar.gz archive. |
| `import` | Import a profile from a tar.gz archive. |

## `zaya profile list`

```bash
zaya profile list
```

Lists all profiles. The currently active profile is marked with `*`.

**Example:**

```bash
$ zaya profile list
  default
* work
  dev
  personal
```

No options.

## `zaya profile use`

```bash
zaya profile use <name>
```

Sets `<name>` as the active profile. All subsequent `zaya` commands (without `-p`) will use this profile.

| Argument | Description |
|----------|-------------|
| `<name>` | Profile name to activate. Use `default` to return to the base profile. |

**Example:**

```bash
zaya profile use work
zaya profile use default
```

## `zaya profile create`

```bash
zaya profile create <name> [options]
```

Creates a new profile.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Name for the new profile. Must be a valid directory name (alphanumeric, hyphens, underscores). |
| `--clone` | Copy `config.yaml`, `.env`, and `SOUL.md` from the current profile. |
| `--clone-all` | Copy everything (config, memories, skills, sessions, state) from the current profile. |
| `--clone-from <profile>` | Clone from a specific profile instead of the current one. Used with `--clone` or `--clone-all`. |
| `--no-alias` | Skip wrapper script creation. |

**Examples:**

```bash
# Blank profile — needs full setup
zaya profile create mybot

# Clone config only from current profile
zaya profile create work --clone

# Clone everything from current profile
zaya profile create backup --clone-all

# Clone config from a specific profile
zaya profile create work2 --clone --clone-from work
```

## `zaya profile delete`

```bash
zaya profile delete <name> [options]
```

Deletes a profile and removes its shell alias.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Profile to delete. |
| `--yes`, `-y` | Skip confirmation prompt. |

**Example:**

```bash
zaya profile delete mybot
zaya profile delete mybot --yes
```

:::warning
This permanently deletes the profile's entire directory including all config, memories, sessions, and skills. Cannot delete the currently active profile.
:::

## `zaya profile show`

```bash
zaya profile show <name>
```

Displays details about a profile including its home directory, configured model, gateway status, skills count, and configuration file status.

| Argument | Description |
|----------|-------------|
| `<name>` | Profile to inspect. |

**Example:**

```bash
$ zaya profile show work
Profile: work
Path:    ~/.zaya/profiles/work
Model:   anthropic/claude-sonnet-4 (anthropic)
Gateway: stopped
Skills:  12
.env:    exists
SOUL.md: exists
Alias:   ~/.local/bin/work
```

## `zaya profile alias`

```bash
zaya profile alias <name> [options]
```

Regenerates the shell alias script at `~/.local/bin/<name>`. Useful if the alias was accidentally deleted or if you need to update it after moving your Zaya installation.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Profile to create/update the alias for. |
| `--remove` | Remove the wrapper script instead of creating it. |
| `--name <alias>` | Custom alias name (default: profile name). |

**Example:**

```bash
zaya profile alias work
# Creates/updates ~/.local/bin/work

zaya profile alias work --name mywork
# Creates ~/.local/bin/mywork

zaya profile alias work --remove
# Removes the wrapper script
```

## `zaya profile rename`

```bash
zaya profile rename <old-name> <new-name>
```

Renames a profile. Updates the directory and shell alias.

| Argument | Description |
|----------|-------------|
| `<old-name>` | Current profile name. |
| `<new-name>` | New profile name. |

**Example:**

```bash
zaya profile rename mybot assistant
# ~/.zaya/profiles/mybot → ~/.zaya/profiles/assistant
# ~/.local/bin/mybot → ~/.local/bin/assistant
```

## `zaya profile export`

```bash
zaya profile export <name> [options]
```

Exports a profile as a compressed tar.gz archive.

| Argument / Option | Description |
|-------------------|-------------|
| `<name>` | Profile to export. |
| `-o`, `--output <path>` | Output file path (default: `<name>.tar.gz`). |

**Example:**

```bash
zaya profile export work
# Creates work.tar.gz in the current directory

zaya profile export work -o ./work-2026-03-29.tar.gz
```

## `zaya profile import`

```bash
zaya profile import <archive> [options]
```

Imports a profile from a tar.gz archive.

| Argument / Option | Description |
|-------------------|-------------|
| `<archive>` | Path to the tar.gz archive to import. |
| `--name <name>` | Name for the imported profile (default: inferred from archive). |

**Example:**

```bash
zaya profile import ./work-2026-03-29.tar.gz
# Infers profile name from the archive

zaya profile import ./work-2026-03-29.tar.gz --name work-restored
```

## `zaya -p` / `zaya --profile`

```bash
zaya -p <name> <command> [options]
zaya --profile <name> <command> [options]
```

Global flag to run any Zaya command under a specific profile without changing the sticky default. This overrides the active profile for the duration of the command.

| Option | Description |
|--------|-------------|
| `-p <name>`, `--profile <name>` | Profile to use for this command. |

**Examples:**

```bash
zaya -p work chat -q "Check the server status"
zaya --profile dev gateway start
zaya -p personal skills list
zaya -p work config edit
```

## `zaya completion`

```bash
zaya completion <shell>
```

Generates shell completion scripts. Includes completions for profile names and profile subcommands.

| Argument | Description |
|----------|-------------|
| `<shell>` | Shell to generate completions for: `bash` or `zsh`. |

**Examples:**

```bash
# Install completions
zaya completion bash >> ~/.bashrc
zaya completion zsh >> ~/.zshrc

# Reload shell
source ~/.bashrc
```

After installation, tab completion works for:
- `zaya profile <TAB>` — subcommands (list, use, create, etc.)
- `zaya profile use <TAB>` — profile names
- `zaya -p <TAB>` — profile names

## See also

- [Profiles User Guide](../user-guide/profiles.md)
- [CLI Commands Reference](./cli-commands.md)
- [FAQ — Profiles section](./faq.md#profiles)
