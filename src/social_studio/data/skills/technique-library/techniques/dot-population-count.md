# dot-population-count

**Family:** data, particles. **Wants:** 2.5-5 s (longer when the dots redistribute into a second shape).
**Source:** prompt-motion.com's gallery (jesscaroline7-1ff7cb), studied 2026-10-09.

## Looks

A big number counts up while, under it, a population of small dots stands for the total, one dot per unit: a
tidy grid when the count is exact, a looser cluster when it is not. A subset highlights in the accent colour to
call out a slice of the total (a column, a filtered group), then the dots let go of the grid and relax apart,
or gather into a ring whose arc-length per colour reads as a share of the whole. Small mono labels at the edges
name the outliers the main cluster doesn't cover.

## Build

- One dot per unit up to a few hundred; above that, sample (1 dot per N units) and say so in a small label.
- Grid state: dots at `(col * spacing, row * spacing)` with a tiny per-dot random jitter (±1-2 px) so it never
  looks like a raster. Highlight subset: recolor dots whose index falls in the called-out range, accent colour,
  `stagger` by column.
- Scatter/relax state: each dot tweens from its grid `(x,y)` to a target position inside a soft circular
  scatter (`r = R * sqrt(random())`, `theta = random() * 2π`) with per-dot easing offsets so the field settles
  unevenly, not as one wave.
- Ring state (for a breakdown): bucket the dots by category, lay each bucket along its own arc proportional to
  its share, `angle = category.count / total * 2π`, with 1-2 px of radius jitter so the ring reads as dust, not
  a stroke.
- The number count-up ties to the same clock driving the dots so both land on the same beat.

## Sound

A soft granular patter while the dots settle, a tick on the count-up digits, a slightly louder tick when the
accent subset highlights.

## Adapting

Keep the unit honest: if a dot cannot mean one real thing, label it "sample" or show a rate instead. In 9:16,
stack the number above a taller, narrower field so the grid keeps readable spacing.
