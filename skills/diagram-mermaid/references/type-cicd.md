# cicd in Mermaid

Read `../../_shared/types/cicd.md` first. This file only says what Mermaid
does with it.

**Renders as:** `flowchart TD`. Coverage is **full**.

## How roles become shapes

| `role` | Mermaid | Reads as |
|---|---|---|
| `start`, `end` | `([...])` | the trigger and the finish |
| `job` | `[...]` | something that runs and can fail |
| `gate` | `{...}` | a decision, in the same yellow rhombus every type uses |
| `artifact` | `[(...)]` | a cylinder: a thing produced that outlives the job |
| `environment` | `[[...]]` | a boxed box: somewhere it is deployed |

`trigger` edges are drawn thick (`==>`), which is the one place in this
toolchain a thick arrow is used. It marks the outside event that starts
everything.

## What to know before shipping

- **A failure loop back to the start renders as a long arc** around the
  outside. One is fine and reads well; two means the pipeline has two failure
  paths and probably wants splitting by trigger.
- **`gate` needs at least two labelled ways out**, and the checker says so.
  An unlabelled gate is the commonest defect in a pipeline diagram.
- Declaration order follows `tier`, so pinning the stages gives Mermaid a
  strong hint about the rows even though it lays out for itself.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
