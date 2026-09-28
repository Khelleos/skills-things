# dfd — data flow diagram

What data moves where, and where it crosses a boundary.

**Layout:** `container` — `payload` holds `nodes`, `edges` and `groups`.

## Shows

Data in motion. Every edge is a piece of data with a name, and every group is
a boundary that data crosses. The point of the diagram is the crossings.

## Does not show

- Control flow. An edge is what moves, not what calls what. If the labels are
  verbs, the type is `flowchart` or `architecture`.
- Timing or ordering. Edges are not numbered.
- Threats. Naming what could go wrong is `threat-model`, which is this type
  with the threats added.

## Fields

`nodes[]`

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | |
| `role` | yes | `process` (transforms data), `store` (holds it), `external` (outside), `actor` (a person) |
| `note` | no | one line |

`edges[]` — **label every one with the data**, not with the mechanism:
`decoded args`, not `over HTTP`.

| `kind` | Means |
|---|---|
| `flow` | data moves |
| `read` | a process reads a store |
| `write` | a process writes a store |

`groups[]` — the boundaries.

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | name what is trusted inside it |
| `members` | yes | node ids |
| `kind` | recommended | `trust` for a trust boundary, `group` for a plain grouping |

A `trust` group is drawn as a dashed red frame in both formats. That is the
one visual convention shared across every type in this toolchain, and it
exists so that a crossing is visible before any label is read.

## Limits

9 nodes, 12 edges, 4 groups.

## Reducing this type

- Two processes inside the same boundary doing the same thing to the same
  data are one process.
- A store only one process touches folds into that process (rung 3), unless
  the store is on the other side of a boundary.
- **Never drop an edge that crosses a boundary.** That is the diagram. Drop a
  node inside a boundary instead, or split by data flow.

## When a table is better

Rarely, for this type: a list of flows loses the boundaries, which is the
whole content. If the system has no boundary worth drawing, the type is
wrong, not the format.
