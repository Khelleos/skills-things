# state in Mermaid

Read `../../_shared/types/state.md` first. This file only says what Mermaid
does with it.

**Renders as:** `stateDiagram-v2`. Coverage is **full**.

Never emit the old `stateDiagram`. The `-v2` renderer is the one GitHub uses
and the one the layout rules below describe.

## How the type maps

| In `graph.json` | In Mermaid |
|---|---|
| node, role `state` | `state "Label" as id`, or bare `id` when they match |
| node, role `start` | `[*]`, as the source of its edge |
| node, role `end` | `[*]`, as the target of its edge |
| node, role `choice` | `state id <<choice>>` |
| edge | `from --> to : event` |
| node `note` | a real `note right of id` block |

Both `start` and `end` collapse onto the same `[*]` marker — Mermaid tells
them apart by direction, exactly as a reader does. Their `label` is not
rendered here; draw.io does draw it, which is why the type still asks for one.

## Edges

Only `kind: "transition"` applies, so every edge is `-->`. The event goes
after a colon: `active --> stale : access token expires`.

## What to know before shipping

- **This is the one wave-1 type with a real note.** Use it: a state that
  needs a sentence of explanation gets one, and the note does not count
  against the block budget.
- **Composite states are not generated.** Mermaid supports nesting a machine
  inside a state; `graph.json` has no field for it, deliberately — a nested
  machine is a second diagram. If the code really has one, draw the outer
  machine and link to the inner one from the prose.
- **Layout is Mermaid's.** A cycle between three states may render as a
  triangle or as a line with a long return arc. Do not describe the picture
  in the prose; describe the machine.
- `choice` renders as a small diamond with no label. Put the question on the
  incoming edge, and the answers on the outgoing ones.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
