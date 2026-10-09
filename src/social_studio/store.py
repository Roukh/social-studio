"""The reference store: the techniques, scenes and story references every build draws from.

Each item is one JSON file under data/store/ (techniques/, scenes/, stories/), so an addition is a reviewable diff
and extraction sessions working side by side never write the same file. The store is SQLite, built from those
files on first use: tags are many-to-many facet rows, an FTS5 index covers the text, and one query joins both.

Kinds:
  technique  an atomic move (a wipe, a voxel field); its long recipe is skills/technique-library/techniques/<id>.md
  scene      one shot of a reference film; it combines techniques and carries a general prompt
  story      one analysed brand post: the object, the call to action, the key moments, the structure

Stdlib only and runnable on its own: a build copies this file and the built database into the session, where the
designer searches with `python3 tools/store.py search ...` (the same code the build retrieves with).
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE_DIR = HERE / "data" / "store"
RECIPES = HERE / "data" / "skills" / "technique-library" / "techniques"
FOLDERS = {"technique": "techniques", "scene": "scenes", "story": "stories"}
SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,95}")
ROLES = ("hook", "intro", "problem", "solution", "demo", "proof", "cta", "transition")  # a beat's or moment's role
TEXT_FIELDS = ("name", "looks", "build", "sound", "prompt", "object", "audience", "message", "cta", "why")
PROMPT_MAX = 1200
STOP = {"the", "and", "for", "with", "that", "this", "from", "into", "its", "are", "was", "but", "not", "you",
        "your", "our", "out", "one", "all", "has", "have", "then", "than", "what", "who", "how", "why", "when"}

SCHEMA = """
CREATE TABLE items (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('technique', 'scene', 'story')),
  name TEXT NOT NULL,
  prompt TEXT NOT NULL DEFAULT '',
  dur_min REAL, dur_max REAL,
  source TEXT NOT NULL DEFAULT '',
  body TEXT NOT NULL
);
CREATE TABLE tags (
  item TEXT NOT NULL REFERENCES items(id),
  facet TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (item, facet, value)
);
CREATE INDEX tags_value ON tags(facet, value);
CREATE TABLE uses (
  scene TEXT NOT NULL REFERENCES items(id),
  technique TEXT NOT NULL REFERENCES items(id),
  PRIMARY KEY (scene, technique)
);
CREATE VIRTUAL TABLE fts USING fts5(id UNINDEXED, text, tokenize = 'porter unicode61');
"""


class StoreError(ValueError):
    """The store's files break its rules; the message lists every problem."""


# --- loading and checking -----------------------------------------------------------------------------

def vocab(root: Path = STORE_DIR) -> dict:
    return json.loads((root / "facets.json").read_text())


def load(root: Path = STORE_DIR, files: list[Path] | None = None) -> list[dict]:
    """Every item, or only `files`; each keeps the file it came from as `_file`."""
    paths = files if files is not None else sorted(f for d in FOLDERS.values() for f in (root / d).glob("*.json"))
    items = []
    for f in paths:
        try:
            item = json.loads(Path(f).read_text())
        except (OSError, json.JSONDecodeError) as e:
            item = {"_error": f"{type(e).__name__}: {e}"}
        if not isinstance(item, dict):
            item = {"_error": "not a JSON object"}
        item["_file"] = str(f)
        items.append(item)
    return items


def _duration(v) -> bool:
    return (isinstance(v, list) and len(v) == 2 and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                                                         for x in v) and 0 < v[0] <= v[1] <= 60)


