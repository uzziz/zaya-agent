<p align="center">
  <img src="assets/banner.png" alt="Zaya Agent" width="100%">
</p>

# Zaya Agent ☤

<p align="center">
  <a href="https://zaya-stack.vercel.app/docs/"><img src="https://img.shields.io/badge/Docs-zaya--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://github.com/uzziz/zaya-agent"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/uzziz/zaya-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Built%20by-Nous%20Research-blueviolet?style=for-the-badge" alt="Built by Nous Research"></a>
</p>

**The self-improving AI agent built by [Nous Research](https://nousresearch.com).** It's the only agent with a built-in learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

Use any model you want — [Nous Portal](https://portal.nousresearch.com), [OpenRouter](https://openrouter.ai) (200+ models), [Xiaomi MiMo](https://platform.xiaomimimo.com), [z.ai/GLM](https://z.ai), [Kimi/Moonshot](https://platform.moonshot.ai), [MiniMax](https://www.minimax.io), [Hugging Face](https://huggingface.co), OpenAI, or your own endpoint. Switch with `zaya model` — no code changes, no lock-in.

<table>
<tr><td><b>A real terminal interface</b></td><td>Full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Lives where you do</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, and CLI — all from a single gateway process. Voice memo transcription, cross-platform conversation continuity.</td></tr>
<tr><td><b>A closed learning loop</b></td><td>Agent-curated memory with periodic nudges. Autonomous skill creation after complex tasks. Skills self-improve during use. FTS5 session search with LLM summarization for cross-session recall. <a href="https://github.com/plastic-labs/honcho">Honcho</a> dialectic user modeling. Compatible with the <a href="https://agentskills.io">agentskills.io</a> open standard.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>Built-in cron scheduler with delivery to any platform. Daily reports, nightly backups, weekly audits — all in natural language, running unattended.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Spawn isolated subagents for parallel workstreams. Write Python scripts that call tools via RPC, collapsing multi-step pipelines into zero-context-cost turns.</td></tr>
<tr><td><b>Runs anywhere, not just your laptop</b></td><td>Six terminal backends — local, Docker, SSH, Daytona, Singularity, and Modal. Daytona and Modal offer serverless persistence — your agent's environment hibernates when idle and wakes on demand, costing nearly nothing between sessions. Run it on a $5 VPS or a GPU cluster.</td></tr>
<tr><td><b>Research-ready</b></td><td>Batch trajectory generation, Atropos RL environments, trajectory compression for training the next generation of tool-calling models.</td></tr>
</table>

---

## Quick Install

```bash
curl -fsSL https://raw.githubusercontent.com/uzziz/zaya-agent/main/scripts/install.sh | bash
```

Works on Linux, macOS, WSL2, and Android via Termux. The installer handles the platform-specific setup for you.

> **Android / Termux:** The tested manual path is documented in the [Termux guide](https://zaya-stack.vercel.app/docs/getting-started/termux). On Termux, Zaya installs a curated `.[termux]` extra because the full `.[all]` extra currently pulls Android-incompatible voice dependencies.
>
> **Windows:** Native Windows is not supported. Please install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) and run the command above.

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
zaya              # start chatting!
```

---

## Getting Started

```bash
zaya              # Interactive CLI — start a conversation
zaya model        # Choose your LLM provider and model
zaya tools        # Configure which tools are enabled
zaya config set   # Set individual config values
zaya gateway      # Start the messaging gateway (Telegram, Discord, etc.)
zaya setup        # Run the full setup wizard (configures everything at once)
zaya claw migrate # Migrate from OpenClaw (if coming from OpenClaw)
zaya update       # Update to the latest version
zaya doctor       # Diagnose any issues
```

📖 **[Full documentation →](https://zaya-stack.vercel.app/docs/)**

## CLI vs Messaging Quick Reference

Zaya has two entry points: start the terminal UI with `zaya`, or run the gateway and talk to it from Telegram, Discord, Slack, WhatsApp, Signal, or Email. Once you're in a conversation, many slash commands are shared across both interfaces.

| Action | CLI | Messaging platforms |
|---------|-----|---------------------|
| Start chatting | `zaya` | Run `zaya gateway setup` + `zaya gateway start`, then send the bot a message |
| Start fresh conversation | `/new` or `/reset` | `/new` or `/reset` |
| Change model | `/model [provider:model]` | `/model [provider:model]` |
| Set a personality | `/personality [name]` | `/personality [name]` |
| Retry or undo the last turn | `/retry`, `/undo` | `/retry`, `/undo` |
| Compress context / check usage | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]` |
| Browse skills | `/skills` or `/<skill-name>` | `/skills` or `/<skill-name>` |
| Interrupt current work | `Ctrl+C` or send a new message | `/stop` or send a new message |
| Platform-specific status | `/platforms` | `/status`, `/sethome` |

For the full command lists, see the [CLI guide](https://zaya-stack.vercel.app/docs/user-guide/cli) and the [Messaging Gateway guide](https://zaya-stack.vercel.app/docs/user-guide/messaging).

---

## Documentation

All documentation lives at **[zaya-stack.vercel.app/docs](https://zaya-stack.vercel.app/docs/)**:

| Section | What's Covered |
|---------|---------------|
| [Quickstart](https://zaya-stack.vercel.app/docs/getting-started/quickstart) | Install → setup → first conversation in 2 minutes |
| [CLI Usage](https://zaya-stack.vercel.app/docs/user-guide/cli) | Commands, keybindings, personalities, sessions |
| [Configuration](https://zaya-stack.vercel.app/docs/user-guide/configuration) | Config file, providers, models, all options |
| [Messaging Gateway](https://zaya-stack.vercel.app/docs/user-guide/messaging) | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](https://zaya-stack.vercel.app/docs/user-guide/security) | Command approval, DM pairing, container isolation |
| [Tools & Toolsets](https://zaya-stack.vercel.app/docs/user-guide/features/tools) | 40+ tools, toolset system, terminal backends |
| [Skills System](https://zaya-stack.vercel.app/docs/user-guide/features/skills) | Procedural memory, Skills Hub, creating skills |
| [Memory](https://zaya-stack.vercel.app/docs/user-guide/features/memory) | Persistent memory, user profiles, best practices |
| [MCP Integration](https://zaya-stack.vercel.app/docs/user-guide/features/mcp) | Connect any MCP server for extended capabilities |
| [Cron Scheduling](https://zaya-stack.vercel.app/docs/user-guide/features/cron) | Scheduled tasks with platform delivery |
| [Context Files](https://zaya-stack.vercel.app/docs/user-guide/features/context-files) | Project context that shapes every conversation |
| [Architecture](https://zaya-stack.vercel.app/docs/developer-guide/architecture) | Project structure, agent loop, key classes |
| [Contributing](https://zaya-stack.vercel.app/docs/developer-guide/contributing) | Development setup, PR process, code style |
| [CLI Reference](https://zaya-stack.vercel.app/docs/reference/cli-commands) | All commands and flags |
| [Environment Variables](https://zaya-stack.vercel.app/docs/reference/environment-variables) | Complete env var reference |

---

## Migrating from OpenClaw

If you're coming from OpenClaw, Zaya can automatically import your settings, memories, skills, and API keys.

**During first-time setup:** The setup wizard (`zaya setup`) automatically detects `~/.openclaw` and offers to migrate before configuration begins.

**Anytime after install:**

```bash
zaya claw migrate              # Interactive migration (full preset)
zaya claw migrate --dry-run    # Preview what would be migrated
zaya claw migrate --preset user-data   # Migrate without secrets
zaya claw migrate --overwrite  # Overwrite existing conflicts
```

What gets imported:
- **SOUL.md** — persona file
- **Memories** — MEMORY.md and USER.md entries
- **Skills** — user-created skills → `~/.zaya/skills/openclaw-imports/`
- **Command allowlist** — approval patterns
- **Messaging settings** — platform configs, allowed users, working directory
- **API keys** — allowlisted secrets (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS assets** — workspace audio files
- **Workspace instructions** — AGENTS.md (with `--workspace-target`)

See `zaya claw migrate --help` for all options, or use the `openclaw-migration` skill for an interactive agent-guided migration with dry-run previews.

---

## Contributing

We welcome contributions! See the [Contributing Guide](https://zaya-stack.vercel.app/docs/developer-guide/contributing) for development setup, code style, and PR process.

Quick start for contributors:

```bash
git clone https://github.com/uzziz/zaya-agent.git
cd zaya-agent
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"
python -m pytest tests/ -q
```

> **RL Training (optional):** To work on the RL/Tinker-Atropos integration:
> ```bash
> git submodule update --init tinker-atropos
> uv pip install -e "./tinker-atropos"
> ```

---

## Community

- 💬 [Discord](https://github.com/uzziz/zaya-agent)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/uzziz/zaya-agent/issues)
- 💡 [Discussions](https://github.com/uzziz/zaya-agent/discussions)
- 🔌 [ZayaClaw](https://github.com/AaronWong1999/zayaclaw) — Community WeChat bridge: Run Zaya Agent and OpenClaw on the same WeChat account.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Nous Research](https://nousresearch.com).
