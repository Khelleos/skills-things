# sequence in draw.io

Read `../../_shared/types/sequence.md` first. This file only says what
draw.io does with it.

**Layout:** `lifeline`. Coverage is **full**.

## How the type is placed

Each actor becomes one `umlLifeline` shape: the head box and the dashed line
below it are a single object, sized to reach the last message. Columns are
laid left to right in the order the actors are listed, so **the list order is
the column order**, exactly as in Mermaid.

Messages are placed at computed heights and drawn as free-floating edges with
explicit endpoints, rather than as edges attached to the lifelines. That is
deliberate: attaching them would let draw.io re-route on open and slide a
message off its row.

The consequence is worth knowing: **moving a lifeline by hand does not move
its messages.** Regenerating is the way to change the layout, and
regenerating throws away every other hand edit.

## Shapes and arrows

| `kind` | Drawn as |
|---|---|
| `request` | solid line, filled arrowhead |
| `response` | dashed line, open arrowhead |
| `async` | solid line, open arrowhead |
| `self` | out, down and back, as a three-point loop |
| `create` | dashed line, filled arrowhead |
| `destroy` | line with a cross at the end |

`store`, `external` and `boundary` actors are drawn as ordinary lifelines.
draw.io could distinguish them and does not here, because the distinction
belongs to the intent and adding a shape per actor kind would be a second
vocabulary for a reader to learn.

A message `note` becomes a real note shape pinned beside it, in pale yellow.
This is a place draw.io beats Mermaid: the note is an object with a position
rather than text spanning two lifelines.

Fragments — `alt`, `opt`, `loop`, `par` — become a `umlFrame` around the
messages they cover, tagged with the kind and the condition.

## What to know before shipping

- **A self-message needs vertical room**, and the layout gives it more than a
  plain message. Several in a row make a tall diagram; that is the diagram
  telling you the actor is doing too much on its own.
- **The lifelines all end at the same depth**, computed from the last
  message. A `destroy` does not shorten the line — the cross marks the end
  and the line continues. Mermaid draws this properly; here it does not.
- **Ordering still matters most.** A message drawn between distant columns
  puts its label over the lifelines it crosses, exactly as in Mermaid, and
  `validate_graph.py` warns at two crossings in both formats.

## Compared with Mermaid

Better here: real note objects, real frames, exact placement.

Worse here: no lifeline termination on `destroy`, no auto-numbered steps, and
no rendering in a pull request.

## Not checked by anything

Whether it looks right. Say so.
