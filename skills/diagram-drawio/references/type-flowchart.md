# flowchart in draw.io

Read `../../_shared/types/flowchart.md` first. This file only says what
draw.io does with it.

**Layout:** `layered`. Coverage is **full**.

## How the type is placed

Ranks run top to bottom, one per step of the procedure, with branches
spreading sideways within a rank. Unlike Mermaid, **the left branch stays on
the left**: positions are computed and written down, so prose beside the
diagram may safely say "the left-hand path".

That is a real difference and worth spending. If the surrounding text needs
to refer to a branch by where it sits, this is the format that allows it.

## Shapes

- **stadium, pale green** — `start` and `end`, the way in and the way out.
- **rhombus, pale yellow** — `decision`. The colour is the signal to slow
  down; every diagram in this toolchain uses it for the same thing.
- **parallelogram** — `io`, something read or written.
- **process with side bars** — `subroutine`, a step drawn elsewhere.

## What to know before shipping

- **Branch labels are edge labels**, drawn on the line. Keep them to a word:
  `yes`, `no`, `expired`. A sentence on an edge collides with the shapes it
  passes.
- **Loops back to an earlier step are routed around the outside.** One is
  fine. Two, and the return paths start crossing the forward ones — which is
  the signal in `flowchart.md` that the procedure wants splitting.
- **`subroutine` is a promise.** It gets a shape of its own -- a rectangle
  with side bars -- which tells a reader this step is drawn elsewhere. If it
  is not, the shape is decoration and the reader is left wondering why one
  box looks different. `validate_graph.py` warns when the role carries no
  `note` naming that other diagram; the fix is usually `process`.
- **A decision with one way out is a step**, and `validate_graph.py` says so.
  It is a warning rather than an error because a guard clause that always
  falls through can be a legitimate simplification, but it usually means an
  arm went missing.

## Compared with Mermaid

Better here: stable left and right, so the prose can name a branch. Exact
placement for a slide or a printed runbook.

Worse here: a runbook is read at 3am on a phone, and a `.drawio` will not
render there. For anything on-call, Mermaid inline in the Markdown wins.

## Not checked by anything

Whether it looks right. Say so.
