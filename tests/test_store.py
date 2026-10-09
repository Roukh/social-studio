"""The reference store (F15, J40 and J44): one JSON file per item, checked against a tag vocabulary, built into
SQLite with facet rows and FTS5, ranked per story beat, and runnable on its own inside a session."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from social_studio import store

TAGS = {"role": ["hook"], "purpose": ["tease"], "content": ["type"], "energy": ["punch"], "format": ["9:16"],
        "family": ["type"], "complexity": "low"}


def technique(iid: str, **tags) -> dict:
    return {"id": iid, "kind": "technique", "name": iid.replace("-", " "), "looks": "a look", "build": "a build",
            "sound": "", "duration": [1.5, 2.5], "prompt": f"build {iid} for any brand", "source": "a film",
            "tags": {**TAGS, **tags}}


def scene(iid: str, uses: list[str], **tags) -> dict:
    return {"id": iid, "kind": "scene", "name": iid, "looks": "cards fan out", "build": "gsap stagger",
            "sound": "", "duration": [2, 3], "prompt": f"a {iid} shot", "techniques": uses,
            "source": {"film": "f", "url": "https://example.com/f", "creator": "@c", "start": 1.0, "end": 3.0},
            "tags": {**TAGS, **tags}}


def story_item(iid: str, **tags) -> dict:
    return {"id": iid, "kind": "story", "name": iid, "brand": "Acme", "object": "an audio API",
            "message": "This video tells developers that voices take one call.", "cta": "Try it free",
            "why": "it shows the product working", "source": {"url": "https://example.com/p", "platform": "x"},
            "moments": [{"role": "hook", "what": "a voice speaks"}, {"role": "cta", "what": "the logo"}],
            "tags": {"goal": ["launch"], "product": ["api"], "structure": ["hook-demo-cta"], "voice": ["narration"],
                     "format": ["9:16"], **tags}}


def write(root: Path, *items: dict) -> None:
    for item in items:
        d = root / store.FOLDERS[item["kind"]]
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{item['id']}.json").write_text(json.dumps(item))


@pytest.fixture
def root(tmp_path) -> Path:
    """A small store; technique ids are real ones, since a technique needs its recipe in the technique library."""
    r = tmp_path / "store"
    r.mkdir()
    shutil.copy2(store.STORE_DIR / "facets.json", r / "facets.json")
    write(r,
          technique("kinetic-word-run"),
          technique("glass-ui-flow", role=["demo", "solution"], purpose=["show-ease", "reveal-product"],
                    content=["product-ui"], energy=["build"], family=["interface"]),
          technique("grain-vignette", role=["whole-film"], purpose=["set-mood"], content=["abstract"],
                    energy=["calm"], family=["texture"]),
          scene("cards-demo", ["glass-ui-flow"], role=["demo"], purpose=["reveal-product"], content=["product-ui"],
                energy=["build"], family=["interface"]),
          scene("word-slam-hook", ["kinetic-word-run"]),
          story_item("acme-voice-launch"),
          story_item("acme-shop-proof", goal=["proof"], product=["commerce"], format=["16:9"]))
    return r


def con_for(root: Path):
    items = store.load(root)
    assert store.problems(items, store.vocab(root)) == []
    return store.build(items)


def test_the_shipped_store_passes_its_own_check():
    items = store.load()
    assert store.problems(items, store.vocab()) == []
    assert {i["kind"] for i in items} >= {"technique"}


def test_check_lists_every_problem_by_file(root):
    bad = technique("glass-ui-flow", purpose=["vibes"])
    bad["prompt"] = "x" * (store.PROMPT_MAX + 1)
    write(root, bad, scene("orphan", ["no-such-technique"]), {**story_item("thin"), "moments": [{"role": "drama"}]})
    (root / "scenes" / "misfiled.json").write_text(json.dumps(scene("other-id", ["glass-ui-flow"])))
    found = "\n".join(store.problems(store.load(root), store.vocab(root)))
    assert "glass-ui-flow.json: tags.purpose value 'vibes' is not in facets.json" in found
    assert "prompt is over" in found
    assert "orphan.json: technique 'no-such-technique' is not in the store" in found
    assert "thin.json: moments must list" in found or "moment 1 needs a role" in found
    assert "misfiled.json: a scene with id 'other-id' belongs in scenes/other-id.json" in found


def test_a_technique_needs_its_recipe(root):
    write(root, technique("no-recipe-here"))
    found = store.problems(store.load(root), store.vocab(root))
    assert any("no recipe at skills/technique-library/techniques/no-recipe-here.md" in p for p in found)


def test_rank_scores_facets_and_text_and_says_why(root):
    con = con_for(root)
    rows = store.rank(con, role="demo", purpose=["reveal-product"], content=["product-ui"], energy="build",
                      fmt="9:16", text="cards fan out")
    assert rows[0]["id"] == "cards-demo"                     # role 3 + purpose 2 + content 1.5 + energy 1 + format 1 + text
    assert "role demo" in rows[0]["matched"] and "text" in rows[0]["matched"]
    assert [r["id"] for r in rows if r["kind"] == "story"] == []          # stories never compete with techniques


def test_for_beats_gives_each_beat_its_own_items_and_skips_recent_sets(root):
    con = con_for(root)
    beats = [{"role": "hook", "purpose": ["tease"], "content": ["type"], "energy": "punch", "job": "a claim"},
             {"role": "demo", "purpose": ["reveal-product"], "content": ["product-ui"], "energy": "build"}]
    plan = store.for_beats(con, beats, "9:16")
    hook, demo = ([c["id"] for c in b["candidates"]] for b in plan["beats"])
    assert hook[0] in ("kinetic-word-run", "word-slam-hook") and demo[0] == "cards-demo"
    assert not set(hook) & set(demo)                                      # an item serves one beat only
    assert [c["id"] for c in plan["film"]] == ["grain-vignette"]
    assert plan["beats"][1]["candidates"][0]["techniques"] == ["glass-ui-flow"]
    write(root, scene("fresh-demo", ["kinetic-word-run"], role=["demo"], purpose=["reveal-product"],
                      content=["product-ui"], energy=["build"], family=["interface"]))
    con = con_for(root)
    first = lambda recent: store.for_beats(con, beats[1:], "9:16", recent)["beats"][0]["candidates"][0]["id"]
    assert first(set()) == "cards-demo"                                   # a tie goes to the id
    assert first({"glass-ui-flow"}) == "fresh-demo"                       # a recent film's technique drops 2 points


def test_stories_rank_by_goal_product_and_text(root):
    con = con_for(root)
    got = store.stories_for(con, "an online shop", "16:9", goal=["proof"], product=["commerce"])
    assert [s["id"] for s in got] == ["acme-shop-proof", "acme-voice-launch"]
    assert store.stories_for(con, "", limit=1)[0]["kind"] == "story"


def test_free_text_never_reaches_fts_as_syntax(root):
    con = con_for(root)
    for text in ('"unbalanced', "a AND OR NOT (", "col:umn*", "", "the and for"):
        store.rank(con, role="hook", text=text)
        store.search(con, text)
    assert store.fts_query('cards "fan" NEAR motion-graphics, the') == '"cards" OR "fan" OR "near" OR "motion" OR "graphics"'


def test_search_filters_by_facet_and_kind(root):
    con = con_for(root)
    assert [r["id"] for r in store.search(con, kind="scene", facets={"role": "demo"})] == ["cards-demo"]
    assert store.search(con, "fan", kind="technique") == []
    assert store.stats(con)["items"] == {"technique": 3, "scene": 2, "story": 2}


def test_the_session_copy_runs_on_its_own(root, tmp_path):
    session = tmp_path / "work"
    (session / "tools").mkdir(parents=True)
    shutil.copy2(store.HERE / "store.py", session / "tools" / "store.py")
    store.save(con_for(root), session / "store.db")
    run = lambda *a: subprocess.run([sys.executable, "tools/store.py", "--db", "store.db", *a], cwd=session,
                                    capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    out = run("search", "cards", "--tag", "role=demo")
    assert out.returncode == 0 and "cards-demo  [scene]" in out.stdout, out.stderr
    shown = run("show", "acme-voice-launch")
    assert json.loads(shown.stdout)["brand"] == "Acme"
    assert run("show", "nope").returncode == 1
