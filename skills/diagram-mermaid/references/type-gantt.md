# gantt in Mermaid

Read `../../_shared/types/gantt.md` first. This file only says what Mermaid
does with it.

**Renders as:** `gantt`. Coverage is **full**, with one hard requirement.

## Dates, or nothing

Mermaid's gantt understands real dates and nothing else. The generator
**refuses** a graph whose spans carry ordinals rather than `YYYY-MM-DD`,
rather than inventing dates to make it render:

> Mermaid's gantt only understands real dates. Either give every span a start
> and an end in YYYY-MM-DD, or draw it in draw.io, whose timeline axis is
> ordinal and does not care.

That refusal is the right answer often enough to be worth the friction: a
plan with no dates is not a Gantt.

## How the type maps

| In `graph.json` | In Mermaid |
|---|---|
| track | `section <label>` |
| span, kind `task` | `<label> :<id>, <start>, <end>` |
| span, kind `milestone` | `<label> :milestone, <id>, <start>, 0d` |
| `depends_on` | **not drawn** |

## What is lost

**Dependencies.** Mermaid's gantt has `after <id>` for scheduling, but no
drawn arrow between bars. `depends_on` is kept in the intent and drawn by
draw.io; here it is invisible. If the dependencies are the point, say so and
use draw.io.

## What to know before shipping

- `axisFormat %d %b` is set, which reads well up to about three months.
- Two overlapping spans on one track render as two lines, which is what
  Mermaid does naturally and what the draw.io layout was taught to match.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
