"""The storyteller: the first of a build's two sessions (operator, 2026-10-08 and 2026-10-09; F15).

A build tells its story before anyone designs motion. The storyteller runs in the same sandbox and session folder
as the designer, just before it: it states the film's point in one line, studies the brand posts the store
retrieves for this brand (story references), and writes story.json, beats with no motion graphics. Code then checks
the story, retrieves the top technique items for each beat from the store (store.for_beats), and writes the
designer's brief: what each beat must make the viewer understand and feel, its candidate techniques and why, and
the looks banned for this film. The designer session follows with no operator step between.

With no operator brief (no title, subject, topic or notes), a pitch round runs before the storyteller (pitch.py, J6):
five concepts, a judge, and the winner handed to the storyteller in STORY.md.
"""
from __future__ import annotations

import json
import shutil

from . import pitch, store
from .core import PKG_DIR, Ctx, DataError, Preset, log
from .runner import (STORY_SKILL, TIMEOUT_MIN, Backend, Session, _aspect, _brief_block, _fill, _maker_values,
                     _read_json, backend_command, run_jailed)

TASK = "STORY.md"
REFERENCES = "story-references.json"
STORY = "story.json"
TECHNIQUES = "techniques.json"
STORY_SKILLS = [STORY_SKILL, "launch-video"]  # the method, and the vendored launch arc it builds on
BEAT_ROLES = tuple(r for r in store.ROLES if r != "transition")
ALWAYS_BANNED = ["crossfades", "template glass-kit UI cards"]  # rule R41: every brief bans these up front
SECONDS_SLACK = 0.5


def _voiced(p: Preset) -> bool:
    return "voice" in str(p.get("video.sound") or "")


def _brand_text(p: Preset, pillar: str | None) -> str:
    """What the store's story references are ranked against: the brand, its offer and this film's pillar."""
    idea = next((x.get("idea", "") for x in p.get("content.pillars", []) if isinstance(x, dict)
                 and x.get("name") == pillar), "")
    parts = [p.get("brand.name"), p.get("brand.tagline"), p.get("preset.description"), idea, p.get("content.subject"),
             p.get("content.topic"), p.get("content.notes"), p.get("content.cta")]
    return " ".join(str(x) for x in parts if x)


def prepare(p: Preset, s: Session, pillar: str | None, con) -> list[dict]:
    """STORY.md, the story references and the storyteller's skill, into the session's work folder."""
    refs = store.stories_for(con, _brand_text(p, pillar), _aspect(p.get("video.width"), p.get("video.height")),
                             goal=p.get("story.goal", []), product=p.get("story.product", []))
    (s.work / REFERENCES).write_text(json.dumps(refs, indent=2))
    shutil.copytree(PKG_DIR / "data" / "skills" / STORY_SKILL, s.work / "skills" / STORY_SKILL, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".*"))
    write_task(p, s, pillar, refs)
    return refs


def write_task(p: Preset, s: Session, pillar: str | None, refs: list[dict], concept: str = "") -> None:
    """STORY.md; after a pitch round it carries the winning concept (pitch.concept_block)."""
    voc = store.vocab()["technique"]
    vals = {**_maker_values(p), "brief_block": _brief_block(p, pillar, None) + concept,
            "references_line": (f"{len(refs)} analysed posts" if refs else "none yet: work from the method alone"),
            "voice_line": ("\nThis film is voiced: every beat gets a voice line, and the voice sets the timing "
                           "(about 2.5 spoken words a second)." if _voiced(p) else "\nThis film has no voice-over: "
                           "every idea is on screen."),
            "roles": ", ".join(BEAT_ROLES), "purposes": ", ".join(voc["purpose"]),
            "contents": ", ".join(voc["content"]), "energies": " | ".join(voc["energy"]),
            "structures": ", ".join(store.vocab()["story"]["structure"]),
            "always_banned": json.dumps(ALWAYS_BANNED)}
    (s.work / TASK).write_text(_fill((PKG_DIR / "data" / "story_prompt.md").read_text(), vals))


