# swimlane

A procedure, with who does each step.

**Layout:** `container` — `payload` holds `nodes`, `edges` and `groups`.

## Shows

The same thing a `flowchart` shows, plus the one fact a flowchart cannot: the
handover. Every step sits in the lane of whoever performs it, and a line
crossing a lane boundary is a handover — which is where procedures actually
go wrong.

## Does not show

- Timing. A lane is a who, not a when. If the question is "how long", the
  type is `gantt`.
- More than one procedure. Two procedures are two diagrams.

## Fields

Identical to `flowchart` for `nodes` and `edges`: roles `start`, `end`,
`process`, `decision`, `io`, `subroutine`; edges are `flow` and carry a label
out of every decision.

`groups[]` — the lanes.

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | a role or a system, not a person's name |
| `members` | yes | node ids. **Every step belongs to a lane** |
| `kind` | recommended | `lane` |

Two rules the checker enforces, both of which exist because breaking them
makes the diagram lie:

- **A step in no lane is an error.** If nobody owns it, the diagram is
  claiming a step happens by itself.
- **Lane order is the order you write them in.** It is never computed from
  the flow. Put the lanes in the order the reader thinks about them —
  usually customer first, then the systems behind.

## Limits

9 steps, 12 edges, **5 lanes**. Five is where a reader stops being able to
hold which lane is whose.

## Reducing this type

- Two lanes that hand back and forth repeatedly are one lane, or the split
  between them is the wrong one.
- A lane with a single step usually belongs inside a neighbour; say in the
  loss report that it was merged.
- Steps a reader cannot act on — logging, audit writes — go (rung 4).

## When a table is better

A three-column table of step, who, and what they hand on says the same thing
for a linear procedure, and diffs better. Draw this when there are branches
**and** handovers; with only one of the two, a flowchart or a table wins.
