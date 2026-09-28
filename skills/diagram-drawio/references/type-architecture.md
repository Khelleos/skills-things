# architecture in draw.io

Read `../../_shared/types/architecture.md` first — it decides what goes in
the diagram. This file only says what draw.io does with it.

**Layout:** `layered`. Coverage is **full**.

## How the type is placed

`tier` is authoritative here, in a way it is not in Mermaid. In Mermaid it
only nudges declaration order; here it pins the node to a row, and everything
without a tier falls below whatever points at it. If the diagram should read
as tiers — edge, application, data — give every node a tier and it will.

Within a row, order comes from two barycentre passes: each box slides towards
the average position of what points at it. It is not optimal and does not
claim to be; it removes the crossings a reader would notice.

## Shapes

From the vocabulary in `SKILL.md`. The three that carry the most weight on an
architecture diagram:

- **cylinder, pale blue** — a store. State that outlives a request.
- **parallelogram, pale amber** — a queue. Data in motion.
- **dashed grey** — external. Not ours to change, and the dash says so before
  the label is read.

## What to know before shipping

- **Coordinates are final.** Nothing reflows when the diagram is opened, so a
  label that is too long has a box that is too wide, permanently. Keep labels
  under about thirty characters and the page composes itself.
- **Edges are routed by draw.io, not by us.** Endpoints attach to shapes and
  `orthogonalEdgeStyle` finds a path. Two edges may run along the same
  corridor; opening the file and dragging one apart is a legitimate fix, and
  it is also the thing regeneration will undo.
- **`note` on a node is not drawn.** The layered builder has nowhere to put
  it. It survives as an XML comment at the top of the file. If the reader
  must see it, it belongs in the label.

## Compared with Mermaid

Better here: real tiers, exact placement, a file someone can rearrange.

Worse here: it does not render in a pull request. If the diagram's job is to
be read during review, Mermaid is the right format and this one is not.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost, but no draw.io has drawn it. Say so, and point at
draw.io or diagrams.net.