def check(raw: dict, p: Preset, ref_ids: set[str]) -> dict:
    """story.json checked in Python before the designer trusts it. Shape problems fail the build with every problem
    listed; tag values outside the vocabulary are dropped (they only steer retrieval) and recorded."""
    problems, dropped = [], []
    lo, hi = (float(x) for x in p.get("video.duration"))
    if not str(raw.get("idea", "")).strip():
        problems.append("idea is missing")
    beats = raw.get("beats")
    if not isinstance(beats, list) or not 2 <= len(beats) <= 8:
        problems.append("beats must list 2 to 8 beats")
        beats = []
    voc = store.vocab()["technique"]
    clean = []
    for i, b in enumerate(beats, 1):
        if not isinstance(b, dict):
            problems.append(f"beat {i} is not an object")
            continue
        sec = b.get("seconds")
        if b.get("role") not in BEAT_ROLES:
            problems.append(f"beat {i} role {b.get('role')!r} is not one of {', '.join(BEAT_ROLES)}")
        if isinstance(sec, bool) or not isinstance(sec, (int, float)) or sec <= 0:
            problems.append(f"beat {i} seconds must be a positive number")
        if not str(b.get("job", "")).strip():
            problems.append(f"beat {i} has no job (what the viewer must understand)")
        copy = b.get("copy", [])
        if not isinstance(copy, list) or not all(isinstance(x, str) for x in copy):
            problems.append(f"beat {i} copy must be a list of lines")
        beat = dict(b)
        for facet in ("purpose", "content"):
            vals = b.get(facet, [])
            vals = [vals] if isinstance(vals, str) else vals if isinstance(vals, list) else []
            beat[facet] = [v for v in vals if v in voc[facet]]
            dropped += [f"beat {i} {facet} {v!r}" for v in vals if v not in voc[facet]]
        if b.get("energy") not in voc["energy"]:
            if b.get("energy"):
                dropped.append(f"beat {i} energy {b.get('energy')!r}")
            beat["energy"] = ""
        clean.append(beat)
    total = sum(b["seconds"] for b in clean if isinstance(b.get("seconds"), (int, float)))
    if clean and not lo - SECONDS_SLACK <= total <= hi + SECONDS_SLACK:
        problems.append(f"the beats run {total:g} s; the film runs {lo:g} to {hi:g} s")
    refs = raw.get("references", [])
    cited = [r.get("id") for r in refs if isinstance(r, dict)] if isinstance(refs, list) else []
    problems += [f"reference {r!r} is not in {REFERENCES}" for r in cited if r not in ref_ids]
    if ref_ids and not cited:
        problems.append(f"references must name the posts from {REFERENCES} the story learns from")
    if problems:
        raise DataError("story.json failed its check: " + "; ".join(problems), "see the storyteller's log")
    banned = [str(x) for x in raw.get("banned", []) if str(x).strip()] if isinstance(raw.get("banned"), list) else []
    banned += [x for x in ALWAYS_BANNED if not any(x.split()[0] in b.lower() for b in banned)]
    return {**raw, "beats": clean, "banned": banned, "seconds": round(total, 2), "dropped": dropped}


def _span(beats: list[dict]) -> list[tuple[float, float]]:
    out, t = [], 0.0
    for b in beats:
        out.append((round(t, 2), round(t + float(b["seconds"]), 2)))
        t += float(b["seconds"])
    return out


