---
id: cli-conventions-and-isolation
type: reference
created: "2026-10-01T00:00:00Z"
consequence: 7
locus: output
summary: CLI conventions, agent/MCP token costs, sandbox+isolation options, SQLite queue patterns, and OS schedulers for the social-studio CLI.
scope: repo
status: active
---

# CLI conventions and isolation

Research backing social-studio's argparse CLI design, agent exposure, session isolation, SQLite queue, and posting scheduler. Gathered 2026-10-01.

## Question

What CLI conventions, agent-exposure patterns, sandbox/isolation options, SQLite queue/scheduler patterns, and OS scheduling mechanisms should shape a stdlib-only Python CLI used by both humans and agents?

## Method

Read clig.dev, POSIX/GNU option conventions, the XDG spec, BSD sysexits.h, docs for gh/Stripe/Vercel/Supabase/AWS CLI/Docker/kubectl, Anthropic's agent-tool-design post, Agent Skills/MCP docs, OWASP Excessive Agency, sandbox docs for Claude Code/Codex plus bubblewrap/Landlock/firejail/Docker-Podman-rootless, SQLite docs, systemd/launchd/schtasks docs, and 2025-26 MCP-vs-CLI token-cost writeups. Direct retrieval except where flagged unverified.

## Findings

### CLI conventions

| Area | Rule |
|---|---|
| Design | human-first, composable, consistent, discoverable (clig.dev) |
| Flags | GNU long+short; `--name=value`; POSIX `--` ends options |
| XDG dirs | config/data/state/cache = `~/.config`/`~/.local/share`/`~/.local/state`/`~/.cache` → presets / DB+videos / event log / render cache |
| Exit codes | sysexits.h 0/64/65/66/69/70/75/77/78 = OK/USAGE/DATAERR/NOINPUT/UNAVAILABLE/SOFTWARE/TEMPFAIL/NOPERM/CONFIG |
| I/O | stdout=result, stderr=logs/errors; `--json` w/ explicit field list (gh-style); NDJSON for streams (jsonlines.org; ndjson.org squatted) |
| Scripting flags | `-q`/`-v`, `--dry-run`, `--yes` (required for destructive ops, non-TTY), `NO_COLOR` |
| Non-interactive | fail if no TTY and no `--no-input`; Vercel defaults `--non-interactive` ON under a detected agent caller |
| Config | flags>env>project config>user config>defaults; TOML over YAML; named `[profile]` sections (AWS CLI) |
| Lifecycle | `init` scaffolds non-interactively; `doctor` exits nonzero on any problem (brew pattern); `version` |
| Structure | noun-first tree (video/queue/schedule/preset); example-led help; man page shares `--help`'s source |

### Agent-first design and token costs

| Fact | Detail |
|---|---|
| Tool design | `response_format` concise/detailed; paginate/filter/truncate w/ defaults; Claude Code caps responses at 25k tokens; actionable errors, not stack traces (anthropic.com/engineering/writing-tools-for-agents) |
| MCP schema cost | GitHub MCP server: 93 tools, ~55k tokens of schema upfront (Huntley) |
| CLI vs MCP | 145k MCP vs 4,150 CLI tokens on a 50-device task (35x); ~200 tok/CLI call; other reports: 4x-32x, +28% task completion for CLI (jannikreinhard.com; firecrawl.dev) |
| Verdict | MCP's value is a bounded gateway, not token efficiency — CLI primary, unpublished `mcp serve` additive |
| Errors | Stripe model: `type`/`code`/`message`/`param`/`doc_url` |
| Docs for agents | llms.txt = doc index for LLMs; AGENTS.md = repo-root agent README (60k+ repos), distinct from SKILL.md |
| SKILL.md levels | L1 metadata ~100 tok always loaded; L2 body <5k tok on trigger; L3 scripts/refs as-needed, code never in context |
| Idempotency | Stripe key replays first response, 255-char limit, pruned ≥24h |
| Auth pattern | browser OAuth for humans; bearer token via flag/env for agents; OS keyring preferred over plaintext |

### Exposing the CLI to harnesses

