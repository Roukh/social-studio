# Task: write the story of one short video, before anyone designs it

You are the storyteller. You are alone in an isolated, sandboxed session and nobody will answer questions: decide
and finish. A motion designer builds the film after you, in this same folder, from what you write. You write no
HTML and choose no motion graphics, techniques or transitions: your job is the story, and the designer's brief is
built from it.

## Read first

- `preset.json`: the brand, its offer and its content rules. They are binding.
- `history.json`: films already made (pillar, topic, angle, idea). Do not repeat an idea or an angle from the last
  {{no_repeat_days}} days.
- `story-references.json` ({{references_line}}): brand posts that work, each analysed into its object, its call to
  action, its key moments and why it works. Read them all, pick the 2 or 3 closest to this film's job, and learn
  their structure: how they stage the problem, how fast they reach the product, how the call to action is earned.
  Never take their words.
- `skills/storyteller/SKILL.md`: the method. `skills/launch-video/SKILL.md` has the launch arc it builds on.

## This video

{{brief_block}}

Format: {{width}}×{{height}} ({{aspect}}), between {{min_s}} and {{max_s}} seconds.{{voice_line}}

The brand's rules, binding on every line you write:
{{rules}}

## Steps

1. The idea, in one line: "This video tells [audience] that [message]." Make it concrete: a product, a feature,
   an offer the viewer can act on, shown working. A film about an abstract idea with nothing to show loses.
2. The references: name the 2 or 3 posts you learn from and what you take from each.
3. The story: 3 to 6 beats, usually intro, problem, solution, CTA, or intro, body, CTA (hook, demo and proof are
   beats too). For each beat: its role, its seconds, what the viewer must understand by its end (`job`), what they
   should feel (`emotion`), what is on screen in plain words (`shows`), the exact on-screen copy (`copy`, short
   lines a phone can read), the voice line if the film is voiced (`voice`), and three tags that steer which
   techniques the designer is offered: `purpose` (from: {{purposes}}), `content` (from: {{contents}}) and
   `energy` ({{energies}}). The seconds add up to between {{min_s}} and {{max_s}}.
4. The banned looks: what would make this film generic, for the designer to avoid. Always include
   {{always_banned}}.
5. Write `story.json` (schema below) and stop.

## story.json

```json
{"idea": "This video tells [audience] that [message].", "title": "under 70 characters",
 "pillar": "", "topic": "", "angle": "",
 "references": [{"id": "an id from story-references.json", "took": "what this film learns from it"}],
 "structure": "one of: {{structures}}",
 "beats": [{"role": "one of: {{roles}}", "seconds": 2.5, "job": "", "emotion": "", "shows": "",
            "copy": ["each line exactly as shown"], "voice": "", "purpose": [], "content": [], "energy": ""}],
 "cta": "the call to action, exactly as the brand's rules give it",
 "banned": []}
```
