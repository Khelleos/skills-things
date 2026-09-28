# git-graph

Branches, and how a change reaches a release.

**Layout:** `timeline` — `payload` holds `tracks` and `spans`.

## Shows

The branching model a project actually uses: which branches exist, what lands
on them, and where merges happen. Drawn once, in the contributing guide, and
almost never anywhere else.

## Does not show

- Real history. This is the **model**, not a log. A diagram of last month's
  commits is out of date before it is committed.
- Every branch. One representative feature branch stands for all of them.
- Who did what. Authors belong in the log.

## Fields

`tracks[]` — the branches. **The first track is the trunk.**

| Field | Required | Notes |
|---|---|---|
| `id`, `label` | yes | the branch name as people type it: `main`, `v5x` |

`spans[]` — what lands on a branch.

| Field | Required | Notes |
|---|---|---|
| `id`, `track`, `label` | yes | the label is what the commit is for, not its hash |
| `start` | yes | position along the axis: `1`, `2`, `3` … |
| `kind` | yes | `commit`, `merge`, or `branch` |
| `depends_on` | for a merge | the span on the branch being merged in |

A `merge` needs `depends_on` naming a span on **another** track; without it
there is nothing to merge and the generator refuses rather than guessing.

Branches open the first time something lands on them, in axis order. That is
the same rule both formats follow, so the two diagrams agree.

## Limits

5 tracks, 15 spans. Five branches is already an unusual model; more than that
and the model is what needs simplifying, not the diagram.

## Reducing this type

- One feature branch, not three (rung 2). Say in the loss report that others
  behave identically.
- Hotfix branches that behave like feature branches merge into that one box.
- Tags are not spans unless the tag is the point. A release is usually a
  commit labelled for the release.

## When a table is better

For the rules themselves — "feature branches off main, squash-merged, release
branches cut from main, tagged" — prose beats the diagram and is what people
search for. Draw this when the shape is unusual enough that the prose needs
a picture beside it.
