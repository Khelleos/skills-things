# git-graph in Mermaid

Read `../../_shared/types/git-graph.md` first. This file only says what Mermaid
does with it.

**Renders as:** `gitGraph`. Coverage is **full**, and better than draw.io.

This is the one type where Mermaid clearly wins: it has a real branch
renderer and draw.io has bands, which is why plan section 3 marked it
approximate on the draw.io side.

## How the type maps

| In `graph.json` | In Mermaid |
|---|---|
| first track | the trunk. Mermaid opens on it, so it is never branched |
| any other track | `branch <name>` the first time something lands on it |
| span, kind `commit` | `commit id: "<label>"` |
| span, kind `merge` | `merge <source branch> tag: "<label>"` |
| `depends_on` on a merge | which branch is merged in |

A merge whose `depends_on` names nothing on another branch is refused --
there would be nothing to merge.

## What to know before shipping

- **Branch names become identifiers**, so `v5.x` is drawn as `v5_x`. Name the
  tracks the way people type them and this rarely bites.
- **Order is the axis order**, taken from `start`. Two spans with the same
  `start` are drawn in the order they appear in the intent.
- **Mermaid picks the colours.** Do not describe a branch by its colour in
  the prose next to the diagram.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
