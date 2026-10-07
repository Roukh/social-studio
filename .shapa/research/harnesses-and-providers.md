---
id: harnesses-and-providers
type: reference
created: "2026-10-01T00:00:00Z"
consequence: 7
locus: output
summary: Headless flags/auth for claude/opencode/codex/gemini, Anthropic subscription policy, multi-provider libs, Agent Skills/MCP, Python-vs-Rust numbers.
scope: repo
status: active
---

# Harnesses and providers

Research for the social-studio CLI: drives existing agent harnesses headless (one isolated session per video), may later build its own API agent loop.

## Question

How do Claude Code, OpenCode, and Codex run headless with isolated config; what does Anthropic permit for subscription-credential use from third-party tools (vs OpenAI); which multi-provider Python/Rust libraries exist; and what do Agent Skills and MCP SDKs offer a future built-in loop.

## Method

Read each harness's CLI/headless/legal docs, library docs (PyPI, GitHub, crates.io), and Anthropic's legal/compliance page, 2026-10-01. Secondary press used only for history/enforcement, flagged as such. Hermes Agent and clawbot/OpenClaw were researched in depth but condensed here: the operator ruled (ruling 1, 2026-10-01) to drive existing harnesses now, not adopt either project.

## Findings

### Headless invocation and isolation per harness

| Harness | Non-interactive call | Structured output | Isolation mechanism |
|---|---|---|---|
| Claude Code | `claude -p "<prompt>"` | `--output-format text\|json\|stream-json` | `CLAUDE_CONFIG_DIR` + `--bare` (skips hooks/skills/plugins/MCP/CLAUDE.md, never reads OAuth/keychain) |
| OpenCode | `opencode run [msg]` | `--format default\|json` | `OPENCODE_CONFIG_CONTENT` (inline JSON, skips file discovery) |
| Codex CLI | `codex exec "<prompt>"` | `--json` (JSONL) | `--ignore-user-config` + `-c k=v`; auth still reads `$CODEX_HOME` — redirect that var for full isolation |

