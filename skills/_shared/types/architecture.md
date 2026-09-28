# architecture

The running pieces of a system and what talks to what.

**Layout:** `layered` — `payload` holds `nodes` and `edges`.

## Shows

Services, the stores they own, the queues between them, and who calls whom.
One box is one thing that can fail on its own.

## Does not show

- Where the boxes run — that is `deployment`.
- The order calls happen in — that is `sequence`.
- The shape of the data — that is `data-model`.
- Anything a reader cannot act on: version numbers, instance counts, ports,
  unless `audience` is `engineer` and the number is the point.

## Fields

`nodes[]`

| Field | Required | Notes |
|---|---|---|
| `id` | yes | identifier, unique in the diagram |
| `label` | yes | what the reader sees |
| `role` | recommended | `service`, `component`, `store`, `queue`, `external`, `actor` |
| `tier` | no | integer, 0 nearest the user. Only orders the declarations |
| `note` | no | one line, rendered as a comment, not as a box |

`edges[]`

| Field | Required | Notes |
|---|---|---|
| `from`, `to` | yes | must name nodes in this diagram |
| `label` | no | what crosses the line, not how it is transported |
| `kind` | recommended | `flow`, `request`, `response`, `async`, `dep`, `trigger` |

Pick `role` by what the box *is*, never by what shape you want it to have.
The shape is a consequence, and both formats pick it from the role.

## Limits

9 nodes, 12 edges. There is no per-type extra limit.

## Reducing this type

The ladder in `budget.py` applies in full. What it usually means here:

- Replicas collapse into one box (rung 2). Three API instances are `API x3`.
- A store only one service reads collapses into that service (rung 3).
- Metrics, logs and tracing sinks go (rung 4), and the loss report says so.
- Every external system the diagram does not actually explain goes (rung 5).

## When a table is better

When the answer is "which service owns which store" and nothing calls
anything, a two-column table says it faster and stays right longer.

## Worked example

```json
{
  "type": "architecture",
  "layout": "layered",
  "meta": {
    "title": "Token refresh path",
    "scope": "src/auth",
    "detail": "normal",
    "audience": "engineer",
    "dropped": [{ "what": "logging", "why": "cross-cutting infrastructure, rung 5" }],
    "budget_override": null
  },
  "payload": {
    "nodes": [
      { "id": "browser", "label": "Browser", "role": "actor", "tier": 0 },
      { "id": "auth", "label": "Auth service", "role": "service", "tier": 1 },
      { "id": "tokens", "label": "Token store", "role": "store", "tier": 2 }
    ],
    "edges": [
      { "from": "browser", "to": "auth", "label": "POST /refresh", "kind": "request" },
      { "from": "auth", "to": "tokens", "label": "read + rotate", "kind": "flow" }
    ]
  }
}
```
