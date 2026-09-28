# class in Mermaid

Read `../../_shared/types/class.md` first. This file only says what Mermaid
does with it.

**Renders as:** `classDiagram`. Coverage is **full**.

## How the type maps

| In `graph.json` | In Mermaid |
|---|---|
| entity | `class Name { … }`, or bare `class Name` when it has no rows |
| `stereotype` | `<<interface>>` on the first line inside the braces |
| row, kind `field` | `+Type name` |
| row, kind `method` | `+name(args) ReturnType` |
| `visibility` | the `+ - # ~` prefix, written straight through |

## Relations

| `kind` | Mermaid | Read as |
|---|---|---|
| `inherit` | `A --|> B` | A extends B |
| `implement` | `A ..|> B` | A implements B |
| `compose` | `A *-- B` | A owns B; B dies with A |
| `aggregate` | `A o-- B` | A holds B; B outlives A |
| `assoc` | `A --> B` | A refers to B |
| `dep` | `A ..> B` | A uses B without holding it |

Direction is always `from` then `to`, so the arrowhead lands on `to`. This is
the opposite of how UML tools usually let you draw it, and it is the reason
the relation is named for what `from` does.

## One thing Mermaid forces

**Members are bare tokens, not free text.** A member name containing a space
would parse as a type followed by a name and take the rest as an error, so
`expires at` is written as `expires_at`. The generator does this conversion,
along with turning `List<int>` into Mermaid's own `List~int~` generic form.
Class and member names should be written in `graph.json` exactly as they
appear in the code, and then this never comes up.

## What to know before shipping

- A method row gets `()` appended when the name has no parentheses, so
  `now` and `now()` both come out as `now()`.
- Namespaces, packages and notes are not generated. A class diagram that
  needs a namespace is drawing too much of the codebase.
- Mermaid picks the layout. A hierarchy may render with the base class below
  its children; do not describe the picture in the prose.

## Not checked by anything

Mermaid's own grammar. Say so in the answer.
