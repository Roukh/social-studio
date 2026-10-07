---
id: core
type: reference
created: "2026-10-06T23:59:00Z"
consequence: 8
locus: output
summary: Box core - project discovery, config and .env, the repo write boundary, presets with extends and --set, validate_preset, R0 guards, formats, the MCP registry.
scope: repo
status: active
---

# Box: core

Part of [[index]]. Deterministic plumbing every other box uses; no LLM.

| Field | Value |
|---|---|
| Purpose | Find the project, read and write its config and `.env`, enforce the write boundary, load and validate presets |
| Owned paths | `src/social_studio/core.py` (626 lines); the project's `social-studio.toml`, `.env`, `mcp.toml` contracts |
| In | `--project`, `$SOCIAL_STUDIO_PROJECT`, the current folder or a `social/` folder below it; preset names or paths; `--set KEY=VALUE` |
| Out | `Ctx` (project, config, env, `boundary`, `studio_dir`, `library_dir`, `db_path`); `Preset`; `format_sets`; `mcp_registry`; errors mapped to sysexits |

## Contracts

- Project folder: `social-studio.toml`, `.env` (rewritten 0600), `presets/`, `library/`, `drafts/`, `.studio/` (`library.db`, `approval/`, `sessions/`, `engine/`, `cache/`). `init` writes a `.gitignore` for `.env`, `.studio/`, `library/`, `drafts/`.
- Presets: searched in the project's `presets/`, configured `preset_paths` and the built-in `presets/`; `extends` merges; `--set` overrides by dotted key.
- `mcp.toml`: `[servers.NAME]` entries, edited only by a human; each entry's `secrets` lists the only `${VAR}` names it may fill.
- `FORMATS`: 9:16 1080x1920, 4:5 1080x1350, 1:1 1080x1080, 16:9 1920x1080. Only 9:16 keeps the preset's safe zone; the others get 5 % title-safe on every edge. `SOUNDS`: none, sfx, bed+sfx, sfx+voice, bed+sfx+voice. `EFFORTS`: low to max.

## Invariants

- Writes stay inside the git work tree that holds the project (`Ctx.boundary`); paths in the database are project-relative (rule R5).
- `path_problem` refuses anything outside the repo, the project folder itself, its `.env`, `.studio/`, `library/`, `drafts/` and any `.env*` file. Files shipped inside a built-in preset are always allowed, `.env*` never.
- `GUARDED_PRESET` keys (`agent.mcp`, `agent.plugins`, `agent.skills`, `agent.engine_skills`, `assets`, `brand.fonts`, `render`) and `GUARDED_CONFIG` keys (`preset_paths`, `sandbox`, `backend.*.bin|auth|env`) change only by a human (issue I1, R0 tests).
- `require_human` needs a TTY and `SOCIAL_STUDIO_ROLE != agent`.
- `validate_preset` rejects aliased font families (`ALIASED_FONTS`, issue I4), missing font and asset files, `agent.rounds` outside 1-5, unknown efforts and sounds, unknown `agent.package_skills`, `video.end_card_max` outside (0, 1), and every R0 problem (registry-only MCP, slug skill names, paths inside the repo).
- The tool stays brand-neutral: no brand tokens in `data/` or built-in presets other than their own.

## Rules and gotchas

- Rules: R2 (session isolation), R5 (project folder and boundary), R11 (format per run).
- Issues: I1 (preset overrides), I4 (font aliasing).
- Old XDG folders from before the project-folder move (`~/.local/share/social-studio`, `~/.config/social-studio`, `~/.cache/hyperframes`) are no longer read; whether to delete the baseline evidence there is the operator's call.
