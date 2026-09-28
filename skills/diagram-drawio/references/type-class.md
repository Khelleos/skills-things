# class in draw.io

Read `../../_shared/types/class.md` first. This file only says what draw.io
does with it.

**Layout:** `table`. Coverage is **full**, and better than Mermaid on member
names.

## How the type is placed

Each class is a swimlane: the class name in the title bar, one child cell per
member. A `stereotype` is drawn above the name as `<<interface>>`.

Members are laid out in the order given, as `+name : Type`, with `()` added
to a method name that has none.

**Member names are drawn as written.** This is where draw.io wins: Mermaid
reads a member as bare tokens, so `expires at` has to become `expires_at` and
`List<int>` has to become `List~int~`. Here both are labels and both are
drawn as they appear in the code.

Rows are not otherwise decorated. Visibility is the `+ - # ~` prefix and
nothing else — no colour, no icon, no second legend.

## Relations

| `kind` | Drawn as |
|---|---|
| `inherit` | hollow triangle at the target |
| `implement` | hollow triangle, dashed line |
| `compose` | filled diamond at the source |
| `aggregate` | hollow diamond at the source |
| `assoc` | open arrowhead at the target |
| `dep` | open arrowhead, dashed line |

These are the UML notations, which is the one place in this toolchain where a
reader is assumed to already know a convention. It is a fair assumption for a
class diagram and would not be for anything else.

Direction is `from` then `to`, as everywhere: `HmacVerifier inherit
TokenVerifier` puts the triangle on `TokenVerifier`.

## What to know before shipping

- **A row note is drawn nowhere.** It survives as an XML comment.
- **Eight classes across a three-wide grid** is the limit, and a hierarchy
  gridded three across does not look like a hierarchy. If the shape of the
  inheritance is the point, this layout works against you and Mermaid's own
  layout engine will do better.
- **Relations may pass under a box.** Same grid, same caveat as the data
  model.

## Compared with Mermaid

Better here: real member names, real generics, exact placement.

Worse here: a hierarchy laid out on a grid reads worse than one laid out by
an engine that knows it is a hierarchy. For inheritance-shaped diagrams,
prefer Mermaid unless the file has to be hand-edited.

## Not checked by anything

Whether it looks right. Say so.
