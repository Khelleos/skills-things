# state in draw.io

Read `../../_shared/types/state.md` first. This file only says what draw.io
does with it.

**Layout:** `layered`. Coverage is **full**, and in one respect better than
Mermaid.

## How the type is placed

States rank downwards from the entry, transitions become labelled edges. The
`choice` role gets the same rhombus a flowchart decision gets — one shape,
one meaning, across every type in the toolchain.

**`start` and `end` are drawn as real, separate shapes.** Mermaid collapses
both onto `[*]` and tells them apart by direction; here they are two stadium
boxes and each keeps its label. A machine with three ways to finish — done,
cancelled, expired — reads properly in this format and reads as three
identical `[*]` markers in the other.

That is the reason `state.md` asks for a label on `start` and `end` even
though Mermaid throws it away.

## Shapes

- **rounded rectangle, white** — a state.
- **stadium, pale green** — `start` and `end`.
- **rhombus, pale yellow** — `choice`.

## What to know before shipping

- **`note` on a state is not drawn.** Unlike the Mermaid writer, which has a
  real `note right of` block, the layered builder has nowhere to put one; it
  survives as an XML comment. If the note matters to the reader, fold it into
  the state's label or into the prose.
- **Self-transitions** — a state that loops to itself — are routed by draw.io
  as a small arc. They work, but the event label lands close to the box; if
  two states both self-loop, expect to move one label by hand.
- **A machine with more than one entry** draws fine and reads badly.
  `validate_graph.py` warns about it.

## Compared with Mermaid

Better here: distinct, labelled terminals; stable placement; real shapes for
a slide.

Worse here: no drawn notes, and no rendering in a pull request.

## Not checked by anything

Whether it looks right. Say so.
