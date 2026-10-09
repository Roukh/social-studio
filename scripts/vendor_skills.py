#!/usr/bin/env python3
"""Vendor a skill pack at a pinned commit into src/social_studio/data/skills/vendor/ (rule R7).

    python3 scripts/vendor_skills.py OWNER/REPO SHA NAME --licence MIT --what "one line" [--path skills]

Downloads the repo at SHA (never a branch or tag), copies every folder under --path that holds a SKILL.md into
vendor/NAME/ with the repo's LICENSE (and NOTICE), and records the pack in skills.lock.json with the same tree hash
tests/test_reel.py checks. Refuses a pack with no licence file. A pack already in the lock is replaced.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import re
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

VENDOR = Path(__file__).resolve().parent.parent / "src" / "social_studio" / "data" / "skills" / "vendor"
LICENCES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "NOTICE", "NOTICE.md", "NOTICE.txt")


def tree_sha256(root: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file()
                    and not any(part.startswith(".") for part in p.relative_to(root).parts)):
        h.update(str(f.relative_to(root)).encode() + b"\0" + hashlib.sha256(f.read_bytes()).digest())
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("repo")
    ap.add_argument("sha")
    ap.add_argument("name")
    ap.add_argument("--licence", required=True, choices=["MIT", "Apache-2.0"])
    ap.add_argument("--what", required=True)
    ap.add_argument("--path", default="skills", help="folder in the repo that holds the skills")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{40}", a.sha):
        ap.error("pin a full 40-character commit sha, never a branch or tag")
    url = f"https://codeload.github.com/{a.repo}/tar.gz/{a.sha}"
    with urllib.request.urlopen(url, timeout=120) as resp:
        data = resp.read()
    dst = VENDOR / a.name
    tmp = VENDOR / f".{a.name}.partial"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for m in tar.getmembers():
            parts = m.name.split("/", 1)
            if len(parts) < 2 or not (m.isfile() or m.isdir()):
                continue
            rel = parts[1]
            if rel in LICENCES:
                m.name = rel
            elif rel.startswith(a.path.rstrip("/") + "/"):
                m.name = rel[len(a.path.rstrip("/")) + 1:]
            else:
                continue
            tar.extract(m, tmp, filter="data")
    skills = sorted(p.parent.relative_to(tmp) for p in tmp.rglob("SKILL.md"))
    if not any((tmp / n).is_file() for n in LICENCES):
        shutil.rmtree(tmp)
        sys.exit(f"{a.repo}@{a.sha} has no licence file: not vendored (rule R7)")
    if not skills:
        shutil.rmtree(tmp)
        sys.exit(f"no SKILL.md under {a.path}/ in {a.repo}@{a.sha}")
    shutil.rmtree(dst, ignore_errors=True)
    tmp.rename(dst)
    lock_file = VENDOR / "skills.lock.json"
    lock = json.loads(lock_file.read_text())
    lock["packs"] = [p for p in lock["packs"] if p["name"] != a.name]
    lock["packs"].append({
        "name": a.name, "repo": a.repo, "sha": a.sha,
        "path_in_repo": f"{a.path} ({', '.join(str(s) for s in skills)})", "licence": a.licence,
        "skills": [f"{a.name}/{s}" for s in skills], "tree_sha256": tree_sha256(dst),
        "fetched": datetime.date.today().isoformat(), "what": a.what})
    lock_file.write_text(json.dumps(lock, indent=2) + "\n")
    print(f"vendored {a.repo}@{a.sha[:8]} as {a.name}: {', '.join(str(s) for s in skills)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
