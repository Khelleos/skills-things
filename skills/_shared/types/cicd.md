# cicd

What happens between a push and a release.

**Layout:** `layered` — `payload` holds `nodes` and `edges`.

## Shows

The stages a change passes through, what gates it, and what comes out. Read
from the pipeline definition, not from what the team believes the pipeline
does — those diverge, and the file is the one that runs.

## Does not show

- Every job in a matrix. Five Python versions are one box, `Unit tests x5`.
- The contents of a job. A job is a box; what it runs is prose or its own
  `flowchart`.
- Timing. If the question is how long each stage takes, that is a `gantt`.

## Fields

`nodes[]`

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | |
| `role` | yes | `start`, `end`, `job`, `gate`, `artifact`, `environment` |
| `tier` | no | pins a stage to a row, which is usually worth doing here |
| `note` | no | the workflow file it comes from |

The roles carry the whole grammar of a pipeline:

- `start` — what triggers it: a push, a tag, a schedule.
- `job` — something that runs and can fail.
- `gate` — a decision: approval, a branch condition, all-green. Needs at
  least two labelled ways out.
- `artifact` — a thing produced that outlives the job: an image, a wheel.
- `environment` — somewhere it is deployed to.
- `end` — the pipeline succeeded.

`edges[]`

| `kind` | Means |
|---|---|
| `trigger` | the first thing starts this, drawn thick |
| `flow` | ordinary succession |

## Limits

9 nodes, 12 edges.

## Reducing this type

- Parallel jobs that always succeed together are one box (rung 2).
- Notification and reporting steps go (rung 4). They never change the path.
- Caching, artifact upload and download are infrastructure (rung 5) unless
  the cache is what the reader is debugging.
- One pipeline per diagram. Pull-request and release pipelines are two
  diagrams even when they share jobs.

## When a table is better

For a linear pipeline with no gates, a numbered list of stages is better.
The diagram earns its place when there are gates, parallel paths, or a loop
back to the start after a failure.
