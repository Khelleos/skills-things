# user-journey

The steps somebody goes through, and how each one feels.

**Layout:** `timeline` — `payload` holds `tracks` and `spans`.

## Shows

One person's path through a system, in order, with a score out of five on
each step. The score is the whole point: without it this is a numbered list
drawn expensively.

In technical documentation the useful journey is rarely a customer's. It is
the developer's: installing the thing, getting the first result, debugging
the first failure. That journey is where documentation gaps show up as low
scores.

## Does not show

- What the system does internally. That is `sequence`.
- Branches. A journey is one path. The unhappy path is a second journey.
- Time. Steps are ordered, not timed.

## Fields

`tracks[]` — the phases, in order.

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | a phase: `Discover`, `Set up`, `First run` |

`spans[]` — the steps.

| Field | Required | Notes |
|---|---|---|
| `id`, `track`, `label` | yes | the label is what the person does, in their words |
| `start` | yes | the step's position: `1`, `2`, `3` … |
| `score` | **yes** | 0 to 5. Only this type accepts it, and the generator refuses without it |
| `kind` | recommended | `step` |
| `note` | no | who is doing it. Mermaid draws this as the actor |

A score is a claim about somebody else's experience. Take it from something —
a support ticket, a session watched, a complaint — and say in the loss report
where it came from. A score invented to make the chart look interesting is
the worst thing in this whole toolchain.

## Limits

5 tracks, 15 spans.

## Reducing this type

- Steps scoring the same as their neighbours and requiring no separate action
  merge into one.
- Phases with one step each mean the phases are wrong, not that the steps are.
- A journey longer than about a dozen steps is two journeys with a boundary
  in between — usually the point where the person either succeeds or leaves.

## When a table is better

When there are no scores, always: the diagram then carries nothing a list
does not. With scores, the diagram wins, because the shape of the dip is what
a reader takes away and a column of numbers is not.
