# threat-model in draw.io

Read `../../_shared/types/threat-model.md` first. This file only says what draw.io
does with it.

**Layout:** `container`. Coverage is **full**.

## The convention

Unchanged from plan section 3 and identical to the Mermaid side:

- **trust boundary**: dashed red frame, label in the same red
- **solid arrow**: a request
- **dotted arrow**: a response
- a `threat` node is shaped differently from a process

Red appears nowhere else in the style vocabulary. That is what lets a reader
find the boundaries before reading a word.

## What to know before shipping

- **Threats sit inside the boundary they attack from**, which is what makes
  the direction of the arrow meaningful. A threat floating outside every
  frame says nothing about trust.
- **A threat node with no outgoing edge is a note**, not a threat. Point it
  at what it acts on or move it to the prose.
- **Mitigations are not drawn.** There is no shape for them and adding one
  would double the boxes. They belong in the table beside the diagram.
- The threats count against the nine blocks, which forces the diagram to be
  about the two or three that matter.

## Reading somebody else's threat model

If the source is a `.drawio` from elsewhere, unpack it with `drawio_read.py`.
Its labels come back flattened to one line and marked as data. Plan section
9 applies with particular force here: a threat model from outside is exactly
the document most likely to contain text written to be read by a machine.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
