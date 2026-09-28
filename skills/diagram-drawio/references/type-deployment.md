# deployment in draw.io

Read `../../_shared/types/deployment.md` first. This file only says what draw.io
does with it.

**Layout:** `container`. Coverage is **full**, and this is the format the
type was designed around.

## How it is placed

Every group is a real frame with a title bar, sized to its contents rather
than to a grid. Frames are ranked against each other by the edges that cross
between them, so a host that only receives traffic lands below the one that
sends it.

A group inside a group -- a container inside a VM -- nests properly: the
inner frame is a child cell with coordinates relative to the outer one, which
is what lets someone drag the whole host and keep its contents.

## Shapes

Frames come in three kinds, and the kind is visible without reading:

| `kind` | Drawn as |
|---|---|
| `node`, `system`, `group` | grey-titled frame |
| `lane` | white swimlane |
| `trust`, `boundary` | dashed red frame |

Inside, the usual vocabulary: cylinder for a store, parallelogram for a
queue, dashed grey for external.

## What to know before shipping

- **Four frames is the limit** and it is there because frames nest visually
  whether or not they nest logically -- five boxes of borders stops reading
  as structure.
- **Edges are routed by draw.io across frame walls.** They will cross a
  frame's border rather than going around it, which is correct and looks
  wrong until you expect it.
- A node in no group sits at the top level beside the frames, which is where
  an external system belongs.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
