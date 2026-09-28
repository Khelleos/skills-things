# db-schema in Mermaid

Read `../../_shared/types/db-schema.md` first. This file only says what Mermaid
does with it.

**Renders as:** `erDiagram`. Coverage is **approximate**.

## What is lost

**Indexes have nowhere to go.** `erDiagram` has no notation for them at all.
They survive in a row's comment and in the prose, and a reader who skims the
diagram will not see them.

**A foreign key is marked on the column, but the relation line is drawn
separately** and the two are not tied together. With three foreign keys into
one table a reader has to work out which line is which.

**Table names become identifiers.** `celery_taskmeta` survives because it is
already one; `order line` would be drawn as `order_line`.

## What works

Columns, types, `PK`/`FK`/`UK` markers, cardinality, and optionality --
everything a join needs. For a schema whose question is "what joins to what",
this is enough.

## Say this before drawing

> Mermaid's ER has no notation for indexes, so they will be in the notes and
> not on the diagram. If the indexes are the point, draw.io shows them in the
> row and a table shows them better than either.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
