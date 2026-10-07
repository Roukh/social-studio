# Vendored skills

Third-party agent skills, copied at the commits pinned in `skills.lock.json` (repo, commit, path, licence, tree
hash). Each pack keeps its own `LICENSE` (and `NOTICE` where the upstream ships one); a mounted sub-skill gets its
pack's licence copied beside it. A preset mounts them by name through `agent.package_skills`.

Changes from upstream:
- `impeccable/scripts/` was removed: its launcher downloads a binary on first run, which sessions must never do.

Skills written for live web pages drive motion with `requestAnimationFrame` and `Math.random`. In a session their
techniques apply, but every frame is drawn from time (the house rules).
