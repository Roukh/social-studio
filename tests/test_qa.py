"""Report-only quality gates (motion-quality-plan G1). The math and rule tests below need no engine. The
calibration tests at the bottom render the fixtures under tests/fixtures/qa/ with the real engine and its
pinned Chrome, through `qa.check`, and are skipped unless that engine is installed (test_integration's
READY pattern): borrow it from SOCIAL_STUDIO_PROJECT or the current project."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from social_studio import engine, qa
from social_studio.core import PROJECT_FILE, Preset, dump_toml, make_ctx

VERSION = "0.8.106"
REAL = make_ctx()
READY = (REAL.project is not None and shutil.which("bwrap") and shutil.which("ffmpeg")
         and engine.hf_bin(REAL, VERSION).exists() and shutil.which("node"))

FIXTURES = Path(__file__).parent / "fixtures" / "qa"
SAFE_ZONE = {"top": 0.12, "bottom": 0.25, "left": 0.06, "right": 0.10}  # the example preset's own numbers


def node(text="Sample", x=100.0, y=300.0, w=200.0, h=60.0, size=40.0, weight=400, family="Inter",
        generic=False, color=(0, 0, 0, 1), opacity=1.0, bg=(255, 255, 255, 1)) -> dict:
    """A qa-probe.mjs node, built by hand for the gate-function unit tests below."""
    return {"text": text, "box": {"x": x, "y": y, "w": w, "h": h}, "font_size": size, "font_weight": weight,
            "font_family": family, "font_generic": generic, "color": list(color), "opacity": opacity,
            "bg": list(bg) if bg is not None else None}


# --- WCAG contrast math -------------------------------------------------------------------------------------

def test_contrast_ratio_black_on_white_is_21_to_1():
    assert qa.contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0, abs=0.01)


def test_contrast_ratio_matches_the_known_6b6b6b_on_fafafa_pair():
    assert qa.contrast_ratio((0x6B, 0x6B, 0x6B), (0xFA, 0xFA, 0xFA)) == pytest.approx(5.1, abs=0.05)


def test_contrast_ratio_is_symmetric_in_its_two_colours():
    a, b = (0x22, 0x22, 0x22), (0xEE, 0xEE, 0xEE)
    assert qa.contrast_ratio(a, b) == qa.contrast_ratio(b, a)


# --- settled vs transitional: the contrast gate only ever sees nodes it is handed -----------------------------

def test_contrast_gate_flags_a_real_dip_at_a_settled_time():
    # #808080 on white is ~3.95:1: fails the 4.5:1 normal-text bar.
    findings = qa.check_contrast([node(size=40, weight=400, color=(0x80, 0x80, 0x80, 1))], t=1.0, width=1080)
    assert len(findings) == 1 and findings[0] == {"gate": "contrast", "t": 1.0,
                                                   "detail": "3.95:1 (needs 4.5:1) on 'Sample'"}


def test_contrast_gate_never_sees_a_transitional_dip_it_was_not_handed():
    # qa.check() only ever calls check_contrast with nodes from genuinely settled times (sampler.py's real
    # "settled" holds, never its "calmest" fallback): a caller that (correctly) omits mid-move nodes gets no
    # finding for them, which is how finding 6 (frames mid-wipe reading as contrast failures) is avoided.
    assert qa.check_contrast([], t=0.5, width=1080) == []


def test_large_bold_text_gets_the_3_to_1_threshold_instead_of_4_5():
    # Same ~3.95:1 pair as above, but now 60px bold: large text at 1080px wide (threshold ~51px), so 3.95:1
    # clears the 3:1 bar even though it fails 4.5:1.
    grey = (0x80, 0x80, 0x80, 1)
    assert qa.check_contrast([node(size=60, weight=700, color=grey)], t=1.0, width=1080) == []
    assert qa.check_contrast([node(size=60, weight=400, color=grey)], t=1.0, width=1080) != []


def test_contrast_skips_an_unknown_background_instead_of_flagging_it():
    # A background-image/gradient makes the real background unknowable (qa-probe.mjs reports `bg: null`):
    # that is "skipped", never a finding.
    assert qa.check_contrast([node(bg=None)], t=1.0, width=1080) == []


# --- min_px: Apple HIG's 11pt, scaled to this frame -----------------------------------------------------------

def test_min_text_px_matches_the_known_30px_at_1080_wide():
    assert qa.min_text_px(1080) == 30  # round(11 * 1080 / 393)


def test_min_px_gate_flags_text_under_the_floor_only():
    nodes = [node(text="small", size=26), node(text="big enough", size=30), node(text="smaller", size=18)]
    findings = qa.check_min_px(nodes, t=1.0, width=1080)
    assert {f["detail"].split(" ")[0] for f in findings} == {"26px", "18px"}
    assert all(f["gate"] == "min_px" for f in findings)


# --- overlap geometry ------------------------------------------------------------------------------------------

def test_overlap_gate_flags_intersecting_boxes():
    a = node(text="ALPHA", x=200, y=700, w=240, h=80)
    b = node(text="BETA", x=260, y=730, w=185, h=80)
    findings = qa.check_overlap([a, b], t=0.5)
    assert len(findings) == 1 and findings[0]["gate"] == "overlap"


def test_overlap_gate_ignores_touching_or_separate_boxes():
    a = node(text="LEFT", x=0, y=0, w=100, h=100)
    b = node(text="RIGHT", x=100, y=0, w=100, h=100)  # edges touch, zero shared area
    assert qa.check_overlap([a, b], t=0.5) == []
    c = node(text="FAR", x=500, y=500, w=50, h=50)
    assert qa.check_overlap([a, c], t=0.5) == []


def test_overlap_gate_ignores_a_word_inside_its_own_line():
    # "Say <span>one</span> thing.": the line's own text spans the word between its halves (old benchmark video 1)
    line = {**node(text="Say one thing.", x=90, y=700, w=700, h=90), "id": 0, "parents": []}
    word = {**node(text="one", x=250, y=700, w=160, h=90), "id": 1, "parents": [0]}
    other = {**node(text="ELSEWHERE", x=300, y=720, w=200, h=60), "id": 2, "parents": []}
    assert [f["detail"] for f in qa.check_overlap([line, word, other], t=1.0)] == [
        "'Say one thing.' overlaps 'ELSEWHERE'", "'one' overlaps 'ELSEWHERE'"]


def test_overlap_gate_ignores_repeated_text_in_the_same_spot():
    # The same leaf text probed twice (e.g. a duplicate DOM read) is not two blocks colliding.
    a = node(text="ALPHA", x=0, y=0, w=100, h=100)
    b = node(text="ALPHA", x=0, y=0, w=100, h=100)
    assert qa.check_overlap([a, b], t=0.5) == []


# --- safe_zone -------------------------------------------------------------------------------------------------

def test_safe_zone_gate_flags_a_box_outside_the_zone():
    # 1080x1920, safe box is x:[64.8, 972] y:[230.4, 1440]. y=1500 falls below it.
    below = node(text="Below", x=100, y=1500, w=400, h=55)
    findings = qa.check_safe_zone([below], t=0.5, width=1080, height=1920, safe=SAFE_ZONE)
    assert len(findings) == 1 and findings[0]["gate"] == "safe_zone"


def test_safe_zone_gate_passes_a_box_inside_the_zone():
    inside = node(text="Inside", x=100, y=700, w=400, h=55)
    assert qa.check_safe_zone([inside], t=0.5, width=1080, height=1920, safe=SAFE_ZONE) == []


# --- fonts: computed family vs @font-face --------------------------------------------------------------------

def test_declared_font_families_reads_font_face_blocks():
    html = '<style>@font-face { font-family: "Brand Sans"; src: url(x.woff2); }</style>'
    assert qa.declared_font_families(html) == {"brand sans"}


def test_fonts_gate_flags_an_undeclared_family_but_not_a_declared_or_generic_one():
    nodes_by_time = {0.0: [node(family="Georgia", generic=False), node(family="Brand Sans", generic=False),
                            node(family="sans-serif", generic=True)]}
    findings = qa.check_fonts(nodes_by_time, declared={"brand sans"})
    assert len(findings) == 1 and "Georgia" in findings[0]["detail"]


def test_fonts_gate_reports_each_undeclared_family_once():
    nodes_by_time = {0.0: [node(family="Georgia")], 1.0: [node(family="Georgia")]}
    assert len(qa.check_fonts(nodes_by_time, declared=set())) == 1


# --- copy lint -------------------------------------------------------------------------------------------------

def preset(**content) -> Preset:
    return Preset("qa-test", Path("."), {"content": content})


def test_copy_gate_is_word_boundary_aware():
    p = preset(banned=["unlock"])
    assert qa.check_copy(p, ["Unlocked potential"]) == []          # "unlock" is not a whole word here
    findings = qa.check_copy(p, ["unlock your potential"])
    assert len(findings) == 1 and "unlock" in findings[0]["detail"]


def test_copy_gate_is_case_insensitive():
    p = preset(banned=["Game-Changer"])
    assert qa.check_copy(p, ["this is a game-changer"]) != []


def test_copy_gate_exact_line_passes_when_typed_verbatim():
    p = preset(exact_lines={"offer": "Try it free for 14 days."})
    assert qa.check_copy(p, ["Try it free for 14 days."]) == []


def test_copy_gate_exact_line_flags_a_near_miss():
    p = preset(exact_lines={"offer": "Try it free for 14 days."})
    findings = qa.check_copy(p, ["Try it free for 30 days."])
    assert len(findings) == 1 and "offer" in findings[0]["detail"]


def test_copy_gate_exact_line_ignores_unrelated_text():
    p = preset(exact_lines={"offer": "Try it free for 14 days."})
    assert qa.check_copy(p, ["A completely different caption"]) == []


def test_copy_gate_cta_exactness():
    p = preset(cta="Learn more")
    assert qa.check_copy(p, ["Learn more"]) == []
    assert qa.check_copy(p, ["Learn More Now"]) != []
    assert qa.check_copy(p, ["Something else entirely"]) == []


# --- poster window ---------------------------------------------------------------------------------------------

def test_poster_gate_passes_inside_a_settled_hold():
    assert qa.check_poster(1.5, holds_s=[(1.0, 2.0)]) == []


def test_poster_gate_flags_a_poster_inside_a_move():
    findings = qa.check_poster(0.5, holds_s=[(1.0, 2.0)])
    assert len(findings) == 1 and findings[0]["gate"] == "poster"


def test_poster_gate_is_a_no_op_without_a_poster_time():
    assert qa.check_poster(None, holds_s=[(1.0, 2.0)]) == []


# --- audio cue rule ----------------------------------------------------------------------------------------------

def test_audio_gate_flags_cues_with_no_audio_stream():
    brief = {"shots": [{"cue": ""}, {"cue": "soft whoosh"}]}
    findings = qa.check_audio(brief, has_audio=False)
    assert len(findings) == 1 and findings[0]["gate"] == "audio"


def test_audio_gate_passes_when_the_video_has_audio():
    brief = {"shots": [{"cue": "soft whoosh"}]}
    assert qa.check_audio(brief, has_audio=True) == []


def test_audio_gate_is_a_no_op_without_cues_or_a_brief():
    assert qa.check_audio({"shots": [{"cue": ""}]}, has_audio=False) == []
    assert qa.check_audio(None, has_audio=False) == []


# --- frame0 ghost ------------------------------------------------------------------------------------------------

def test_frame0_gate_never_fires_when_text_is_visible():
    assert qa.check_frame0(Path("/does/not/exist.mp4"), nodes_at_0=[node()]) == []


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_frame0_gate_flags_a_blank_first_frame(tmp_path):
    import subprocess
    video = tmp_path / "blank.mp4"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                    "-i", "color=c=white:s=320x240:d=0.5:r=10", str(video)], check=True)
    findings = qa.check_frame0(video, nodes_at_0=[])
    assert len(findings) == 1 and findings[0]["gate"] == "frame0"


# --- calibration: the real engine, rendering tests/fixtures/qa/* --------------------------------------------------

def _ctx(tmp_path, monkeypatch):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    proj = tmp_path / "repo" / "social"
    proj.mkdir()
    (proj / PROJECT_FILE).write_text(dump_toml({"paths": {"library": "library"}}))
    monkeypatch.setenv("SOCIAL_STUDIO_PROJECT", str(proj))
    ctx = make_ctx()
    ctx.engine_dir.mkdir(parents=True)
    (ctx.engine_dir / f"hyperframes-{VERSION}").symlink_to(engine.engine_root(REAL, VERSION))
    ctx.cache_dir.symlink_to(REAL.cache_dir)
    return ctx


def _render_fixture(ctx, name: str, tmp_path) -> tuple[Path, Path]:
    """Copy the fixture, add gsap (the only vendor library it needs, borrowed from the installed engine,
    never committed to the repo), and render it the way runner.run_one renders a finished session."""
    comp = tmp_path / "comp"
    shutil.copytree(FIXTURES / name, comp)
    (comp / "vendor").mkdir(exist_ok=True)
    gsap = engine.engine_root(REAL, VERSION) / "node_modules" / "gsap" / "dist" / "gsap.min.js"
    shutil.copy2(gsap, comp / "vendor" / "gsap.min.js")
    home = tmp_path / "home"
    home.mkdir()
    eng_root = engine.engine_root(ctx, VERSION)
    chrome = engine.chrome_path(ctx, VERSION)
    node_ro, node_path = engine.node_dirs(ctx)
    env = engine.base_env(home, [eng_root / "node_modules" / ".bin", *node_path])
    env["HYPERFRAMES_BROWSER_PATH"] = str(chrome)
    hf = engine.hf_bin(ctx, VERSION)
    video = tmp_path / "master.mp4"
    prefix = engine.bwrap_argv(tmp_path, home, rw=[tmp_path],
                               ro=[eng_root, engine.chrome_root(chrome), *node_ro], env=env)
    engine.render_master(prefix, hf, comp, video, fps=30, crf=18, env=None)
    return comp, video


def _check(ctx, name, tmp_path, poster_at=None, brief=None) -> dict:
    comp, video = _render_fixture(ctx, name, tmp_path)
    p = Preset("qa-fixture", tmp_path, {"video": {"fps": 30, "safe_zone": SAFE_ZONE}, "content": {}})
    return qa.check(ctx, p, comp, video, tmp_path / "qa-work", VERSION, sandbox=True, brief=brief,
                    poster_at=poster_at)


# sequential_clips: two shots in one place, cut from one to the next; the probe hides a clip outside its window, as
# the engine does, so a finished shot never counts as overlapping the next (found on the first real benchmark video)
CALIBRATION_PASS = ("two_line_title", "spatial_entrance", "wipe_over_text", "sequential_clips")
# fixture -> the one gate it must fail, and (loosely) a word that must show up in the finding
CALIBRATION_FAIL = {
    "purple_on_purple": ("contrast", "1.0"),
    "small_label_pill": ("min_px", "26px"),
    "offscreen_text": ("safe_zone", "safe zone"),
    "overlap_blocks": ("overlap", "overlaps"),
    "georgia_font": ("fonts", "Georgia"),
}
RELEVANT_GATES = ("contrast", "safe_zone", "min_px", "overlap", "fonts", "frame0", "copy")


@pytest.mark.skipif(not READY, reason="needs bwrap, ffmpeg, node and `social-studio engine install`")
@pytest.mark.parametrize("name", CALIBRATION_PASS)
def test_calibration_fixture_passes_every_relevant_gate(tmp_path, monkeypatch, name):
    ctx = _ctx(tmp_path, monkeypatch)
    result = _check(ctx, name, tmp_path / name)
    for gate in RELEVANT_GATES:
        assert result["gates"][gate] in ("ok", "skipped"), (gate, result["findings"])
    assert result["settled"], "expected at least one genuinely settled hold"


@pytest.mark.skipif(not READY, reason="needs bwrap, ffmpeg, node and `social-studio engine install`")
@pytest.mark.parametrize("name", sorted(CALIBRATION_FAIL))
def test_calibration_fixture_fails_its_named_gate_only(tmp_path, monkeypatch, name):
    gate, needle = CALIBRATION_FAIL[name]
    ctx = _ctx(tmp_path, monkeypatch)
    result = _check(ctx, name, tmp_path / name)
    assert result["gates"][gate] == "fail", result["findings"]
    assert any(needle in f["detail"] for f in result["findings"] if f["gate"] == gate), result["findings"]
    for other in RELEVANT_GATES:
        if other != gate:
            assert result["gates"][other] in ("ok", "skipped"), (other, result["findings"])


@pytest.mark.skipif(not READY, reason="needs bwrap, ffmpeg, node and `social-studio engine install`")
def test_calibration_poster_inside_a_move_is_flagged(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path, monkeypatch)
    result = _check(ctx, "two_line_title", tmp_path / "poster-move", poster_at=0.3)
    assert result["gates"]["poster"] == "fail"
    result = _check(ctx, "two_line_title", tmp_path / "poster-hold", poster_at=1.5)
    assert result["gates"]["poster"] == "ok"
