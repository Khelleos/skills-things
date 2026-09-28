# sequence

One run through the system, in the order it happens.

**Layout:** `lifeline` — `payload` holds `actors`, `messages`, and optionally
`fragments`.

## Shows

Who sends what to whom, in order, for **one** scenario. The happy path, or
one named failure, never both at once in the same diagram.

## Does not show

- Every branch. A sequence diagram that tries to cover all cases stops being
  readable at about the third `alt`. Draw the main run; draw a second diagram
  for the failure that matters.
- Static structure — that is `architecture`.
- Retries and timeouts unless the retry *is* the thing being explained.

## Fields

`actors[]`

| Field | Required | Notes |
|---|---|---|
| `id` | yes | identifier |
| `label` | yes | what the reader sees |
| `kind` | recommended | `actor` (a person), `participant`, `store`, `external`, `boundary` |
| `note` | no | one line |

`messages[]` — order in the list **is** the order in time.

| Field | Required | Notes |
|---|---|---|
| `from`, `to` | yes | must name actors in this diagram |
| `label` | yes | the call, not the transport: `POST /refresh`, not `HTTPS` |
| `kind` | recommended | `request`, `response`, `async`, `self`, `create`, `destroy` |
| `note` | no | drawn as a note over the two lifelines |

`fragments[]` — optional, at most one or two.

| Field | Required | Notes |
|---|---|---|
| `kind` | yes | `alt`, `opt`, `loop`, `par` |
| `label` | yes | the condition, in the reader's words |
| `start`, `end` | yes | inclusive indices into `messages` |

**Order the actors so the pairs that talk sit next to each other.** The list
order is the column order on the page, and a message drawn between distant
columns puts its label on top of every lifeline it spans. Two crossed
lifelines is where the label stops being readable, and the checker says so.

Pipeline order is the obvious first guess and often the wrong one: a store
that both the first and the last actor touch belongs beside whichever of them
touches it twice, not at the end of the pipeline.

`kind: "self"` requires `from` and `to` to be the same actor; the checker
enforces it. `create` brings a lifeline into being at that message, and
`destroy` ends it — use them only when the birth or death is the point.

## Limits

6 lifelines, 12 messages. Six columns is where a sequence diagram stops
fitting on a screen, so this limit is tighter than the general 9.

## Reducing this type

- Collapse a request/response pair into one labelled request when the reply
  is uninteresting (`200 OK` is uninteresting).
- A store that is read once collapses into the service that reads it.
- Drop the caller's caller. Start at the boundary the reader cares about.
- Two scenarios in one diagram is the signal to split (rung 6).

## When a table is better

Never, really — ordering is exactly what a table cannot show. If order does
not matter, the diagram is the wrong type, not the wrong format.
