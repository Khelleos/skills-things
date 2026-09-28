# gantt in draw.io

Read `../../_shared/types/gantt.md` first. This file only says what draw.io
does with it.

**Layout:** `timeline`. Coverage is **full**, and it carries one thing
Mermaid does not.

## The axis is ordinal

Neighbouring values sit one column apart whether they are a day or a quarter
apart. A timeline here answers "what follows what"; it does not claim to
answer "how long", and the column spacing would be a lie if it did.

The consequence is a useful one: **draw.io draws a timeline whose axis is not
made of dates**, where Mermaid's gantt refuses. Ordinals, sprint numbers,
release names -- all fine.

## How it is placed

One band per track, the track name on the left edge, spans placed along the
axis. **Spans that overlap in time on one track are packed into sub-rows**,
because two things running at once is ordinary and drawing them on top of
each other is not. A track whose spans never overlap keeps a single row.

| `kind` | Drawn as |
|---|---|
| `task` | rounded bar, pale blue |
| `milestone` | rhombus, pale yellow |

`depends_on` is drawn as a dashed arrow between spans -- the thing Mermaid's
gantt cannot show at all.

## What to know before shipping

- **A bar's width is columns, not days.** Do not let prose beside the diagram
  say a task is twice as long as another because its bar is twice as wide.
- Five tracks and fifteen spans is the limit.
- The axis ticks are drawn above the first band as plain text, not as a
  ruler. They label columns; they do not measure them.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
