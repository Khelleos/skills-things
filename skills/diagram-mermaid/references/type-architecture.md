# architecture in Mermaid

Read `../../_shared/types/architecture.md` first — it decides what goes in
the diagram. This file only says what Mermaid does with it.

**Renders as:** `flowchart TD`. Coverage is **full**: nothing in the type is
lost in this format.

## How roles become shapes

| `role` | Mermaid | Reads as |
|---|---|---|
| `service` | `id["..."]` | a rectangle, the default thing |
| `component` | `id("...")` | rounded, a part inside something |
| `store` | `id[("...")]` | a cylinder, state that outlives a request |
| `queue` | `id[/"..."/]` | a parallelogram, data in motion |
| `external` | `id{{"..."}}` | a hexagon, not ours |
| `actor` | `id(("..."))` | a circle, a person |

## How edge kinds become arrows

| `kind` | Mermaid | Reads as |
|---|---|---|
| `flow`, `request` | `-->` | the ordinary case |
| `response`, `dep` | `-.->` | dotted: a reply, or a dependency rather than traffic |
| `async` | `--o` | sent, no reply awaited |
| `trigger` | `==>` | thick: this causes the other thing to run |

Mermaid has four arrow endings and this spends all four. `response` and `dep`
share the dotted arrow: they do not co-occur in practice, because one is a
runtime pairing and the other is a static relation. If a diagram needs both
at once, that diagram is doing two jobs and should be split.

## What to know before shipping

- **Mermaid lays the graph out, not us.** `tier` orders the declarations,
  which nudges the result, and that is all it does. Do not promise a reader
  that the top row is the edge of the system.
- **Long labels widen boxes** and push the whole diagram sideways. The
  120-character clip in `escape.py` is a backstop, not a target — over about
  30 characters, shorten the label instead.
- **`end` as a node id breaks the diagram.** The generator appends an
  underscore to it and to a dozen other reserved words automatically.
- Labels are quoted and entity-escaped, so brackets, quotes and pipes inside
  a label are safe.
- `note` on a node becomes a `%%` comment, not a drawn note: `flowchart` has
  no note syntax. To have it drawn, make it part of the label.

## Not checked by anything

Mermaid's own grammar. Say so in the answer: the syntax is correct by
construction, but no renderer has seen this file. Point the reader at the
GitHub preview.
