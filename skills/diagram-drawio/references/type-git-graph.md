# git-graph in draw.io

Read `../../_shared/types/git-graph.md` first. This file only says what draw.io
does with it.

**Layout:** `timeline`. Coverage is **approximate**, and this is the one type
where Mermaid is clearly the better format.

## What is lost

**There is no branch renderer.** Mermaid has one; draw.io has bands. A branch
here is a horizontal track with commits placed along it, and a merge is a
circle on the target track with a dashed arrow coming from the source. It is
readable, and it is not the picture people expect when they ask for a branch
diagram.

**Branch colour, the curve of a merge, the sense of divergence and
convergence** -- all of that is Mermaid's, and none of it is reproduced.

## How it is placed

| `kind` | Drawn as |
|---|---|
| `commit` | small circle |
| `merge` | circle, pale green |
| `branch` | rounded bar |

`depends_on` becomes a dashed arrow, which is how a merge shows what it
merged.

## When to use this format anyway

Only two reasons, and both are real:

1. The diagram has to sit in a slide next to other draw.io diagrams and look
   like them.
2. Someone will rearrange it by hand, because the model is unusual enough
   that no generator will lay it out the way it needs to be.

Otherwise, say plainly that Mermaid draws this type properly and this one
does not.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