def designer_brief(story: dict, plan: dict, refs: list[dict], voiced: bool) -> str:
    """The video's brief for the designer's TASK.md: the story beat by beat with the store's candidates."""
    names = {r["id"]: f"{r.get('brand', '')}: {r.get('name', '')}" for r in refs}
    lines = [f"- The story, written by the storyteller before you (`story.json`, binding): **{story['idea']}**"]
    for key, label in (("title", "Working title"), ("pillar", "Pillar"), ("topic", "Topic"), ("angle", "Angle")):
        if str(story.get(key, "")).strip():
            lines.append(f"- {label}: {story[key]}")
    learned = [f"{names.get(r['id'], r['id'])} ({r.get('took', '')})" for r in story.get("references", [])
               if isinstance(r, dict)]
    if story.get("structure") or learned:
        lines.append(f"- Structure: {story.get('structure', 'as the beats run')}."
                     + (f" Learned from: {'; '.join(learned)}." if learned else ""))
    if voiced:
        lines.append("- This film is voiced: the voice lines set the timing. Cut the picture to the voice, not to a "
                     "fixed beat grid, and keep every spoken idea on screen too.")
    lines.append("\nThe beats, in order:\n")
    for (start, end), b, slot in zip(_span(story["beats"]), story["beats"], plan["beats"]):
        lines.append(f"{slot['beat']}. **{b['role']}**, {start:g}-{end:g} s. The viewer must understand: {b['job']}"
                     + (f" They should feel: {b['emotion']}." if b.get("emotion") else "")
                     + (f" On screen: {b['shows']}." if b.get("shows") else ""))
        if b.get("copy"):
            lines.append("   - Copy, exactly: " + " / ".join(f"\"{c}\"" for c in b["copy"]))
        if b.get("voice"):
            lines.append(f"   - Voice: \"{b['voice']}\"")
        for c in slot["candidates"]:
            kind = "scene" if c["kind"] == "scene" else "technique"
            uses = f" Uses: {', '.join(c['techniques'])}." if c.get("techniques") else ""
            lines.append(f"   - Candidate {kind} `{c['id']}` ({c['why']}): {c['prompt']}{uses}")
    if plan.get("film"):
        lines.append("\nThrough the whole film, candidates: " + "; ".join(
            f"`{c['id']}` ({c['prompt']})" for c in plan["film"]))
    lines.append(f"\nBanned for this film: {'; '.join(story['banned'])}.")
    if story.get("cta"):
        lines.append(f"The call to action: \"{story['cta']}\".")
    return "\n".join(lines)


def tell(ctx: Ctx, p: Preset, s: Session, b: Backend, version: str, history: list[dict], pillar: str | None) -> dict:
    """Run the storyteller, check its story, retrieve each beat's techniques, and return the designer brief."""
    con = store.open_store()
    try:
        return _tell(ctx, p, s, b, version, history, pillar, con)
    finally:
        con.close()


def _tell(ctx: Ctx, p: Preset, s: Session, b: Backend, version: str, history: list[dict], pillar: str | None,
          con) -> dict:
    refs = prepare(p, s, pillar, con)
    pitched = pitch.run(ctx, p, s, b, version, pillar) if pitch.needed(p) else None
    if pitched:
        write_task(p, s, pillar, refs, pitch.concept_block(pitched))
    prompt = (f"Read {TASK} in the current folder and complete it. Work autonomously; nobody will answer questions. "
              f"Finish by writing {STORY}.")
    argv, env, ro, rw = backend_command(ctx, p, b, s, prompt, STORY_SKILLS, role="story")
    log(f"[{s.id}] storyteller {b.name}{':' + b.model if b.model else ''} working")
    code = run_jailed(ctx, s, argv, env, ro, rw, b.sandbox, version, "story",
                      int(p.get("story.timeout_min", TIMEOUT_MIN["story"])) * 60)
    raw = _read_json(s.work / STORY, STORY)
    try:
        told = check(raw, p, {r["id"] for r in refs})
    except DataError as e:
        raise DataError(f"{e} (storyteller exit {code})", e.hint) from e
    (s.work / STORY).write_text(json.dumps({k: v for k, v in told.items() if k != "dropped"}, indent=2))
    recent = {t for h in history[:5] for t in h.get("techniques", [])}
    fmt = _aspect(p.get("video.width"), p.get("video.height"))
    plan = store.for_beats(con, told["beats"], fmt, recent, film_text=f"{told['idea']} {p.get('brand.name', '')}")
    (s.work / TECHNIQUES).write_text(json.dumps(plan, indent=2))
    if told["dropped"]:
        log(f"[{s.id}] story tags outside the vocabulary, dropped: {', '.join(told['dropped'])}")
    meta = {"idea": told["idea"], "structure": told.get("structure", ""), "seconds": told["seconds"],
            "beats": [x["role"] for x in told["beats"]],
            "references": [r.get("id") for r in told.get("references", []) if isinstance(r, dict)]}
    if pitched:
        meta["pitch"] = pitched["meta"]
    return {"story": told, "plan": plan, "meta": meta,
            "brief": designer_brief(told, plan, refs, _voiced(p))}
