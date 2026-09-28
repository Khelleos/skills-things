# dfd in draw.io

Read `../../_shared/types/dfd.md` first. This file only says what draw.io
does with it.

**Layout:** `container`. Coverage is **full**.

## The trust boundary

A group with `kind: "trust"` is drawn as a **dashed red frame** with its
label in the same red at the top left -- the convention from plan section 3,
identical in both formats.

It is deliberately the only red on the page. Nothing else in the style
vocabulary uses it, so a crossing is visible before a single label is read.

## Shapes

| `role` | Drawn as |
|---|---|
| `process` | rectangle |
| `store` | cylinder, pale blue |
| `external` | dashed grey rectangle |
| `actor` | ellipse |

Edges: solid for `flow` and `write`, dashed for `read`. The label carries the
data; the arrowhead carries the direction.

## What to know before shipping

- **Edge labels sit on the line** and a line crossing a boundary passes
  through the frame's border. Keep the label short or move it to the prose.
- **A store inside one boundary read by a process in another** is the shape
  this type exists to make visible. Do not let the budget delete that edge --
  drop a node instead.
- Nested boundaries work, but two nested dashed red frames read as one thick
  one. If trust has three levels, that is two diagrams.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
