# data-model in Mermaid

Read `../../_shared/types/data-model.md` first. This file only says what
Mermaid does with it.

**Renders as:** `erDiagram`. Coverage is **full** for `data-model`.

## How the type maps

| In `graph.json` | In Mermaid |
|---|---|
| entity | a named block with its rows between braces |
| row | `type name KEY "note"` |
| `key: "pk"` / `"fk"` / `"uk"` | `PK` / `FK` / `UK` after the name |
| relation | `A ||--o{ B : "label"` |

## Cardinality

`cardinality` and `optional` together choose the connector:

| `cardinality` | `optional: false` | `optional: true` |
|---|---|---|
| `1-1` | `\|\|--\|\|` | `\|\|--o\|` |
| `1-n` | `\|\|--\|{` | `\|\|--o{` |
| `n-1` | `}\|--\|\|` | `}o--o\|` |
| `n-n` | `}\|--\|{` | `}o--o{` |

`optional: true` means the far side may be absent — zero-or-one instead of
one, zero-or-more instead of one-or-more. It is the difference between "every
account has a session" and "an account may have sessions", which is usually
the thing a reader actually wants to know.

## Two things Mermaid forces

**Entity names become identifiers.** Mermaid names an ER block with a bare
token, so `Refresh token` is drawn as `Refresh_token`. The generator does the
conversion and disambiguates a collision with a numeric suffix. Nothing can
be done about this in Mermaid; draw.io draws the label as written.

**Every row needs a type.** `erDiagram` has no syntax for a bare attribute
name. A row with no `type` is drawn as `unknown name`, and `validate_graph.py`
warns about each one before it gets that far. Fill the types in.

## What to know before shipping

- Relations are emitted before the entity blocks, which is what Mermaid's own
  examples do and what keeps the diff readable when a row is added.
- The `label` on a relation is required by the syntax. An empty one renders
  as an empty pair of quotes, which looks like a mistake — give every
  relation a verb.
- Row order is preserved, so put the key first and the rest in the order a
  reader would ask about them.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
