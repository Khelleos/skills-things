# data-model

The entities the system stores and how they relate.

**Layout:** `table` — `payload` holds `entities` and `relations`.

## Shows

The domain shape: what is stored, what identifies it, what points at what.
Written from the code's models, not from the database.

## Does not show

- Indexes, constraints, storage types, nullability. That is `db-schema`.
- Behaviour. Methods belong to `class`.
- Every column. A model with forty columns shows the six that carry meaning,
  and the loss report says the rest were left out.

## Fields

`entities[]`

| Field | Required | Notes |
|---|---|---|
| `id` | yes | identifier |
| `label` | yes | singular, in the domain's words: `Refresh token` |
| `rows` | yes | may be empty when the entity is only a reference |
| `note` | no | one line |

`rows[]`

| Field | Required | Notes |
|---|---|---|
| `name` | yes | the attribute |
| `type` | strongly recommended | Mermaid ER has no form without a type and prints `unknown` |
| `key` | no | `pk`, `fk`, `uk` |
| `note` | no | short, becomes a comment on the row |

`relations[]`

| Field | Required | Notes |
|---|---|---|
| `from`, `to` | yes | must name entities in this diagram |
| `cardinality` | yes | `1-1`, `1-n`, `n-1`, `n-n` |
| `optional` | no | `true` when the far side may be absent: zero-or-one, zero-or-more |
| `label` | recommended | the verb, read from `from` to `to`: `opens`, `rotates` |

`kind` is not accepted here — that field belongs to `class` and
`requirements`. The checker rejects the mix rather than guessing.

## Limits

8 entities, 12 relations, 12 rows in any one entity.

## Reducing this type

- Join tables for a many-to-many disappear into an `n-n` relation (rung 3).
- Audit columns — `created_at`, `updated_at`, `created_by` — go as a group
  (rung 1) unless the diagram is about auditing.
- An entity that only ever hangs off one other and is never queried on its
  own folds into it.

## When a table is better

When the question is "what columns does this have", a Markdown table of the
one entity answers it completely and stays diffable. Draw the diagram when
the question is about relations.