def check_item(item: dict, voc: dict, techniques: set[str]) -> list[str]:
    """What is wrong with one item: its shape, its tags against the vocabulary, its links. Empty when it is fine."""
    if "_error" in item:
        return [item["_error"]]
    out, kind, iid = [], item.get("kind"), str(item.get("id", ""))
    if kind not in FOLDERS:
        return [f"kind {kind!r} is not one of {', '.join(FOLDERS)}"]
    if not SLUG.fullmatch(iid):
        out.append(f"id {iid!r} is not a slug (a-z, 0-9, hyphens)")
    f = item.get("_file")
    if f and (Path(f).stem != iid or Path(f).parent.name != FOLDERS[kind]):
        out.append(f"a {kind} with id {iid!r} belongs in {FOLDERS[kind]}/{iid}.json")
    need = {"technique": ("name", "looks", "build", "prompt"), "scene": ("name", "looks", "build", "prompt"),
            "story": ("name", "brand", "object", "message", "cta", "why")}[kind]
    out += [f"{k} is missing or empty" for k in need if not str(item.get(k, "")).strip()]
    if len(str(item.get("prompt", ""))) > PROMPT_MAX:
        out.append(f"prompt is over {PROMPT_MAX} characters: a general prompt is a direction, not a script")
    if kind != "story" and not _duration(item.get("duration")):
        out.append("duration must be [min, max] seconds, 0 < min <= max <= 60")
    src = item.get("source")
    if kind == "scene":
        ok = isinstance(src, dict) and src.get("url") and src.get("film") and \
            all(isinstance(src.get(k), (int, float)) for k in ("start", "end")) and src["start"] < src["end"]
        if not ok:
            out.append("source must be {film, url, creator, start, end} with start < end")
        uses = item.get("techniques")
        if not isinstance(uses, list) or not uses:
            out.append("techniques must list the atomic techniques the scene uses")
        else:
            out += [f"technique {t!r} is not in the store" for t in uses if t not in techniques]
    elif kind == "story":
        if not (isinstance(src, dict) and src.get("url")):
            out.append("source must be {url, platform, posted}")
        moments = item.get("moments")
        if not isinstance(moments, list) or len(moments) < 2:
            out.append("moments must list the post's key moments, in order")
        else:
            for i, m in enumerate(moments):
                if not isinstance(m, dict) or m.get("role") not in ROLES or not str(m.get("what", "")).strip():
                    out.append(f"moment {i + 1} needs a role ({', '.join(ROLES)}) and what happens")
    elif not src:
        out.append("source must say where the technique comes from")
    if kind == "technique" and not (RECIPES / f"{iid}.md").is_file():
        out.append(f"no recipe at skills/technique-library/techniques/{iid}.md")
    out += _check_tags(item.get("tags"), voc, "technique" if kind == "scene" else kind,
                       voc["required"]["scene" if kind == "scene" else kind], voc.get("single", []))
    return out


def _check_tags(tags, voc: dict, space: str, required: list[str], single: list[str]) -> list[str]:
    if not isinstance(tags, dict):
        return ["tags must be an object of facet: [values]"]
    out, allowed = [], voc[space]
    for facet, values in tags.items():
        if facet not in allowed:
            out.append(f"tag facet {facet!r} is not one of {', '.join(allowed)}")
            continue
        vals = [values] if facet in single and isinstance(values, str) else values
        if not isinstance(vals, list) or not vals or (facet in single and len(vals) != 1):
            out.append(f"tags.{facet} must be {'one value' if facet in single else 'a non-empty list'}")
            continue
        out += [f"tags.{facet} value {v!r} is not in facets.json" for v in vals if v not in allowed[facet]]
    out += [f"tags.{facet} is missing" for facet in required if facet not in tags]
    return out


def problems(items: list[dict], voc: dict, known: set[str] | None = None) -> list[str]:
    """Every problem across items, prefixed by file. `known` adds technique ids that exist outside `items`."""
    techniques = {i.get("id") for i in items if i.get("kind") == "technique"} | (known or set())
    out, seen = [], {}
    for item in items:
        where = Path(item.get("_file", "?")).name
        out += [f"{where}: {p}" for p in check_item(item, voc, techniques)]
        iid = item.get("id")
        if iid in seen:
            out.append(f"{where}: id {iid!r} is also used by {seen[iid]}")
        seen.setdefault(iid, where)
    return out


# --- the database ---------------------------------------------------------------------------------------

def _tag_rows(item: dict) -> list[tuple[str, str]]:
    return [(facet, v) for facet, values in item.get("tags", {}).items()
            for v in ([values] if isinstance(values, str) else values)]


def _text(item: dict) -> str:
    parts = [str(item.get(k, "")) for k in TEXT_FIELDS]
    parts += [str(m.get(k, "")) for m in item.get("moments", []) if isinstance(m, dict) for k in ("what", "copy")]
    parts += [v for _, v in _tag_rows(item)] + [str(t) for t in item.get("techniques", [])] + [str(item.get("brand", ""))]
    return " ".join(p for p in parts if p)


