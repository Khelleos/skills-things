# requirements in draw.io

Read `../../_shared/types/requirements.md` first. This file only says what draw.io
does with it.

**Layout:** `table`. Coverage is **full**, and better than Mermaid.

Before anything else: the type file says a table is almost always better, and
that holds regardless of format. Offer it in the confirmation line.

## What draw.io carries that Mermaid does not

**The acceptance criteria.** Each requirement is a swimlane with its rows
drawn underneath it -- which is exactly where the criteria belong. Mermaid's
`requirementDiagram` has four fixed fields and no room for them, so it keeps
them as comments.

**Nothing is invented.** Mermaid's syntax demands `risk` and `verifymethod`,
so the generator writes placeholders there. Here there is no such field and
nothing is filled in on the reader's behalf.

## How it is placed

One swimlane per entity: the label in the title bar, criteria as rows. An
entity with a `stereotype` shows it above the name as `<<check>>`.

Relations use the UML-ish arrows already in the class vocabulary -- a dashed
open arrow for every requirement relation, with the kind named in the label,
because `satisfies` and `verifies` have no distinct notation anyone would
recognise.

## What to know before shipping

- **Eight entities, eight rows each.** Requirements diagrams grow without
  limit; this is the type most likely to be over budget on the first attempt.
- **Direction is easy to get backwards**: an element satisfies a requirement,
  so `from` is the element. The arrowhead lands on the requirement.
- A requirement nothing points at is the finding the diagram exists to
  produce. Do not quietly drop it to fit the budget -- drop a satisfied one
  instead, and say so.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
