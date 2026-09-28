# threat-model

Where data crosses a boundary, and what could go wrong there.

**Layout:** `container` — `payload` holds `nodes`, `edges` and `groups`.

This is `dfd` with the threats drawn in. If there are no threats to name, the
type is `dfd` and this one is pretending.

## Shows

The flows, the trust boundaries, and the specific things that could happen at
the crossings. A threat is attached to the place it acts on, not floated in a
corner.

## Does not show

- Mitigations. What is already done about a threat is prose, or a column in
  the table that accompanies the diagram. Drawing both doubles the boxes and
  halves the legibility.
- Severity or likelihood. Those are numbers and belong in the table.
- Threats to things outside the scope. A diagram naming every threat to the
  cloud provider is a diagram nobody will act on.

## Fields

`nodes[]`

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | a threat's label names the thing that happens |
| `role` | yes | `process`, `store`, `external`, `actor`, `threat` |
| `note` | no | the control that currently applies, if any |

`edges[]` — `flow`, `request`, `response`. An edge **from** a `threat` node
points at what it acts on.

`groups[]` — at least one with `kind: "trust"`. A threat model with no trust
boundary has not said where trust changes, which is the only thing that makes
it a threat model.

## The convention, fixed for both formats

- A trust boundary is a **dashed red frame**.
- A solid arrow is a request; a dotted arrow is a response.
- A threat node is drawn differently from a process, and sits inside the
  boundary it attacks from.

This is the one ready-made convention the research turned up, and it is kept
unchanged so that a reader who has seen one threat model elsewhere reads this
one without a legend.

## Limits

9 nodes, 12 edges, 4 groups. Threats count towards the nine — which forces
the diagram to be about the two or three threats that matter.

## Reducing this type

- Threats sharing a cause collapse into one: five injection points are one
  `Unvalidated input` threat pointing at the one boundary.
- The flows that carry no threat go (rung 4). This diagram is not a complete
  data flow and should not pretend to be.
- More than three threats is a table with a diagram beside it, not a bigger
  diagram.

## When a table is better

A STRIDE table — threat, where, impact, mitigation — carries more and stays
current. The diagram's job is to show **where the boundary is**; the table's
job is everything else. Offer both, and say which is which.
