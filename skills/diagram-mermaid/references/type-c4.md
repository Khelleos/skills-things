# c4 in Mermaid

Read `../../_shared/types/c4.md` first. This file only says what Mermaid
does with it.

**Renders as:** `flowchart TD` with `subgraph` frames. Coverage is **full at
levels 1 and 2**, **approximate at 3 and 4**.

**The `C4Context` family of Mermaid diagrams is not used.** Those types are
experimental, their syntax moves between versions, and no parser checks them.
A plain flowchart with frames looks the same and has a grammar that holds
still.

## What is lost, at levels 3 and 4

Nesting. A component inside a container inside a system is three frames that
all look alike, and the reader loses track of which boundary is which. Level 1
and level 2 each need one frame, which is exactly what subgraphs do well.

## What works

- One frame marking the system, people and external systems outside it.
- The role vocabulary: a person is a circle, an external system is a dashed
  hexagon, a store is a cylinder.
- Labelled edges, which C4 insists on and this toolchain also insists on.

## Say this before drawing

At level 3 or 4:

> At this level C4 is mostly nesting, and Mermaid draws every frame the same
> way. draw.io keeps the levels apart. Or go up a level, which is usually the
> better answer.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