- `mcp serve` as a CLI mode is precedented: Claude Code, Stripe, Supabase (`read_only`/`project_ref`/`features` flags), Vercel, GitHub (`--toolsets`, small default + `all` opt-in, to cut context). social-studio's unpublished `mcp serve` should match, over the CLI's own broker.
- Role scoping, rising strength: `agent ...` namespace → server-enforced `--role` → shorter agent-only MCP tool list → capability tokens (GitHub fine-grained PATs; Stripe agent-tagged keys w/ mandatory approval; SQLite `sqlite3_set_authorizer()`).
- Recommended: `agent ...`/restricted `mcp serve` over an `agent_visible_videos` view, authorizer-locked connection, narrow named platform credential.

### Isolation options compared

Two problems: hygiene (fresh scratch state) vs security — Willison's "lethal trifecta" (private data + untrusted content + external communication = exfiltration); OWASP "Excessive Agency" names approval before social posts publish as its own example.

| Tool | What it blocks | Network restriction |
|---|---|---|
| bubblewrap | unprivileged userns; mount/PID/IPC/UTS namespaces; construction tool only | binary: full or loopback-only, no domain concept |
| Landlock | in-process LSM, self-restricts, tightens-only; FS since Linux 5.13 | TCP bind/connect allowlist since ABI v4, UDP v10 |
| firejail | SUID wrapper, namespaces+seccomp+caps, profiles | `--net=none`/`--netfilter`(iptables)/`--netlock`(startup IPs) |
| Docker/Podman rootless | userns containers, bounds host privilege only | none |
| Claude Code sandbox | bwrap+socat/Seatbelt; writes confined to cwd+temp; reads default-open (DB/.env need explicit deny); no unsandboxed-retry escape; wraps only Bash/PowerShell/Monitor | forced proxy, default-empty allowlist, hostname-only unless `tlsTerminate` |
| Codex CLI | `read-only`/`workspace-write`(default)/`danger-full-access`; bwrap+seccomp/Seatbelt/native | off by default; TOML domain allow/deny, deny wins |

Only Claude Code/Codex do proxy-based hostname allow/deny; bubblewrap needs a cooperating proxy for domain granularity — the gap in social-studio's open network-allowlist work (proxy + unshared netns, as Claude Code's sandbox-runtime does).

Mitigation (Auth0 "separate decide from do"; "AI secret broker"): never hand the agent process the DB or `.env` at all. Route persistence/credentials through a narrow broker exposing only task-shaped verbs (`get-next-job`, `store-video`, `request-publish`), never generic SQL/file-read.

### SQLite queue/scheduler patterns

- WAL: readers never block writers or vice versa; single-host only; one writer at a time; pairs with `PRAGMA synchronous=NORMAL` — right mode for CLI+broker+scheduler sharing one file.
- `CHECK(status IN (...))` can't see old→new; a `BEFORE UPDATE` trigger + `RAISE(ABORT,...)` rejects illegal transitions (generated→{approved,rejected,needs-revision}; needs-revision→{approved,rejected}; approved→scheduled; scheduled→{posted,approved}).
- Partial unique indexes: `WHERE status='scheduled'` on `(platform,time)` → one video per open slot; `WHERE platform_post_id IS NOT NULL` → one post id per platform.
- Append-only `video_status_events`, written by an `AFTER UPDATE` trigger alongside the validation trigger.
- Atomic claim (SQLite ≥3.35.0): `UPDATE videos SET status='scheduled' WHERE id=(SELECT id FROM videos WHERE status='approved' ORDER BY created_at LIMIT 1) RETURNING *;` — race-free, zero rows = already claimed.
- Hiding assigned rows: `CREATE VIEW agent_visible_videos AS SELECT * FROM videos WHERE status NOT IN ('scheduled','posted');` — agent broker queries only this; pair with `sqlite3_set_authorizer()`.
- Idempotent publish: store `platform_post_id`; check existing non-null value before calling the platform API again.
- Migrations: `PRAGMA user_version`; bump as the last step of each migration, check at startup.

### Scheduling per OS

