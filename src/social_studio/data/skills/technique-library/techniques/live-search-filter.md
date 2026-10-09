# live-search-filter

**Family:** interface. **Wants:** 1.5-2.5 s. **Source:** prompt-motion.com's gallery (mehul4795-4a7007),
studied 2026-10-09.

## Looks

A search field types on with a short query; a list beneath it narrows from many rows to just the matching ones
as each character lands, and the matched substring inside each surviving row highlights in the accent colour.
The narrowing itself is the proof that search works, not a separate results screen.

## Build

- The full list is present underneath from the start, dimmed or off-screen below the fold; as the query types
  on, non-matching rows animate out (`height -> 0`, `opacity -> 0`, 150-200ms, staggered by their position) on
  every keystroke that changes the match set, not just the final one.
- The matched substring inside each surviving row gets a background highlight that fades in once filtering
  settles (not per keystroke, to avoid flicker).

## Sound

A soft mechanical key-tick under the typed query, a light whoosh as rows filter out, nothing on the final
settle.

## Adapting

Keep the query short (one or two words) and let 2-4 rows survive — enough to prove relevance without the list
feeling cherry-picked.
