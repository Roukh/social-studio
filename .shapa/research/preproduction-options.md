---
id: preproduction-options
type: reference
created: "2026-10-02T10:30:00Z"
consequence: 8
locus: output
summary: Pre-production options (2026-10-02) - story stage, keyframe boards, a pinned skill registry, a vetted MCP registry - candidates, licences, rulings 6-11.
scope: repo
status: active
---

# Pre-production options (2026-10-02)

The research behind the story stage, keyframe boards, the vendored skill pack and the MCP registry. The skill pack and the MCP registry are built; the story and board stages are ledger feature F2 (rulings 6-7, rule R6).

## Question

What should happen before any motion is built (story, keyframe boards), which skills should ship inside social-studio, and how should MCP servers be admitted safely?

## Method

- The operator's request, 2026-10-02: "I want an additional screen planning - like a key frames pre plan, story creation skills, other external skills to add directly within social-studio, mcp registers aswell".
- Read the pinned engine `E` = `social/.studio/engine/hyperframes-0.8.106/` (upstream `heygen-com/hyperframes@b5e3ffa6`, Apache-2.0, with `LICENSE`, `CREDITS.md`, a `skills-manifest.json` hashing each skill, no NOTICE).
- External skills and servers checked with `gh api` reads and live fetches on 2026-10-02; the operator's global skills lock (source, skillPath, computedHash per skill) served as the precedent for a lock.

## Findings

### State on 2026-10-02

- No story step: `brief.json` was written in the same pass as the HTML. No boards: the maker only snapshotted a finished composition.
- 5 engine skills from an unhashed tag tarball without its LICENSE; sessions also loaded 18 built-in Claude Code skills and tools (Workflow, CronCreate, RemoteTrigger, DesignSync).
- MCP: free-form `agent.mcp` entries, `${VAR}` resolving any variable, open network. That was issue I1, fixed by R0 first.

### A. Story

| Option | What | Outcome |
|---|---|---|
| A1 inline | maker writes brief, spine and beats before HTML | — |
| A2 pitch round | engine `skills/hyperframes/references/pitch-round.md` L11-36: 4 grounding questions, 5 concepts on 5 paths (at least 2 with p < 0.10), a silhouette check drops lookalikes, picks a winner and names "the most typical direction deliberately left behind"; judged on a rubric with `design-tournament` | ruling 6: used when there is no operator brief (job J6) |
| A3 human pick | pitches stop at the operator | — |

- Artifacts: `BRIEF.md` (message, audience, angle, length, aspect); the echo line "This video tells [audience] that [message]." (`story-spine.md` L26); a beat list `NN — Name (start–end, ~dur)` whose durations sum (`storyboard-recipe.md` L21-32).
- Structures that fit 10-18 s: And-But-Therefore (Randy Olson); Story Spine (Kenn Adams); PAS, BAB and demo loop (`product-launch-video` `story-design.md` L45-57). TikTok wants the proposition in the first 3 s and the hook within 6 s.

### B. Keyframe boards

- A board is the key pose of one shot (start, key, end states) as static HTML at the final layout with real fonts and tokens; element ids stay the same across a shot's states. Engine backing: "storyboard frames are KEYFRAMES, not slides" (`figma/SKILL.md` L108); keyframes are "a pose contract" (`hyperframes-keyframes/SKILL.md` L16, L60-71).
- B1 gate inside the session; **B2 separate stage** (`make --boards` stops at a confirmed sheet, `board approve|revise|drop`, `make --from-board ID`); B3 B2 plus an animatic compared with `snapshot --against animatic.mp4`. Ruling 7: B2, operator approves (job J7).
- Rendering: `hyperframes compare a.html b.html ... --out sheet.png` (2-16 boards with `data-width`/`data-height`), or `snapshot --at`. The engine's contact sheet is fixed at 3 columns of 600 px (a 9-frame sheet is 1816x3295, seen by the model at 1102x2000), so we build a tiler: within 2000 px, safe-zone overlay, labels (shot, time, blueprint, text). The engine ships no storyboard template and no music-free timing validator.
- Critique sources: `design-adherence.md` L5-19; the scale table in `video-composition.md` L34-47; studio safe zones L94-108; story-spine traceability; impeccable's specificity verdict; frontend-design's list of AI habits.
- Data: a v2 `boards` table with its own status CHECK, transition trigger and `agent_boards` view; `videos.board_id`; board approval TTY-gated or signed under a separate namespace so it never passes as a video approval (rule R4).

### C. Skill registry

