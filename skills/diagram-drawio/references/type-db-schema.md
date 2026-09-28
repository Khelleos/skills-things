# db-schema in draw.io

Read `../../_shared/types/db-schema.md` first. This file only says what draw.io
does with it.

**Layout:** `table`. Coverage is **full**, and better than Mermaid on two
counts.

## What draw.io carries that Mermaid does not

**Table names as written.** `celery_taskmeta` and `order line` are both drawn
exactly as given; Mermaid would make the second an identifier.

**Row notes.** An index, a default, a check constraint -- anything put in a
row's `note` is drawn beside the row rather than lost. This is where indexes
live, and it is the reason this type is full coverage here and approximate
there.

## How it is placed

One swimlane per table: the name in the title bar, one child cell per column.
Boxes are sized from their widest row and gridded three across. A row marked
`pk` or `uk` is drawn in bold, which is the entire key notation.

Relations are orthogonal and go round any table in between, with the
cardinality written at each end -- `1` and `0..n` -- rather than crow's feet, so no legend is needed.

## What to know before shipping

- **The gap between tables is sized from the widest relation label**, up to
  300 pixels, because the label is drawn in that gap. Past 40 characters
  `validate_graph.py` says the label is the problem: a relation label is a
  verb.
- **Fifteen rows per table** is the limit here, looser than the data model's
  twelve.
- Relations are not routed around boxes; with eight tables in a grid, a line
  between distant ones may pass under a third.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