Claude Code also: `--strict-mcp-config`, `--permission-mode` (incl. `bypassPermissions`), `--system-prompt[-file]` (full replacement, needed here), Bash-tool sandboxing (Seatbelt macOS / bubblewrap Linux, matching this CLI's approach); `CLAUDE_CONFIG_DIR` is documented for "ephemeral containers." Codex also has `--sandbox {read-only|workspace-write|danger-full-access}` and `--oss`/`--local-provider {lmstudio|ollama}`. OpenCode (TS/Bun, MIT, 211k stars) removed Claude Pro/Max account-key auth "following Anthropic's legal requests" (The Register, 2026-02-20).

### Anthropic subscription-auth policy vs OpenAI

Anthropic's "Legal and compliance" page (fetched 2026-10-01): OAuth login is "intended exclusively for purchasers of Claude Free/Pro/Max/Team/Enterprise... to support ordinary use of Claude Code." Third parties must use API-key auth, not Free/Pro/Max credentials on users' behalf, and may not collect/store/intermediate Claude.ai credentials. An unmodified `claude` binary may still be used by an end user signed in with their own subscription, even hosted by a platform, provided each end user pays with their own credential.

Design rule: human-run mode shells out to the user's own unmodified `claude` binary. Tool/SDK mode requires the operator's own `ANTHROPIC_API_KEY`/cloud credential — never harvest or proxy OAuth/session tokens.

OpenAI contrast: "Sign in with ChatGPT" (DevDay, 2026-09-29) lets Plus/Pro subscribers use their plan's allowance in third-party tools via OAuth, with a per-app weekly cap; 16 launch partners, including OpenCode and OpenClaw. The opposite policy choice from Anthropic's, and a sanctioned integration point for a Codex backend. (Secondary-source based; OpenAI's own help page returned HTTP 403.)

### Multi-provider libraries

| Library | Lang | Scope | Footprint |
|---|---|---|---|
| LiteLLM | Python | unified client + proxy, 100+ providers | heavy: v1.103.2, 213.5 MB release, 106 deps |
| any-llm (mozilla-ai) | Python | unified client; required 7 all "verified" | thin: per-provider extras |
| pydantic-ai | Python | full agent framework; native + OpenAI-compat presets | framework-sized |
| aisuite | Python | unified client + light agent layer; no native xAI/DeepSeek/OpenRouter | lightweight |
| rig / rig-core | Rust | full agent framework, 20+ providers, WASM-compatible | native binary |
| genai (rust-genai) | Rust | unified client, 25+ providers incl. all 7 required | thin, v0.6.5 |
| async-openai | Rust | OpenAI-shaped client; any OpenAI-compatible endpoint via `base_url` | thin, v0.41.1, 5.59M downloads |

One OpenAI-SDK-shaped client reaches 6 of 7 required providers via compatible base URLs: xAI `api.x.ai/v1`; DeepSeek `api.deepseek.com`; Gemini's generativelanguage endpoint (Google's own forum: "not fully implemented," partial parity); OpenRouter (400+ models, filter tool-capable via `?supported_parameters=tools`); Ollama `localhost:11434/v1` ("a subset of the OpenAI API"). Only Anthropic needs a native client.

Verdict: hand-roll a thin two-branch client (OpenAI-compatible + Anthropic-native) over LiteLLM; any-llm is the pre-built middle ground if a dependency is acceptable.

### Agent Skills standard and MCP

Agent Skills: Claude-only from 2025-10-16, opened as a cross-platform standard 2025-12-18 (spec + SDK at agentskills.io). A skill is a directory with `SKILL.md` (frontmatter `name`+`description` min.) plus optional scripts/references/assets; progressive loading (name/description at startup, body on match, resources on demand). 40+ adopting platforms claimed (Claude Code, Codex, Copilot, Cursor, VS Code). Composition patterns built as `SKILL.md` skills would be portable to any harness driven as a backend. Caveat: live spec page not directly fetched — verify fields before building a parser.

MCP: official SDKs under the `modelcontextprotocol` org — Python `python-sdk` (reworked for the 2026-07-28 spec) and Rust `rust-sdk` (tokio-based, `rmcp` core + `rmcp-macros`). Either supports both directions a built-in loop needs: the CLI as an MCP server, and consuming MCP servers as tools.

### Python vs Rust (vs Node) for a built-in agent loop

No authoritative LOC benchmark found; qualitative only. Python (any-llm/aisuite): single-provider wrapper under 50 lines; full tool-call loop ~100–300 lines, native try/except, dicts for tool JSON. Rust (genai/async-openai): similar wrapper size but needs explicit tokio setup, `Result`-based errors, serde structs per provider — more boilerplate unless genai/rig absorb it.

Distribution: Python via `uv tool install` (fast, isolated venv, can fetch its own interpreter) vs PyInstaller `--onefile` (~8.8 MB base, driven by imports; thin-dependency build lands in the tens-of-MB range). Rust via `cargo install` (needs a toolchain) vs cargo-dist static binaries (used by `uv`/`ruff` themselves); natural stack runs ~10–40 MB unoptimized, low single-digit MB after LTO/strip. CLI frameworks: Python has Click/Typer/cyclopts; Rust has one default, clap (1.16B+ downloads).

Node: the render engine (HyperFrames) is already a hard Node 22+/Puppeteer/FFmpeg dependency, and both named inspirations (OpenCode, OpenClaw) are TS/Node — but Node lacks Python's venv or Rust's single-binary distribution story; not size-benchmarked here.

**Python was chosen** (operator ruling) over Rust for the built-in loop; Node remains the renderer's language regardless.

### Hermes Agent / OpenClaw (condensed)

| Project | Relevant fact |
|---|---|
| Hermes Agent (NousResearch) | Python core; 7 terminal-isolation backends via one YAML key. Not adopted — unneeded once driving existing harnesses directly. |
| clawbot / OpenClaw (TS/Node, 391k stars) | Renamed Clawdbot → Moltbot → OpenClaw (early 2026). CVE-2026-25253 (CVSS 8.8): Control UI auto-opened a WebSocket to a query-string `gatewayUrl`, leaking the auth token. Lesson: never auto-connect to an untrusted callback URL; treat open skill registries as a supply-chain risk. |

## Sources

- https://code.claude.com/docs/en/cli-reference, /headless, /sandboxing, /settings, /legal-and-compliance
- https://opencode.ai/docs/cli/, /config/, /agents/ ; https://github.com/sst/opencode
- https://learn.chatgpt.com/docs/developer-commands?surface=cli
- https://www.theregister.com/2026/02/20/anthropic_clarifies_ban_third_party_claude_access/ ; https://thenewstack.io/sign-in-with-chatgpt/
- https://pypi.org/project/litellm/ ; https://github.com/mozilla-ai/any-llm ; https://github.com/pydantic/pydantic-ai ; https://github.com/andrewyng/aisuite
- https://github.com/0xPlaygrounds/rig ; https://github.com/jeremychone/rust-genai ; https://crates.io/crates/async-openai
- https://docs.x.ai/docs/overview ; https://api-docs.deepseek.com/ ; https://ai.google.dev/gemini-api/docs/openai ; https://openrouter.ai/docs/guides/features/tool-calling ; https://docs.ollama.com/api/openai-compatibility
- https://siliconangle.com/2025/12/18/anthropic-makes-agent-skills-open-standard/ ; https://github.com/modelcontextprotocol/python-sdk ; https://github.com/modelcontextprotocol/rust-sdk
- https://pipx.pypa.io/latest/explanation/comparisons.html ; https://axodotdev.github.io/cargo-dist/ ; https://crates.io/crates/clap
- https://github.com/NousResearch/hermes-agent ; https://en.wikipedia.org/wiki/OpenClaw ; https://www.sentinelone.com/vulnerability-database/cve-2026-25253/

## Date

Gathered 2026-10-01; condensed 2026-10-06 for the format 4 wiki.
