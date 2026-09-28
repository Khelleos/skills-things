# user-journey in Mermaid

Read `../../_shared/types/user-journey.md` first. This file only says what Mermaid
does with it.

**Renders as:** `journey`. Coverage is **full**.

## Scores are required

A journey step is `label: score: actor`, and the score is not optional. A
span without one is refused:

> a journey step is a score out of five, and <id> has none. Give every span a
> 'score', or drop the diagram: without the scores it says nothing a numbered
> list would not say better.

That is the type's own rule enforced by the format that happens to agree with
it.

## How the type maps

| In `graph.json` | In Mermaid |
|---|---|
| track | `section <label>` |
| span `label` | the step |
| span `score` | the number, 0 to 5 |
| span `note` | the actor drawn beside the step; defaults to `User` |

## What to know before shipping

- **Mermaid draws the scores as a line**, which is what makes the dip
  visible. That line is the diagram; everything else is labels.
- **Order is the order of the spans**, by `start` along the axis.
- The actor column is one word in practice. `Writer`, `Reviewer`, `On-call`.
  A sentence there crowds the step out.
- draw.io draws the score as a colour on the bar rather than as a line. Both
  are honest; the line reads faster.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
