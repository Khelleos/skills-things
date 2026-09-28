# data-model in draw.io

Read `../../_shared/types/data-model.md` first. This file only says what
draw.io does with it.

**Layout:** `table`. Coverage is **full**, and better than Mermaid on two
counts.

## How the type is placed

Each entity is a swimlane: a title bar with the entity name, and one child
cell per row beneath it. Boxes are sized from their widest row and gridded
three across, each grid row aligned on its top edge.

**Entity names are drawn as written.** This is the first place draw.io wins:
Mermaid names an ER block with a bare token, so `Refresh token` has to become
`Refresh_token`. Here the label is a label, spaces and all.

**Rows keep their types and their notes.** Mermaid's ER needs a type on every
attribute and prints `unknown` without one; here a row with no type simply
has no type shown. That is not permission to leave types out — `data-model.md`
still asks for them — but it does mean the diagram is not disfigured by a
gap.

A row marked `pk` or `uk` is drawn in bold. That is the whole key notation:
no separate column, no legend to read.

## Relations

Drawn orthogonal, leaving each table on the side that faces the other and going
round any table in between, with the cardinality written at each end as a
small label on the edge:

| `cardinality` | Near end | Far end |
|---|---|---|
| `1-1` | 1 | 1 |
| `1-n` | 1 | n |
| `n-1` | n | 1 |
| `n-n` | n | n |

`optional: true` turns the far end into `0..n` or `0..1`. Crow's feet are not
used: the text says the same thing and does not need a key.

## What to know before shipping

- **An entity note is drawn nowhere.** It survives as an XML comment. Put
  anything the reader must see into the label or into the prose.
- **Three boxes per grid row is fixed.** With eight entities that gives three,
  three and two, which reads fine; it is not chosen per diagram.
- **Relations are not routed around boxes.** With entities in a grid, an edge
  between two distant ones may pass under a third. Eight entities is the
  limit for a reason.
- **The label sits in the gap between two tables**, so the gap is sized from
  the widest relation label in the diagram, up to 300 pixels. Past that the
  gap stops growing and the label is the problem: `validate_graph.py` warns
  at 40 characters, because a relation label is a verb and a sentence there
  pushes the whole page apart.

## Compared with Mermaid

Better here: real labels, optional types, bold keys, notes on rows.

Worse here: no rendering in a pull request, and a model that changes weekly
is easier to keep honest as text.

## Not checked by anything

Whether it looks right. Say so.
