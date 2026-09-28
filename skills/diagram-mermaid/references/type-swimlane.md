# swimlane in Mermaid

Read `../../_shared/types/swimlane.md` first. This file only says what Mermaid
does with it.

**Renders as:** `flowchart TD` with one `subgraph` per lane. Coverage is
**approximate**.

## What is lost

**Lane direction is a request, not a rule.** The generator emits
`direction LR` inside every lane, and Mermaid honours it unreliably once
frames nest or once an edge crosses two lanes. The lanes will be there; which
way the steps run inside them is not guaranteed.

**A lane is a frame like any other frame.** Nothing marks it as belonging to
somebody. draw.io draws a real lane, with the name on the edge and the band
running the width of the page.

**Lane order is the declaration order in the intent**, and Mermaid respects
it for the frames themselves — that much does hold.

## What works

The handover, which is the point of the type: an arrow leaving one frame and
entering another is visible, and that is what a reader is looking for.

## Say this before drawing

> Mermaid draws lanes as frames and may not keep the steps running in the
> direction asked for. The handovers will be clear; the tidiness will not.
> draw.io draws real lanes.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
