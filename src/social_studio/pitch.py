"""The pitch round: with no operator brief, the story stage opens with five pitched concepts and a judge (F15, J6;
rule R6, ruling 6).

The pitcher runs in the build's own sandbox and session folder, before the storyteller. It follows the engine's
pitch-round method (four grounding questions, five concepts on five paths, at least two below p = 0.10, a silhouette
check, the typical direction left behind; see skills/pitch-round/NOTICE.md) and writes pitches.json, which code checks.
The judge is a fresh session in its own folder inside the session (`<session>/judge/`, its own home and work), so it
sees only the pitches and the brief: never the pitcher's grounding, probabilities or transcript. It scores every pitch
on one rubric (after the operator's design-tournament skill); code checks the verdict the way review.check_verdict
does and picks the winner from the scores. The storyteller then writes story.json from the winning concept.
"""
from __future__ import annotations

import json
import random
import shutil

from .core import PKG_DIR, Ctx, DataError, Preset, log
from .runner import (PITCH_SKILL, TIMEOUT_MIN, Backend, Session, _brief_block, _fill, _maker_values, _read_json,
                     backend_command, remove_within, run_jailed)

TASK = "PITCH.md"
PITCHES = "pitches.json"
VERDICT = "pitch-verdict.json"          # the checked verdict, kept in the session and the library
JUDGE_TASK = "JUDGE.md"
BRIEF_KEYS = ("content.title", "content.subject", "content.topic", "content.notes")  # what an operator brief sets
GROUNDING = ("subject", "emotion", "surface", "everyone_else")  # the four grounding questions
PATHS = ("subject", "emotion", "audience", "anti-pattern", "format")  # one concept from each
FIELDS = ("concept", "world", "hook", "truth", "silhouette")
SHOWN = ("concept", "world", "hook", "truth")  # all the judge sees of a pitch
TAIL_P, TAIL_MIN = 0.10, 2
# The shared rubric: criterion -> (what a 10 looks like, what a 1 looks like).
RUBRIC = {
    "product truth": ("the film shows a concrete product truth from the brief working: a feature, the offer, a "
                      "number the brand gives", "an abstract mood or value with nothing of the product to show"),
    "clarity": ("a viewer on a phone, sound off, knows what is offered within 3 s", "the point is still unclear at "
                "the end"),
    "hook": ("the first second stops a thumb: a claim, a pain, the product in motion", "an empty field or a logo "
             "fading up"),
    "distinctiveness": ("nothing like the usual video on this subject", "the median: what any model would make from "
                        "this brief"),
    "brand fit": ("the brand's own words, rules and offer; nothing invented", "breaks a brand rule, or invents a "
                  "client, a result or a number"),
    "buildable": ("HTML motion graphics build it well inside the runtime, with the brand's fonts and assets",
                  "needs footage, people or more seconds than the film has"),
}
TRUTH = "product truth"
TRUTH_FLOOR = 5  # a pitch below this on product truth cannot win: the film that lost had nothing to sell (M27)


def operator_brief(p: Preset) -> bool:
    return any(str(p.get(k) or "").strip() for k in BRIEF_KEYS)


def needed(p: Preset) -> bool:
    """A pitch round runs when the operator gave no brief, unless the preset turns it off (story.pitch)."""
    return bool(p.get("story.pitch", True)) and not operator_brief(p)


def _voice_line(p: Preset) -> str:
    voiced = "voice" in str(p.get("video.sound") or "")
    return "\nThis film is voiced." if voiced else "\nThis film has no voice-over: every idea is on screen."


def task_text(p: Preset, pillar: str | None) -> str:
    vals = {**_maker_values(p), "brief_block": _brief_block(p, pillar, None), "voice_line": _voice_line(p),
            "paths": ", ".join(PATHS), "tail_min": TAIL_MIN, "tail_p": f"{TAIL_P:.2f}"}
    return _fill((PKG_DIR / "data" / "pitch_prompt.md").read_text(), vals)