- C2 (chosen, ruling 8): vendored pack `skills/NAME/` plus a lock recording repo@sha, path, SPDX licence, tree sha256, size, roles; ship LICENSE and attributions (Apache-2.0 §4, CC-BY-4.0), mark modified files; each role mounts only its skills; `doctor` verifies hashes. Built 2026-10-06 as `data/skills/vendor/` with `skills.lock.json`; the doctor check is job J3.
- C3: `skills add REPO@SHA:PATH`, human-only, refusing branches and tags. The Claude Code plugin `sha` field is the most reliable pin found; SHA restore in `npx skills` has an open bug (vercel-labs/skills#2279).
- Distil rather than mount whole skills: sessions read under 1 % of the skills mounted on 2026-10-02.

| Role | Source (pin) | Licence |
|---|---|---|
| story | hyperframes@b5e3ffa6 pitch-round, brief format, story-spine, storyboard-recipe; `faceless` story-design | Apache-2.0 |
| story | design-tournament (operator's skill); writing-beats, writing-shape (mattpocock/skills) | operator; MIT |
| story | DirectorSKILL@c65ae0d (overlays named after real directors kept) | MIT |
| board | hyperframes storyboard-format, review-loop, keyframes pose contract, figma storyboards L106-129 | Apache-2.0 |
| board | anthropics/skills@8a1541c canvas-design, frontend-design; athemeroy `docs/production-brief.md`@497986b | Apache-2.0; CC-BY-4.0 |
| motion | hyperframes motion-language part 2, cut-catalog, `springEase`; emil-design-eng; impeccable animate, craft-floor | Apache-2.0; MIT |
| critique | impeccable critique; design-adherence | Apache-2.0 |

Excluded: Anthropic's brand-guidelines (its own brand) and office skills (proprietary); remotion-dev/skills (no licence, plus Remotion's paid automation tier); PDoomVideo and ai-video-storyboard-skill (no licence); ClaudeAnimationBase (built around a mascot); the product-launch script bank (real brand names); anything that calls `npx`, a catalog or a registry at run time.

### D. MCP registry

- D2 (built by R0): a vetted `mcp.toml` that only a human edits. Each entry: name, pinned package@version or image digest, transport, the env var names it declares (only those resolve), its hosts (for the network allowlist, job J8), roles, a spend cap. Presets name entries only. Public registries were rejected as the trust anchor: the official MCP Registry stores metadata only, leaves scanning to others, is in preview and cannot pin a commit; malicious servers shipped through open package registries (postmark-mcp, CVE-2025-6514, an Oura clone in Feb 2026).
- D3: `social-studio mcp serve` over stdio, agent verbs only. Ruling 11: never published (rule R10, job J14).

| Server (pin) | Use | Terms / auth | Fit then |
|---|---|---|---|
| playwright-mcp@f183dad; chrome-devtools-mcp@648a667 | reference capture outside sessions | Apache-2.0, no auth | high |
| fal.ai hosted or luminarylane/fal-mcp-server@398fe93; Replicate hosted or sena-labs@0f6279e | generated stills | no non-infringement warranty / each model's terms; key or token | open |
| ElevenLabs sound effects | generated SFX | paid plan for commercial use; hosted MCP OAuth-only, key MCP archived 2026-08-20 | ruled (9): REST from the runner |
| Pixabay audio; Figma Dev Mode; excalidraw-webmcp@cf735a6 | library SFX; boards from Figma; sketching | commercial OK; Pro plan plus Dev seat; MIT | not chosen; low; low |

Excluded: Freesound (non-commercial only), the LottieFiles community MCP (licence unverified, no update in 17 months), Higgsfield (blocked by org policy). The wider 2026-10-06 sweep is [[mcp-skill-candidates]].

### Rulings this produced (2026-10-02)

Operator, verbatim: "1. both i can tell it or let it decide. 2. me. 3. keep. 4. eleven labs. 5. swap 6. just let people connect their own." These are rulings 6-11, now rules R6 (story and boards), R7 (vendored skills), R8 (sound), R9 (accent italic), R10 (mcp serve unpublished).

### Open from this research

- Generated stills: none, fal.ai or Replicate. A design question, so the agent's call under ruling 18; nothing keyed is in use yet.
- Whether the brand site also drops Sentient, or the video differs from the site: the operator's call (the brand preset is the operator's file).

## Sources

- Engine `E/skills/` files cited inline; https://github.com/heygen-com/hyperframes
- https://improvencyclopedia.org/games/Story_Spine.html; https://ads.tiktok.com/help/article/creative-best-practices
- https://code.claude.com/docs/en/plugins/marketplace-reference; https://github.com/vercel-labs/skills/issues/2279
- https://modelcontextprotocol.io/registry/about; https://modelcontextprotocol.io/registry/versioning; https://www.upguard.com/blog/mcp-security-incidents

## Date

Researched 2026-10-02; rulings 6-11 the same day. Folded from the former `arch/preproduction-plan.md` on 2026-10-06.
