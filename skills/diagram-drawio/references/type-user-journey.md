# user-journey in draw.io

Read `../../_shared/types/user-journey.md` first. This file only says what draw.io
does with it.

**Layout:** `timeline`. Coverage is **full**.

## The score is a colour

Mermaid draws the scores as a line, which makes the dip visible at a glance.
draw.io has no line, so the score is drawn as the bar's fill, on a five-step
scale from a pale red at 0 to a pale green at 5, with the number written into
the label as `(2/5)`.

Both are honest. The line reads faster; the colour survives being pasted into
a slide, and is the one worth having when the journey is being presented
rather than reviewed.

## How it is placed

One band per phase, steps along the axis in `start` order. A step's `note` --
who is doing it -- is not drawn here; Mermaid draws it as the actor. Put the
actor in the phase label if it matters, or accept that this format shows the
path and not the cast.

## What to know before shipping

- **A score with no source is the worst thing this toolchain can produce.**
  Take it from a ticket, a session, a complaint, and say where in the loss
  report.
- **Colour is doing the work**, so this is the one diagram here that loses
  meaning printed in greyscale. The `(n/5)` in the label is the fallback and
  the reason it is there.
- Five phases, fifteen steps.

## Not checked by anything

Whether it looks right. `validate_drawio.py` proves the model is sound and
that nothing was lost between the intent and the XML, but no draw.io has
opened it. Say so.