def _filled(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_pitches(raw: dict) -> dict:
    """pitches.json checked in Python before the judge sees it. Every problem is listed; any fails the build."""
    problems = []
    grounding = raw.get("grounding") if isinstance(raw.get("grounding"), dict) else {}
    problems += [f"grounding.{q} is not answered" for q in GROUNDING if not _filled(grounding.get(q))]
    concepts = raw.get("concepts") if isinstance(raw.get("concepts"), list) else []
    if len(concepts) != len(PATHS):
        problems.append(f"concepts must list exactly {len(PATHS)} pitches, not {len(concepts)}")
    ids, paths, shapes, tail = [], [], {}, 0
    for i, c in enumerate(concepts, 1):
        if not isinstance(c, dict):
            problems.append(f"pitch {i} is not an object")
            continue
        cid = str(c.get("id") or "").strip()
        if not cid or cid in ids:
            problems.append(f"pitch {i} needs an id of its own")
        ids.append(cid)
        if c.get("path") not in PATHS:
            problems.append(f"pitch {i} path {c.get('path')!r} is not one of {', '.join(PATHS)}")
        paths.append(c.get("path"))
        problems += [f"pitch {i} has no {f}" for f in FIELDS if not _filled(c.get(f))]
        pv = c.get("p")
        if isinstance(pv, bool) or not isinstance(pv, (int, float)) or not 0 <= pv <= 1:
            problems.append(f"pitch {i} p must be a number from 0 to 1")
        elif pv < TAIL_P:
            tail += 1
        shape = " ".join(str(c.get("silhouette", "")).lower().split())
        if shape in shapes:
            problems.append(f"pitches {shapes[shape]} and {i} share a silhouette: they are one concept")
        elif shape:
            shapes[shape] = i
    if concepts and len({x for x in paths if x in PATHS}) < len(PATHS):
        problems.append(f"the five pitches must take the five paths ({', '.join(PATHS)}), one each")
    if concepts and tail < TAIL_MIN:
        problems.append(f"{tail} pitches sit below p = {TAIL_P:.2f}; at least {TAIL_MIN} must (the tail constraint)")
    if not _filled(raw.get("left_behind")):
        problems.append("left_behind (the most typical direction, deliberately not pitched) is missing")
    if problems:
        raise DataError(f"{PITCHES} failed its check: " + "; ".join(problems), "see the pitcher's log")
    return raw


def for_judge(concepts: list[dict], seed: str) -> tuple[list[dict], dict[str, str]]:
    """What the judge sees: each pitch's own words under a letter, in a shuffled order so the pitcher's order (one
    path after another) cannot steer the scores. Returns the pitches and the letter -> pitch id map."""
    order = random.Random(seed).sample(concepts, len(concepts))
    letters = [chr(ord("A") + i) for i in range(len(order))]
    return ([{"id": x, **{f: c[f] for f in SHOWN}} for x, c in zip(letters, order)],
            {x: str(c["id"]).strip() for x, c in zip(letters, order)})


def _rubric_lines() -> str:
    return "\n".join(f"- **{c}**: 10 = {hi}; 1 = {lo}." for c, (hi, lo) in RUBRIC.items())


def judge_text(p: Preset, pillar: str | None, ids: list[str]) -> str:
    """The judge's JUDGE.md: the brief (the brand, this film, its format and rules) and the rubric."""
    brand = [f"- {label}: {p.get(k)}" for k, label in (("brand.name", "Brand"), ("brand.tagline", "Tagline"),
                                                       ("preset.description", "What it is")) if p.get(k)]
    vals = _maker_values(p)
    brief = "\n".join([*brand, _brief_block(p, pillar, None),
                       f"- Format: {vals['width']}×{vals['height']} ({vals['aspect']}), {vals['min_s']} to "
                       f"{vals['max_s']} seconds.{_voice_line(p).replace(chr(10), ' ')}",
                       "- The brand's rules:", vals["rules"]])
    example = {i: {c: 0 for c in RUBRIC} for i in ids}
    return _fill((PKG_DIR / "data" / "judge_prompt.md").read_text(),
                 {"count": len(ids), "brief": brief, "rubric": _rubric_lines(),
                  "scores_example": json.dumps(example), "truth_floor": TRUTH_FLOOR, "truth": TRUTH})


def check_verdict(raw: dict, ids: list[str]) -> dict:
    """The judge's verdict checked in Python: every pitch scored on every criterion with a whole number from 1 to 10,
    a pick among the ids and a reason. Code, not the judge, then picks the winner from the scores: the highest total
    among pitches that reach TRUTH_FLOOR on product truth, ties going to product truth, then distinctiveness, then
    the judge's own pick. A malformed verdict, or one where no pitch rests on a product truth, fails the build."""
    problems = []
    scores = raw.get("scores") if isinstance(raw.get("scores"), dict) else {}
    if not isinstance(raw.get("scores"), dict):
        problems.append("scores is not an object")
    for cid in ids:
        row = scores.get(cid)
        if not isinstance(row, dict):
            problems.append(f"pitch {cid} is not scored")
            continue
        for c in RUBRIC:
            v = row.get(c)
            if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 10:
                problems.append(f"pitch {cid} {c!r} is scored {v!r}, not a whole number from 1 to 10")
        problems += [f"pitch {cid}: {k!r} is not a criterion" for k in row if k not in RUBRIC]
    problems += [f"{k!r} is not a pitch" for k in scores if k not in ids]
    if raw.get("pick") not in ids:
        problems.append(f"pick {raw.get('pick')!r} is not one of {', '.join(ids)}")
    if not _filled(raw.get("why")):
        problems.append("why is missing")
    if problems:
        raise DataError("the pitch verdict failed its check: " + "; ".join(problems), "see the judge's log")
    totals = {cid: sum(scores[cid].values()) for cid in ids}
    eligible = [cid for cid in ids if scores[cid][TRUTH] >= TRUTH_FLOOR]
    if not eligible:
        raise DataError(f"no pitch scored {TRUTH_FLOOR} or more on {TRUTH}: every concept was an abstract mood",
                        "run the build again, or give it a brief with --topic or --notes")
    winner = max(eligible, key=lambda c: (totals[c], scores[c][TRUTH], scores[c]["distinctiveness"],
                                          c == raw["pick"]))
    out = {"scores": {cid: {c: scores[cid][c] for c in RUBRIC} for cid in ids}, "totals": totals,
           "winner": winner, "pick": raw["pick"], "why": raw["why"].strip()}
    if isinstance(raw.get("notes"), dict):
        out["notes"] = {k: str(v) for k, v in raw["notes"].items() if k in ids}
    if winner != raw["pick"]:
        out["checked"] = {"judge_said": raw["pick"], "by_scores": winner}
    return out


def concept_block(result: dict) -> str:
    """The winning concept as the storyteller's STORY.md states it."""
    c = result["winner"]
    return ("\n\nThe concept for this film, picked by a pitch round from five (`pitches.json`, `pitch-verdict.json`). "
            "Build the story from it; do not start another idea:\n"
            f"- Concept: {c['concept']}\n- Visual world: {c['world']}\n- Opening: {c['hook']}\n"
            f"- The product truth it rests on: {c['truth']}\n"
            f"- Left behind on purpose (do not drift back to it): {result['left_behind']}")


def _limit(p: Preset, role: str) -> int:
    return int(p.get(f"{role}.timeout_min", TIMEOUT_MIN[role])) * 60


def _pitch(ctx: Ctx, p: Preset, s: Session, b: Backend, version: str, pillar: str | None) -> dict:
    """The pitcher, in the build's own folder: PITCH.md and the method in, pitches.json out and checked."""
    shutil.copytree(PKG_DIR / "data" / "skills" / PITCH_SKILL, s.work / "skills" / PITCH_SKILL, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns(".*"))
    (s.work / TASK).write_text(task_text(p, pillar))
    prompt = (f"Read {TASK} in the current folder and complete it. Work autonomously; nobody will answer questions. "
              f"Finish by writing {PITCHES}.")
    argv, env, ro, rw = backend_command(ctx, p, b, s, prompt, [PITCH_SKILL], role="pitch")
    log(f"[{s.id}] pitch round: pitcher working")
    code = run_jailed(ctx, s, argv, env, ro, rw, b.sandbox, version, "pitch", _limit(p, "pitch"))
    try:
        return check_pitches(_read_json(s.work / PITCHES, PITCHES))
    except DataError as e:
        raise DataError(f"{e} (pitcher exit {code})", e.hint) from e


def _judge(ctx: Ctx, p: Preset, s: Session, b: Backend, version: str, pillar: str | None, pitches: dict) -> dict:
    """The judge, in `<session>/judge/` with its own home and work: the brief and the pitches' own words, nothing
    of the pitcher's. Its logs join the build's; the folder goes once the verdict is read."""
    judge = Session(f"{s.id}-judge", s.dir / "judge")
    for d in (judge.home, judge.work, judge.logs):
        d.mkdir(parents=True, exist_ok=True)
    shown, letters = for_judge(pitches["concepts"], s.id)
    (judge.work / PITCHES).write_text(json.dumps(shown, indent=2))
    shutil.copy2(s.work / "preset.json", judge.work / "preset.json")
    (judge.work / JUDGE_TASK).write_text(judge_text(p, pillar, list(letters)))
    prompt = f"Read {JUDGE_TASK} in the current folder and complete it. Nobody will answer questions."
    try:
        argv, env, ro, rw = backend_command(ctx, p, b, judge, prompt, [], role="judge")
        log(f"[{s.id}] pitch round: judge scoring")
        code = run_jailed(ctx, judge, argv, env, ro, rw, b.sandbox, version, "judge", _limit(p, "judge"))
        try:
            verdict = check_verdict(_read_json(judge.work / "verdict.json", "verdict.json"), list(letters))
        except DataError as e:
            raise DataError(f"{e} (judge exit {code})", e.hint) from e
    finally:
        for f in judge.logs.iterdir():
            shutil.move(str(f), str(s.logs / f.name))
        remove_within(judge.dir, s.dir)
    return {**verdict, "letters": letters, "shown": shown}


def run(ctx: Ctx, p: Preset, s: Session, b: Backend, version: str, pillar: str | None) -> dict:
    """The whole round: pitches, the judge's checked verdict, and the winning concept. The pitcher's file and the
    verdict stay in the session (and go to the library with the video); the winner and the direction left behind
    go into the video's meta."""
    pitches = _pitch(ctx, p, s, b, version, pillar)
    verdict = _judge(ctx, p, s, b, version, pillar, pitches)
    by_id = {str(c["id"]).strip(): c for c in pitches["concepts"]}
    winner = by_id[verdict["letters"][verdict["winner"]]]
    (s.work / VERDICT).write_text(json.dumps(verdict, indent=2))
    log(f"[{s.id}] pitch round: {winner['id']} ({winner['path']}) wins, {verdict['totals'][verdict['winner']]} "
        f"points: {winner['concept']}")
    meta = {"winner": winner["id"], "path": winner["path"], "concept": winner["concept"],
            "truth": winner["truth"], "left_behind": pitches["left_behind"].strip(),
            "points": verdict["totals"][verdict["winner"]]}
    return {"winner": winner, "left_behind": pitches["left_behind"].strip(), "verdict": verdict, "meta": meta}
