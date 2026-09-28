# flowchart in Mermaid

Read `../../_shared/types/flowchart.md` first. This file only says what
Mermaid does with it.

**Renders as:** `flowchart TD`. Coverage is **full**.

## How roles become shapes

| `role` | Mermaid | Reads as |
|---|---|---|
| `start`, `end` | `id(["..."])` | a stadium, the way in and the way out |
| `process` | `id["..."]` | a rectangle, a step |
| `decision` | `id{"..."}` | a rhombus, a question |
| `io` | `id[/"..."/]` | a parallelogram, something read or written |
| `subroutine` | `id[["..."]]` | a boxed box, a step drawn elsewhere |

`start` and `end` share a shape on purpose: the reader tells them apart by
where the arrows point, and giving them different shapes adds a rule to
remember for nothing.

## Edges

Only `kind: "flow"` applies, so every edge is `-->`. Branch labels ride in
pipes: `valid -->|"yes"| rotate`.

Label the branches with the condition's answer, not with the condition:
`yes` / `no` out of `Signature valid?`, never `Signature valid` on one arm.

## What to know before shipping

- **Top-down only.** The generator emits `TD`. Mermaid supports `LR`, but a
  procedure read left to right stops fitting on a page at about five steps,
  and mixing directions across diagrams costs the reader more than it saves.
- **Mermaid decides where the branches go.** A `yes` arm may come out on the
  left in one render and the right in another as the graph changes. Never
  write prose that says "the left branch".
- **`end` as a node id breaks the diagram** — the generator renames it. This
  bites hardest here, because `end` is the obvious id for the final node.
- Loops back to an earlier step render fine, but Mermaid will route the line
  around the outside; two of them and the diagram is worth splitting.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