def _source_line(item: dict) -> str:
    src = item.get("source")
    if not isinstance(src, dict):
        return str(src or "")
    span = f", {src['start']:g}-{src['end']:g} s" if isinstance(src.get("start"), (int, float)) else ""
    who = src.get("creator") or item.get("brand") or ""
    return f"{src.get('url', '')} ({who}{span})".replace(" ()", "")


def build(items: list[dict], path: str = ":memory:") -> sqlite3.Connection:
    """The SQLite store, built from checked items."""
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    with con:
        for item in items:
            body = {k: v for k, v in item.items() if not k.startswith("_")}
            d = item.get("duration") if _duration(item.get("duration")) else [None, None]
            con.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (item["id"], item["kind"], item["name"], item.get("prompt", ""), d[0], d[1],
                         _source_line(item), json.dumps(body)))
            con.executemany("INSERT INTO tags VALUES (?, ?, ?)", [(item["id"], f, v) for f, v in _tag_rows(item)])
            con.execute("INSERT INTO fts VALUES (?, ?)", (item["id"], _text(item)))
        for item in items:
            if item["kind"] == "scene":
                con.executemany("INSERT INTO uses VALUES (?, ?)", [(item["id"], t) for t in item["techniques"]])
    return con


_CHECKED: dict[str, list[dict]] = {}
_LOCK = threading.Lock()


def open_store(root: Path = STORE_DIR) -> sqlite3.Connection:
    """A new connection to the checked store for `root`. The files are read and checked once per process; each
    caller gets its own in-memory database (a few ms to build), since a SQLite connection serves one thread and
    `build --parallel` prepares sessions on several. A broken store raises StoreError, never half-loads."""
    key = str(root)
    with _LOCK:
        if key not in _CHECKED:
            items = load(root)
            found = problems(items, vocab(root))
            if found:
                raise StoreError(f"the reference store at {root} has {len(found)} problem(s): "
                                 + "; ".join(found[:10]))
            _CHECKED[key] = items
    return build(_CHECKED[key])


def save(con: sqlite3.Connection, path: Path) -> None:
    """A file copy of the store, for a session to search."""
    path.unlink(missing_ok=True)
    dst = sqlite3.connect(path)
    with dst:
        con.backup(dst)
    dst.close()


# --- queries --------------------------------------------------------------------------------------------

def fts_query(text: str) -> str:
    """Free text as an FTS5 OR-query of its words, each quoted, so no user text is FTS syntax."""
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOP]
    return " OR ".join(f'"{w}"' for w in dict.fromkeys(words))


RANK_SQL = """
WITH m AS (
  SELECT t.item AS id,
    SUM(CASE
      WHEN t.facet = 'role' AND t.value = :role THEN 3.0
      WHEN t.facet = 'purpose' AND t.value IN (SELECT value FROM json_each(:purpose)) THEN 2.0
      WHEN t.facet = 'content' AND t.value IN (SELECT value FROM json_each(:content)) THEN 1.5
      WHEN t.facet = 'energy' AND t.value = :energy THEN 1.0
      WHEN t.facet = 'format' AND t.value = :format THEN 1.0
      ELSE 0 END) AS facets,
    MAX(t.facet = 'role' AND t.value = :role) AS role_hit,
    group_concat(CASE WHEN (t.facet = 'role' AND t.value = :role)
      OR (t.facet = 'purpose' AND t.value IN (SELECT value FROM json_each(:purpose)))
      OR (t.facet = 'content' AND t.value IN (SELECT value FROM json_each(:content)))
      OR (t.facet = 'energy' AND t.value = :energy) THEN t.facet || ' ' || t.value END, '; ') AS matched
  FROM tags t GROUP BY t.item
)
SELECT i.id, i.kind, i.name, i.prompt, i.dur_min, i.dur_max, i.source, i.body, m.facets, m.role_hit, m.matched,
       {rank} AS rank
FROM items i JOIN m ON m.id = i.id {join}
WHERE i.kind IN (SELECT value FROM json_each(:kinds))
"""


