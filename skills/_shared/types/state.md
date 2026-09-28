# state

The states one thing can be in, and what moves it between them.

**Layout:** `layered` — `payload` holds `nodes` and `edges`.

## Shows

The lifecycle of a single entity: an order, a session, a job, a connection.
Every edge is an event that causes the move, and the label is that event.

## Does not show

- What the system does while in a state. A state is a condition, not a step.
  If the boxes read like actions, the type is `flowchart`.
- More than one entity. Two lifecycles are two diagrams.

## Fields

`nodes[]`

| Field | Required | Notes |
|---|---|---|
| `id` | yes | identifier |
| `label` | yes | an adjective or a condition: `Active`, `Awaiting payment` |
| `role` | yes | `state`, `start`, `end`, `choice` |
| `note` | no | one line, drawn beside the state |

`edges[]`

| Field | Required | Notes |
|---|---|---|
| `from`, `to` | yes | must name nodes in this diagram |
| `label` | recommended | the event, in the past or imperative: `payment cleared` |
| `kind` | no | only `transition` |

Exactly one node in role `start`. Usually one in role `end`; a lifecycle
with no end (a long-running session) may legitimately have none, and the
checker only warns.

Both `start` and `end` are markers, not states. Give them a short `label`
anyway — draw.io draws it and Mermaid ignores it.

## Limits

9 states, 12 transitions.

## Reducing this type

- Merge states nothing distinguishes for the reader: `Queued` and
  `Scheduled` are one state unless something acts on the difference.
- Error states collapse into one `Failed` unless recovery differs per cause.
- Do **not** drop transitions to make the count fit. A missing transition is
  a lie about the machine; drop a state instead, or split (rung 6).

## When a table is better

A transition table — from, event, to, guard — beats a diagram once there are
more than about a dozen transitions, and is the honest answer when the
machine is dense rather than shapely. Offer it before drawing.
