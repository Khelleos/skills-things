# db-schema

The tables as they exist in the database.

**Layout:** `table` — `payload` holds `entities` and `relations`.

## Shows

Real tables, real column types, real keys. Read from the migrations or from
the schema itself, never from the ORM models — the two disagree more often
than anyone expects, and the database is the one that is true.

## Does not show

- The domain. That is `data-model`, written from the code's models, in the
  domain's words. This type is the physical thing underneath it.
- Query plans, partitioning, replication. Those belong in prose.

## Fields

Same shape as `data-model`, used more literally.

`entities[]` — one per table. The `label` is the **table name as it is in the
database**: `celery_taskmeta`, not `Task result`.

`rows[]`

| Field | Required | Notes |
|---|---|---|
| `name` | yes | the column name, exactly |
| `type` | yes | the database type, with its size: `varchar(155)`, not `string` |
| `key` | no | `pk`, `fk`, `uk` |
| `note` | no | where an index lives, or a default worth knowing |

`relations[]` carry `cardinality` and `optional`, as in `data-model`. A
relation here should correspond to a real foreign key; if it does not, say so
in the label.

## Limits

8 tables, 12 relations, **15 rows** in any one table. The row limit is looser
than `data-model`'s twelve, because a real table legitimately carries more
columns than a domain object does.

## Reducing this type

- Audit columns go as a group and are named in the loss report (rung 1).
- A table nothing joins to may still belong — say why it is there.
- Past eight tables, split by subsystem rather than shrinking each table.
  Half a schema drawn honestly beats all of it drawn illegibly.

## What neither format draws

**Indexes have no shape in either format.** Put them in a row `note` and in
the prose. A schema diagram that silently omits the index everything depends
on has misled the reader about the most important thing on the page.

Foreign keys are marked on the column with `key: "fk"`, and the relation line
says which table it points at — but only draw.io shows both at once.

## When a table is better

Very often. `\d tablename` output, or a Markdown table per table, answers
"what columns does this have" better than any diagram. Draw this when the
joins are the question.
