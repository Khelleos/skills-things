# class

Types in the code and how they are related.

**Layout:** `table` — `payload` holds `entities` and `relations`.

## Shows

The handful of types a reader needs in order to extend or replace something:
the interface, its implementations, the value objects passing between them.

## Does not show

- Every class in the module. Six is a diagram; twenty is a directory
  listing, and the directory listing is better.
- Call order — that is `sequence`.
- Private helpers, `__init__`, getters, setters, dunder methods. They are
  rung 1 and go without being mentioned.

## Fields

`entities[]`

| Field | Required | Notes |
|---|---|---|
| `id` | yes | identifier |
| `label` | yes | the type name as written in the code |
| `rows` | yes | may be empty when only the relation matters |
| `stereotype` | no | `interface`, `abstract`, `enum`, `service` |
| `note` | no | one line |

`rows[]`

| Field | Required | Notes |
|---|---|---|
| `name` | yes | field name, or a method signature: `verify(token)` |
| `type` | recommended | the field's type, or a method's return type |
| `kind` | recommended | `field` or `method` |
| `visibility` | no | `+` public, `-` private, `#` protected, `~` package |

`relations[]`

| Field | Required | Notes |
|---|---|---|
| `from`, `to` | yes | must name entities in this diagram |
| `kind` | yes | `inherit`, `implement`, `compose`, `aggregate`, `assoc`, `dep` |
| `label` | no | the role the relation plays |

Direction is always read from `from` to `to`: `HmacVerifier inherit
TokenVerifier` means the first extends the second.

`cardinality` is not accepted here — that field belongs to `data-model`.

## Limits

8 classes, 12 relations, 12 rows in any one class.

## Reducing this type

- Show one implementation, not five (rung 2), and say in the loss report how
  many others there are.
- A value object with no behaviour becomes a row's type rather than a box
  (rung 3).
- Base classes that add nothing to the story go (rung 4).

## When a table is better

Almost always, for "what does this class expose" — that is what a signature
listing is for. The diagram earns its place only when the shape of the
relations is the point: a strategy set, a hierarchy, a boundary.
