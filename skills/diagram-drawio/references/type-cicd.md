# cicd in draw.io

Read `../../_shared/types/cicd.md` first. This file only says what draw.io
does with it.

**Layout:** `layered`. Coverage is **full**.

## How it is placed

Stages rank downwards, and `tier` pins a stage to a row -- worth using here,
because a pipeline has a natural sequence of stages that a reader expects to
see as rows.

Unlike Mermaid, **the position of a parallel job is stable**: if lint sits
left of the tests in one render it sits left in the next, so the prose beside
the diagram may safely say "the left-hand job".

## Shapes

| `role` | Drawn as |
|---|---|
| `start`, `end` | stadium, pale green |
| `job` | rectangle |
| `gate` | rhombus, pale yellow |
| `artifact` | cylinder, pale blue |
| `environment` | rectangle with side bars |

A `trigger` edge is drawn with a thick line -- the one place a thick line is
used in this toolchain, marking the outside event that starts everything.

## What to know before shipping

- **A failure loop back to the start** is routed around the outside. It
  works; it is also the signal that the diagram is carrying two stories.
- **An artifact is a cylinder**, the same shape a database gets. That is
  deliberate: both are things that outlive the step that made them.
- Coordinates are final, so a long job name makes a permanently wide box.
  Keep stage names to two or three words.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
