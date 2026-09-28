# c4 in draw.io

Read `../../_shared/types/c4.md` first. This file only says what draw.io
does with it.

**Layout:** `container`. Coverage is **full at every level**, which is the
reason to reach for this format at levels 3 and 4.

## How it is placed

One frame for the system boundary, people and external systems outside it,
and the contents arranged in rows inside. At level 3 and 4 the nesting is
real: an inner frame is a child cell, so it moves with its parent and a
reader can tell which boundary is which by the title bar rather than by
counting borders.

## Shapes

| `role` | Drawn as |
|---|---|
| `person` | ellipse |
| `system`, `container`, `component` | rectangle |
| `store` | cylinder, pale blue |
| `external` | dashed grey rectangle |

**No AWS or Azure icon sets.** They were considered and left out: a shape
name is an exact string, a typo produces an empty shape that no check
catches, and at levels 1 and 2 an icon adds nothing a label does not. If they
ever go in, it will be for `deployment`, and each name will be checked by eye
once.

## What to know before shipping

- **`meta.level` does not change the drawing.** It is there so the diagram
  says which level it is and so a reviewer can tell when two levels have been
  mixed.
- **Technology notes are not drawn.** C4 conventionally puts "[Python,
  FastAPI]" under a container name; here that belongs in the label itself if
  it matters, because a node `note` survives only as an XML comment.
- Four frames is the limit, and at level 2 one is usually right.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
