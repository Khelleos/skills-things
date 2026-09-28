# swimlane in draw.io

Read `../../_shared/types/swimlane.md` first. This file only says what draw.io
does with it.

**Layout:** `container`, in lane mode. Coverage is **full**, and clearly
better than Mermaid.

## How it is placed

**Lanes keep the order they were written in.** They are not ranked by the
flow -- that is the whole point of the type, and the layout has a mode of its
own for it. Every lane gets the same width and they stack down the page in
declaration order.

A step belonging to no lane is an **error**, not a stray box:

> swimlane: every step belongs to a lane; <id> is in none

Within a lane, steps are arranged left to right in the order they were
declared, wrapping if the lane runs long.

## Shapes

The flowchart vocabulary unchanged: stadium for start and end, rhombus for a
decision, parallelogram for I/O, rectangle for a step. The lane itself is a
`swimlane` cell with its name on the top edge.

## What to know before shipping

- **A handover is an edge leaving one lane and entering another**, and
  draw.io routes it across the lane boundary. Those crossings are what the
  reader counts, so keep the lane order such that most flow goes downward.
- **Five lanes is the limit.** Past that the page is taller than it is
  readable.
- Moving a step into another lane by hand changes nothing in `graph.json`,
  and regenerating puts it back.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
