# flowchart

The steps of one procedure and where it branches.

**Layout:** `layered` — `payload` holds `nodes` and `edges`.

## Shows

What happens, in order, with the decisions that change the path. One
procedure: a function, a request handler, an operator's checklist.

## Does not show

- Who does each step. Once that matters, the type is `swimlane`.
- Components — that is `architecture`. If the boxes are nouns rather than
  verbs, the type is wrong.
- Every guard clause. Early returns collapse into one `invalid input` branch
  unless they lead somewhere different.

## Fields

`nodes[]`

| Field | Required | Notes |
|---|---|---|
| `id` | yes | identifier |
| `label` | yes | a verb phrase: `Rotate token pair`, not `Rotation` |
| `role` | yes | `start`, `end`, `process`, `decision`, `io`, `subroutine` |
| `note` | no | one line |

`edges[]`

| Field | Required | Notes |
|---|---|---|
| `from`, `to` | yes | must name nodes in this diagram |
| `label` | required out of a `decision` | the branch condition: `yes`, `no`, `expired` |
| `kind` | no | only `flow` |

Every node in role `decision` must have at least two outgoing edges, and each
of them must carry a label. An unlabelled branch out of a decision is the
single most common way a flowchart becomes unreadable.

Use `subroutine` for a step that has its own diagram somewhere, and name that
diagram in `note`.

## Limits

9 steps, 12 edges.

## Reducing this type

- A run of steps with no branch between them is one step (rung 2). Name it
  for what the run achieves.
- Logging, metrics and cleanup steps go (rung 4), unless the procedure exists
  to produce them.
- Error paths that all end the same way join into one edge to one end node.
- Two decisions deep with four outcomes is usually two diagrams (rung 6).

## When a table is better

For a linear procedure with no branches at all, a numbered list is better
than a diagram in every way — shorter, diffable, and it reads aloud. Say so
before drawing.
