# dfd in Mermaid

Read `../../_shared/types/dfd.md` first. This file only says what Mermaid
does with it.

**Renders as:** `flowchart TD` with `subgraph` frames. Coverage is **full**.

This is the one container type Mermaid carries completely, because a data
flow diagram needs exactly what a subgraph gives: a frame, and edges that
cross it.

## The trust boundary

A group with `kind: "trust"` gets a dashed red frame, applied with a
`classDef` after the graph:

```
classDef trust stroke:#B3261E,stroke-width:2px,stroke-dasharray: 6 4,fill:none
class sg_inside trust
```

Same colour, same dash, same meaning as draw.io. A reader who learns it on
one format reads the other without being told.

## What to know before shipping

- **Subgraph ids are prefixed `sg_`** so a group and a node may share a name
  in the intent without colliding in the output.
- **Edge labels carry the data**, and Mermaid puts them on the line. Keep
  them to two or three words or they collide with the frames they cross.
- `read` and `write` both render as arrows -- dotted for read, solid for
  write. The direction of the arrow is what says which.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
