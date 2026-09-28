# requirements

What the thing must do, and what shows that it does.

**Layout:** `table` — `payload` holds `entities` and `relations`.

**Read the last section first.** For this type, a table is usually the better
answer, and saying so is part of doing the job.

## Shows

Requirements, the things that satisfy or verify them, and the traces between.
Its value is entirely in the traces: a requirement nothing points at is a
requirement nobody has implemented, and that gap is what the diagram is for.

## Does not show

- The implementation. What satisfies a requirement is named, not described.
- Priority, status, owner, estimate. Those are columns, and columns belong in
  a table.
- Acceptance criteria in full. Neither format has room; they survive as
  comments and belong in the prose beside the diagram.

## Fields

`entities[]` — two kinds, told apart by `stereotype`.

| | `stereotype` | Means |
|---|---|---|
| a requirement | absent | something that must be true |
| an element | present | a test, a check, a module that bears on one |

| Field | Required | Notes |
|---|---|---|
| `id` | yes | |
| `label` | yes | the requirement, as one sentence: "Diagrams stay readable" |
| `rows` | yes | may be empty. Acceptance criteria, one per row |
| `stereotype` | for elements | `check`, `test`, `module` |

`relations[]`

| Field | Required | Notes |
|---|---|---|
| `from`, `to` | yes | read from `from` to `to` |
| `kind` | yes | `satisfies`, `verifies`, `derives`, `refines`, `traces` |
| `label` | no | why, when the kind alone is not enough |

Direction matters and is easy to get backwards: an element **satisfies** a
requirement, so `from` is the element. A requirement **derives** from another
requirement, so `from` is the derived one.

## Limits

8 entities, 12 relations, **8 rows** per entity.

## Reducing this type

- Requirements with the same element satisfying them and no separate trace
  are one requirement.
- Elements that verify nothing come out (rung 4) — and their absence is worth
  reporting, because it may mean a test nobody needs.
- Past eight entities, split by subsystem. Requirements diagrams grow without
  limit and stop being read at about a dozen boxes.

## When a table is better

**Almost always.** A four-column table — requirement, satisfied by, verified
by, status — carries more than the diagram, diffs cleanly, sorts, and is what
anyone actually needs to answer "is this covered".

Offer the table first, in the confirmation line, every time. Draw the diagram
only when the **shape** of the tracing is the question: a requirement with
three derived children, or one nothing reaches.
