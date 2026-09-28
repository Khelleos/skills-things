# requirements in Mermaid

Read `../../_shared/types/requirements.md` first. This file only says what Mermaid
does with it.

**Renders as:** `requirementDiagram`. Coverage is **approximate**.

Before anything else: the type file says a table is almost always better
here, and that is not a formality. Offer it in the confirmation line.

## How the type maps

| In `graph.json` | In Mermaid |
|---|---|
| entity with no `stereotype` | `requirement <name> { id, text, risk, verifymethod }` |
| entity with a `stereotype` | `element <name> { type }` |
| `label` | the `text:` field -- a sentence, which is what this type needs |
| relation | `<from> - <kind> -> <to>` |
| `rows` | **not drawn.** Kept as `%%` comments |

## What is lost

**Acceptance criteria.** A requirement block has four fixed fields and no
room underneath. The rows survive as comments and belong in the prose.

**Risk and verification method are invented.** The generator writes
`risk: medium` and `verifymethod: inspection` because the syntax demands
both and `graph.json` carries neither. Say so if a reader might take them
seriously -- they are placeholders, not judgements.

**The type itself is thin.** `requirementDiagram` is among the least used
Mermaid diagrams and its layout shows it: boxes of very different sizes, and
relation labels that collide past about six entities.

## Say this before drawing

> A four-column table -- requirement, satisfied by, verified by, status --
> carries more than this diagram and sorts. The diagram is worth it only if
> the shape of the tracing is the question.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
