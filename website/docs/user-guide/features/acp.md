---
sidebar_position: 11
title: "ACP Editor Integration"
description: "Use Zaya Agent inside ACP-compatible editors such as VS Code, Zed, and JetBrains"
---

# ACP Editor Integration

Zaya Agent can run as an ACP server, letting ACP-compatible editors talk to Zaya over stdio and render:

- chat messages
- tool activity
- file diffs
- terminal commands
- approval prompts
- streamed thinking / response chunks

ACP is a good fit when you want Zaya to behave like an editor-native coding agent instead of a standalone CLI or messaging bot.

## What Zaya exposes in ACP mode

Zaya runs with a curated `zaya-acp` toolset designed for editor workflows. It includes:

- file tools: `read_file`, `write_file`, `patch`, `search_files`
- terminal tools: `terminal`, `process`
- web/browser tools
- memory, todo, session search
- skills
- execute_code and delegate_task
- vision

It intentionally excludes things that do not fit typical editor UX, such as messaging delivery and cronjob management.

## Installation

Install Zaya normally, then add the ACP extra:

```bash
pip install -e '.[acp]'
```

This installs the `agent-client-protocol` dependency and enables:

- `zaya acp`
- `zaya-acp`
- `python -m acp_adapter`

## Launching the ACP server

Any of the following starts Zaya in ACP mode:

```bash
zaya acp
```

```bash
zaya-acp
```

```bash
python -m acp_adapter
```

Zaya logs to stderr so stdout remains reserved for ACP JSON-RPC traffic.

## Editor setup

### VS Code

Install an ACP client extension, then point it at the repo's `acp_registry/` directory.

Example settings snippet:

```json
{
  "acpClient.agents": [
    {
      "name": "zaya-agent",
      "registryDir": "/path/to/zaya-agent/acp_registry"
    }
  ]
}
```

### Zed

Example settings snippet:

```json
{
  "agent_servers": {
    "zaya-agent": {
      "type": "custom",
      "command": "zaya",
      "args": ["acp"],
    },
  },
}
```

### JetBrains

Use an ACP-compatible plugin and point it at:

```text
/path/to/zaya-agent/acp_registry
```

## Registry manifest

The ACP registry manifest lives at:

```text
acp_registry/agent.json
```

It advertises a command-based agent whose launch command is:

```text
zaya acp
```

## Configuration and credentials

ACP mode uses the same Zaya configuration as the CLI:

- `~/.zaya/.env`
- `~/.zaya/config.yaml`
- `~/.zaya/skills/`
- `~/.zaya/state.db`

Provider resolution uses Zaya' normal runtime resolver, so ACP inherits the currently configured provider and credentials.

## Session behavior

ACP sessions are tracked by the ACP adapter's in-memory session manager while the server is running.

Each session stores:

- session ID
- working directory
- selected model
- current conversation history
- cancel event

The underlying `AIAgent` still uses Zaya' normal persistence/logging paths, but ACP `list/load/resume/fork` are scoped to the currently running ACP server process.

## Working directory behavior

ACP sessions bind the editor's cwd to the Zaya task ID so file and terminal tools run relative to the editor workspace, not the server process cwd.

## Approvals

Dangerous terminal commands can be routed back to the editor as approval prompts. ACP approval options are simpler than the CLI flow:

- allow once
- allow always
- deny

On timeout or error, the approval bridge denies the request.

## Troubleshooting

### ACP agent does not appear in the editor

Check:

- the editor is pointed at the correct `acp_registry/` path
- Zaya is installed and on your PATH
- the ACP extra is installed (`pip install -e '.[acp]'`)

### ACP starts but immediately errors

Try these checks:

```bash
zaya doctor
zaya status
zaya acp
```

### Missing credentials

ACP mode does not have its own login flow. It uses Zaya' existing provider setup. Configure credentials with:

```bash
zaya model
```

or by editing `~/.zaya/.env`.

## See also

- [ACP Internals](../../developer-guide/acp-internals.md)
- [Provider Runtime Resolution](../../developer-guide/provider-runtime.md)
- [Tools Runtime](../../developer-guide/tools-runtime.md)
