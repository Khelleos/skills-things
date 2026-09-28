# gantt

What happens when, and what waits for what.

**Layout:** `timeline` — `payload` holds `tracks` and `spans`.

## Shows

Work over time, grouped into streams, with the dependencies that force the
order. Useful in technical documentation for exactly two things: a migration
with a cutover, and a deprecation with a removal date.

## Does not show

- Effort or cost. A bar's length is elapsed time, not work.
- Who is doing it. If that is the question, the type is `swimlane`.
- Anything beyond a horizon a reader believes. A twelve-month bar is a
  statement of intent drawn as a fact.

## Fields

`tracks[]` — the streams. Each is a section on the page.

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | the stream: a workstream, a team, a subsystem |

`spans[]`

| Field | Required | Notes |
|---|---|---|
| `id`, `track`, `label` | yes | |
| `start` | yes | `YYYY-MM-DD` |
| `end` | for a task | omit it and the span is a point in time |
| `kind` | recommended | `task` or `milestone` |
| `depends_on` | no | span ids this one waits for; the checker rejects a cycle |

**Dates, not ordinals.** draw.io will draw whatever it is given, but Mermaid's
gantt understands only real dates and the generator refuses rather than
inventing them. If the thing being drawn has no dates, it is not a Gantt.

Two spans overlapping in time on one track is ordinary — two things running
at once — and they are drawn on separate rows within the track.

## Limits

**5 tracks, 15 spans.** Looser than the general 9 because a bar carries far
less than a box does; tighter on tracks because a reader tracks five streams
and no more.

## Reducing this type

- Spans shorter than the axis can show collapse into the one they belong to.
- A track with one span belongs in a neighbouring track.
- Split by phase before shrinking: "migration, up to cutover" and "migration,
  after cutover" are two readable diagrams where one is not.

## When a table is better

Very often. A table of what, when, and what it waits for carries the same
information, stays correct when a date slips, and does not imply a precision
the plan does not have. Offer it first unless the dependencies form a shape
worth seeing.
