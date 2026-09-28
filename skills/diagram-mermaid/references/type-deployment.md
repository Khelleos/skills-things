# deployment in Mermaid

Read `../../_shared/types/deployment.md` first. This file only says what Mermaid
does with it.

**Renders as:** `flowchart TD` with `subgraph` frames. Coverage is
**approximate**, and the caveat has to be said before the diagram is drawn.

## What is lost

**A host is a frame, not a thing.** In draw.io a machine is an object with a
kind of its own; here it is a rounded rectangle drawn around its contents and
nothing distinguishes it from any other grouping. A reader cannot tell a host
from a logical boundary without reading the label.

**Ports, replica counts and versions survive only inside a label.** There is
nowhere else to put them: `API x3` is a label, and if it is dropped for
length the count goes with it.

**Nesting reads badly past one level.** A container inside a VM inside a
region is three borders that all look the same.

## What works

Frames, arrows across frames, and the shape vocabulary inside them — a
cylinder is still a store, a dashed box is still external. For a deployment of
four hosts and six processes, this is enough and it renders in a pull
request, which draw.io does not.

## Say this before drawing

> Mermaid draws hosts as plain frames, so replica counts and ports will only
> appear inside labels. If that matters here, draw.io draws them properly.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