| OS | Schedule by | Missed-run catch-up |
|---|---|---|
| systemd user timers (today) | `.timer`+`.service`, `OnCalendar=`/`OnBootSec=` | `Persistent=true` reruns on next boot/wake |
| cron (fallback) | 5-field schedule | none |
| launchd (macOS, open idea) | plist, `StartCalendarInterval` dict | automatic on wake, no opt-in needed |
| Task Scheduler (Windows, open idea) | `schtasks /create /sc once\|daily\|weekly\|monthly` | handled by the scheduler service |

A daemon still needs a native supervisor (`Restart=`, a LaunchAgent, a Windows service) to survive logout/crash/reboot — the real choice is whether the native scheduler invokes a short-lived `publish` directly or keeps a long-lived `daemon` alive.

Hermes Agent's `hermes cron create "every 1d at 09:00" ... --workdir` binds runs to a skill, disallows recursive cron creation. OpenClaw's own open issues (#26370, #16053) show its cron jobs are global, not per-agent-scoped — a gap to design around from day one. No cross-platform scheduler library found; norm is a daemon's loop or a thin per-OS installer behind one `schedule install`.

### Required command checklist

| Area | Commands / conventions |
|---|---|
| Core human | `init`, `doctor` (nonzero on any problem), `version`, `config get/set/list`, `auth login/status/logout`, `completion`, noun-first tree, example-led help, man page sharing `--help`'s source |
| Output/automation | `--json` w/ named fields; NDJSON for streams; `-q`/`-v`; auto non-interactive detection + required `--yes`; `--dry-run` on mutators; `NO_COLOR`; sysexits codes; structured `--json` errors; `--limit`+cursor; idempotency key on `post`/`schedule` |
| Harness exposure | `mcp serve` (curated list, unpublished); shipped `SKILL.md`; `AGENTS.md` at repo root; full-vs-agent split via `agent_visible_videos`; authorizer-locked agent connection; narrow named credential; human-approval gate before publish |
| Isolation | fresh per-run working dir; OS sandbox (bwrap today) with no path to the real DB/.env; default-deny network + small allowlist via unbypassable proxy (open work — network open today); no retry-unsandboxed escape; creds only via a narrow broker |
| Data layer | `WAL`; `CHECK`+`BEFORE UPDATE` transition trigger; partial unique indexes; append-only `video_status_events`; `UPDATE...RETURNING` claim; `user_version` migrations |
| Scheduling | `schedule install` (systemd today; launchd/`schtasks` open ideas), invoking `schedule run`; `Persistent=true`/wake-run catch-up; cron/daemon fallback |

## Sources

clig.dev; POSIX utility syntax guidelines; getopt_long; freedesktop.org basedir-spec; BSD sysexits.h; jsonlines.org; vercel.com/docs/cli; AWS CLI docs; toml.io; docs.npmjs.com; docs.brew.sh; cli.github.com/manual; anthropic.com/engineering/writing-tools-for-agents; simonwillison.net (lethal-trifecta, too-many-mcps); jannikreinhard.com; firecrawl.dev/blog/mcp-vs-cli; docs.stripe.com (api/errors, idempotent_requests, keys, mcp); llmstxt.org; agents.md; platform.claude.com agent-skills; code.claude.com/docs (mcp, sandboxing); supabase.com/docs mcp; github.com/github/github-mcp-server; docs.github.com fine-grained-PATs; modelcontextprotocol.io security-best-practices; genai.owasp.org llm062025-excessive-agency; github.com/containers/bubblewrap; docs.kernel.org/landlock; github.com/netblue30/firejail; docs.docker.com/rootless; docs.podman.io; learn.chatgpt.com/docs/agent-approvals-security; auth0.com blog; sqlite.org (wal, lang_createtable, lang_createtrigger, lang_createindex, partialindex, lang_returning, lang_createview, pragma, c3ref/set_authorizer); man.archlinux.org systemd.timer/service; man7.org crontab.5; developer.apple.com ScheduledJobs; learn.microsoft.com schtasks-create; github.com/NousResearch/hermes-agent; docs.openclaw.ai/automation; github.com/openclaw/openclaw issues 26370/16053.

## Date

Gathered 2026-10-01; condensed 2026-10-06 for the format 4 wiki.