def rank(con: sqlite3.Connection, *, role: str = "", purpose: list[str] = (), content: list[str] = (),
         energy: str = "", fmt: str = "", text: str = "", kinds=("technique", "scene")) -> list[dict]:
    """Every item of `kinds`, scored: facet matches (role 3, purpose 2, content 1.5, energy 1, format 1) plus up to
    2 for how well the text matches (FTS5 bm25). Highest first."""
    q = fts_query(text)
    sql = RANK_SQL.format(rank="f.r" if q else "NULL",
                          join="LEFT JOIN (SELECT id, bm25(fts) AS r FROM fts WHERE fts MATCH :q) f ON f.id = i.id"
                          if q else "")
    params = {"role": role, "purpose": json.dumps(list(purpose)), "content": json.dumps(list(content)),
              "energy": energy, "format": fmt, "kinds": json.dumps(list(kinds)), "q": q}
    rows = [dict(r) for r in con.execute(sql, params)]
    best = min((r["rank"] for r in rows if r["rank"] is not None), default=None)
    order = {f: i for i, f in enumerate(("role", "purpose", "content", "energy"))}
    for r in rows:
        bonus = 2 * r["rank"] / best if best and r["rank"] is not None else 0.0   # bm25: lower is better
        r["score"] = round(r["facets"] + bonus, 3)
        why = sorted((r["matched"] or "").split("; "), key=lambda m: (order.get(m.split(" ")[0], 9), m))
        r["matched"] = "; ".join([m for m in why if m] + (["text"] if bonus >= 0.5 else []))
    return sorted(rows, key=lambda r: (-r["score"], r["id"]))


def _candidate(r: dict) -> dict:
    body = json.loads(r["body"])
    out = {"id": r["id"], "kind": r["kind"], "name": r["name"], "why": r["matched"] or "text",
           "looks": body.get("looks", ""), "prompt": r["prompt"], "duration": [r["dur_min"], r["dur_max"]],
           "source": r["source"]}
    if r["kind"] == "scene":
        out["techniques"] = body.get("techniques", [])
    if r["kind"] == "technique":
        out["recipe"] = f"skills/technique-library/techniques/{r['id']}.md"
    return out


def for_beats(con: sqlite3.Connection, beats: list[dict], fmt: str, recent: set[str] = frozenset(),
              per_beat: int = 3, film_text: str = "") -> dict:
    """The top items for each story beat, and for the film as a whole (texture, frame, through-line). An item serves
    one beat only, and an item whose techniques a recent film used drops 2 points, so the film keeps its range."""
    taken: set[str] = set()

    def pick(rows: list[dict], n: int, need_role: bool) -> list[dict]:
        out = []
        for r in rows:
            uses = set(json.loads(r["body"]).get("techniques", [])) | {r["id"]}
            r["score"] -= 2.0 if uses & recent else 0.0
        for r in sorted(rows, key=lambda r: (-r["score"], r["id"])):
            if len(out) == n:
                break
            if r["id"] in taken or r["score"] <= 0 or (need_role and not r["role_hit"]):
                continue
            taken.add(r["id"])
            out.append(_candidate(r))
        return out

    plan = []
    for i, b in enumerate(beats):
        text = " ".join(str(b.get(k, "")) for k in ("job", "emotion", "voice")) + " " + " ".join(b.get("copy", []))
        rows = rank(con, role=b.get("role", ""), purpose=b.get("purpose", []), content=b.get("content", []),
                    energy=b.get("energy", ""), fmt=fmt, text=text)
        plan.append({"beat": i + 1, "role": b.get("role", ""), "candidates": pick(rows, per_beat, True)
                     or pick(rows, per_beat, False)})
    film = pick(rank(con, role="whole-film", fmt=fmt, text=film_text), 3, True)
    return {"format": fmt, "beats": plan, "film": film}


