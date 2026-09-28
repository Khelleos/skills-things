# deployment

Where the pieces actually run.

**Layout:** `container` — `payload` holds `nodes`, `edges` and `groups`.

## Shows

The machines, containers or managed services, and which process sits on
which. One group is one thing that can be restarted on its own.

## Does not show

- What the pieces do — that is `architecture`. If the reader could not tell
  this diagram from that one with the frames removed, draw `architecture`.
- Instance counts and versions, unless the count is the point. Three of a
  thing is one box labelled `API x3`.
- Networking detail: subnets, security groups, load balancer rules. Those
  change weekly and belong in the infrastructure code.

## Fields

`nodes[]` — a running process.

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | |
| `role` | recommended | `service`, `component`, `store`, `queue`, `external`, `actor`, `host` |
| `note` | no | one line; drawn in neither format, kept as a comment |

`groups[]` — a place things run.

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | name the machine, not the cloud region |
| `members` | yes | node ids. A node belongs to at most one group |
| `kind` | recommended | `node` for a host, `system` for a boundary you own |
| `parent` | no | a group inside a group: a container inside a VM |

`edges[]` as in `architecture`: `flow`, `request`, `response`, `async`,
`dep`, `trigger`.

## Limits

9 nodes, 12 edges, **4 groups**. Four hosts is where the frames stop helping
and start being a second diagram fighting the first.

## Reducing this type

- Identical hosts collapse into one labelled `x3` (rung 2).
- A group holding one node, where the host is not the point, becomes a bare
  node (rung 3).
- Sidecars — logging agents, metrics exporters, service mesh proxies — go as
  a group (rung 5). Say so; a reader may be looking for exactly those.
- More than four hosts is usually two diagrams: one per environment, or one
  per tier.

## When a table is better

When the question is "what runs where", a two-column table beats this
completely and stays correct as hosts are added. Draw the diagram when the
traffic between hosts is the point.
