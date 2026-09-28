# sequence in Mermaid

Read `../../_shared/types/sequence.md` first. This file only says what
Mermaid does with it.

**Renders as:** `sequenceDiagram`, with `autonumber`. Coverage is **full**.

`autonumber` is always on. Numbered steps are what lets the prose next to the
diagram say "at step 4" instead of describing the picture.

## How the type maps

| In `graph.json` | In Mermaid |
|---|---|
| actor, kind `actor` | `actor id as Label` — a stick figure |
| actor, any other kind | `participant id as Label` — a box |
| message, kind `request` | `from->>to: text` solid arrow |
| message, kind `response` | `from-->>to: text` dashed arrow |
| message, kind `async` | `from-)to: text` open arrowhead |
| message, kind `self` | `from->>from: text`, drawn as a loop |
| message, kind `create` | `create participant to as Label`, then the arrow |
| message, kind `destroy` | `destroy to`, then a `--x` arrow |
| message `note` | `Note over from,to: text` |
| fragment | `alt` / `opt` / `loop` / `par` … `end` around the range |

`store`, `external` and `boundary` all render as plain participants: Mermaid
has one box and one stick figure, and nothing else. The distinction survives
in `graph.json` and is drawn properly by draw.io.

## What to know before shipping

- **A participant created mid-diagram is not declared at the top.** The
  generator handles this: an actor that is the target of a `create` message
  is left out of the opening declarations, or Mermaid would draw it standing
  there from the first frame.
- **`alt` renders with no `else` arm.** The type carries one branch per
  fragment by design. If the diagram needs both arms, it needs two diagrams.
- **Order in the list is order on the page**, with no exception. There is no
  timestamp field and there will not be one.
- **A label is drawn centred on its own arrow, with nothing behind it.** The
  lifelines the arrow spans are dashed vertical lines that run straight
  through the text, so a message between distant columns comes out with its
  label struck through two or three times. Mermaid offers no way to give the
  label a background. The fix is the actor order, and `validate_graph.py`
  flags any message crossing two or more lifelines.
- Message text runs to the end of the line, so it cannot contain a newline.
  Long text is clipped at 120 characters; well before that it is unreadable.
- Activation bars are not generated. They add a second thing to track for a
  reader who already has the arrow.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