def stories_for(con: sqlite3.Connection, text: str, fmt: str = "", goal: list[str] = (), product: list[str] = (),
                limit: int = 8) -> list[dict]:
    """The story references that fit a brand best: goal 2, product 2, format 1, plus up to 2 for the text."""
    q = fts_query(text)
    sql = f"""
      SELECT i.id, i.body,
        COALESCE((SELECT SUM(CASE WHEN facet = 'goal' AND value IN (SELECT value FROM json_each(:goal)) THEN 2.0
                                  WHEN facet = 'product' AND value IN (SELECT value FROM json_each(:product)) THEN 2.0
                                  WHEN facet = 'format' AND value = :fmt THEN 1.0 ELSE 0 END)
                  FROM tags WHERE item = i.id), 0) AS facets,
        {'f.r' if q else 'NULL'} AS rank
      FROM items i {'LEFT JOIN (SELECT id, bm25(fts) AS r FROM fts WHERE fts MATCH :q) f ON f.id = i.id' if q else ''}
      WHERE i.kind = 'story'"""
    rows = [dict(r) for r in con.execute(sql, {"goal": json.dumps(list(goal)), "product": json.dumps(list(product)),
                                               "fmt": fmt, "q": q})]
    best = min((r["rank"] for r in rows if r["rank"] is not None), default=None)
    for r in rows:
        r["score"] = r["facets"] + (2 * r["rank"] / best if best and r["rank"] is not None else 0.0)
    rows.sort(key=lambda r: (-r["score"], r["id"]))
    return [json.loads(r["body"]) for r in rows[:limit]]


def search(con: sqlite3.Connection, text: str = "", kind: str = "", facets: dict[str, str] | None = None,
           limit: int = 10) -> list[dict]:
    """Items matching every facet filter, best text match first."""
    q, where, params = fts_query(text), [], {}
    for n, (facet, value) in enumerate((facets or {}).items()):
        where.append(f"EXISTS (SELECT 1 FROM tags WHERE item = i.id AND facet = :f{n} AND value = :v{n})")
        params.update({f"f{n}": facet, f"v{n}": value})
    if kind:
        where.append("i.kind = :kind")
        params["kind"] = kind
    if q:
        where.append("i.id IN (SELECT id FROM fts WHERE fts MATCH :q)")
        params["q"] = q
    order = "(SELECT bm25(fts) FROM fts WHERE fts MATCH :q AND fts.id = i.id)" if q else "i.kind, i.id"
    sql = (f"SELECT i.id, i.kind, i.name, i.prompt, i.source FROM items i "
           f"{'WHERE ' + ' AND '.join(where) if where else ''} ORDER BY {order} LIMIT :limit")
    return [dict(r) for r in con.execute(sql, {**params, "limit": limit})]


def stats(con: sqlite3.Connection) -> dict:
    kinds = dict(con.execute("SELECT kind, COUNT(*) FROM items GROUP BY kind").fetchall())
    facets = {}
    for facet, value, n in con.execute("SELECT facet, value, COUNT(*) FROM tags GROUP BY facet, value ORDER BY 1, 3 DESC"):
        facets.setdefault(facet, {})[value] = n
    return {"items": kinds, "tags": facets}


# --- command line (extraction sessions at a dev checkout; the designer inside a session) ---------------------

def _connect(db: str | None) -> sqlite3.Connection:
    if db:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        return con
    return open_store()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="store.py", description="Search or check the reference store.")
    ap.add_argument("--db", help="a built store file (in a session: store.db); default: build from the JSON files")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check every item, or the files given; lists every problem")
    c.add_argument("files", nargs="*", type=Path)
    s = sub.add_parser("search", help="find items: free text plus facet filters, e.g. --tag role=hook")
    s.add_argument("text", nargs="?", default="")
    s.add_argument("--kind", choices=list(FOLDERS))
    s.add_argument("--tag", action="append", default=[], metavar="FACET=VALUE")
    s.add_argument("-n", type=int, default=10)
    g = sub.add_parser("show", help="one item in full")
    g.add_argument("id")
    sub.add_parser("stats", help="items per kind and tag counts")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        items = load(files=a.files or None)
        known = {i["id"] for i in load() if i.get("kind") == "technique"} if a.files else set()
        found = problems(items, vocab(), known)
        print("\n".join(found) if found else f"ok: {len(items)} item(s)")
        return 1 if found else 0
    con = _connect(a.db)
    if a.cmd == "search":
        facets = dict(t.split("=", 1) for t in a.tag if "=" in t)
        for r in search(con, a.text, a.kind or "", facets, a.n):
            print(f"{r['id']}  [{r['kind']}]  {r['name']}\n    {r['prompt'][:200]}")
    elif a.cmd == "show":
        row = con.execute("SELECT body FROM items WHERE id = ?", (a.id,)).fetchone()
        if not row:
            print(f"no item {a.id!r}", file=sys.stderr)
            return 1
        print(json.dumps(json.loads(row["body"]), indent=2))
    else:
        print(json.dumps(stats(con), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
