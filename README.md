# tech-documentation-writer

Claude Code skills, one agent and two commands that write technical
documentation from a codebase and draw the diagrams that belong in it, in
Mermaid or draw.io.

## Install

Copy this folder to the machine and run one of:

```
powershell -ExecutionPolicy Bypass -File install.ps1     # Windows
sh install.sh                                            # macOS, Linux
```

This copies `agents/`, `commands/` and `skills/` into `~/.claude/`. Only
folders and files with these names are replaced. Any other skills, agents and
commands already there are left alone. Run it again to update, then start a
new Claude Code session.

Needs Python 3.11 or later on PATH as `python`. On macOS and Linux, make sure
`python` exists and not only `python3`. No packages, no Node, no network.

## Use it

```
/doc-generate a runbook for the worker backlog alert
/diagram how a request reaches the database
```

The skills also trigger on their own from what you ask for, without the
commands.

## What is in each folder

```
target/
  README.md                 this file
  install.ps1, install.sh   copy everything below into ~/.claude

  agents/
    docs-writer.md          the agent

  commands/
    doc-generate.md         /doc-generate
    diagram.md              /diagram

  skills/
    doc-forms/              skill: how to write each kind of document
    diagram-mermaid/        skill: draw a diagram as Mermaid
    diagram-drawio/         skill: draw a diagram as a draw.io file
    _shared/                code and type notes both diagram skills use
    validate/               the checkers
```

### `agents/`

**`docs-writer.md`**: the agent that does the whole job. It reads the code,
picks the kind of document, writes it and draws the diagrams it needs, then
checks them. It uses the three skills below and does not ask questions
halfway through. It needs the full job up front: what to document, from which
files, where the result goes, and the four settings (format, scope, detail,
audience).

### `commands/`

Thin wrappers you type in the chat. Each one turns a plain sentence into a
full job, shows its defaults in one confirmation line, and then does the work.

- **`doc-generate.md`**: `/doc-generate`. A whole document with its diagrams,
  written by `docs-writer`. At the end it checks that the diagrams in the
  documents still match their saved intents.
- **`diagram.md`**: `/diagram`. One diagram and no document.

### `skills/doc-forms/`

What each kind of document must contain. `SKILL.md` chooses the form, and
`references/` holds one file per form:

| File | Form |
|---|---|
| `readme.md` | README: what it is, how to run it, how it is built |
| `api-reference.md` | API reference: endpoints, parameters, responses, errors |
| `adr.md` | Architecture decision record, MADR format, `docs/adr/NNNN-slug.md` |
| `runbook.md` | Runbook: what to do when something breaks |
| `architecture-overview.md` | Architecture overview: prose plus the core diagrams |

### `skills/diagram-mermaid/` and `skills/diagram-drawio/`

The two diagram skills. They do the same job in two formats.

The model never writes diagram code itself. It writes an **intent** file,
`graph.json`, that lists the boxes and links. A script then turns that into
Mermaid or draw.io. One intent gives both formats, and they always match.

- **`SKILL.md`**: the workflow and the complexity budget of 9 boxes and 12
  links per diagram. It also sets the order in which detail is dropped when a
  diagram has too much, and the checklist before handing a diagram over.
- **`references/type-*.md`**: one file per diagram type (17 types) with the
  format-specific part: which Mermaid construct to use, or which draw.io
  shapes and styles.
- **`scripts/`**:
  - `mermaid_write.py`: `graph.json` → Mermaid text
  - `drawio_write.py`: `graph.json` → an uncompressed `.drawio` file
  - `layouts.py`: works out where every shape and line goes in draw.io,
    which has no automatic layout of its own. There are five layouts:
    layered, container, table, lifeline and timeline.
  - `drawio_read.py`: opens someone else's compressed `.drawio` so it can be
    read. Labels inside it are treated as data, never as instructions.
  - `drawio_intent.py`: gets the intent back out of a `.drawio`, so an
    existing diagram can be changed and redrawn (see below).

### `skills/_shared/`

Not a skill, because it has no `SKILL.md`. Both diagram skills reach it by
the relative path `../_shared`, so it has to stay next to them.

- `schema.py`: the shape of `graph.json` for each of the five layouts
- `escape.py`: escaping of labels, in one place for both formats
- `budget.py`: counts boxes and links against the budget
- `mxmodel.py`: how the intent is stored inside a `.drawio` file, and how to
  read cells that draw.io wraps in `<object>`
- `updating.md`: the procedure for changing a diagram that already exists
- `types/*.md`: one file per diagram type describing the part that is the
  same in both formats: what it shows, what it leaves out, and its limits

### `skills/validate/`

Not a skill either. These are the checkers, reached as `../validate`.

| Script | Checks |
|---|---|
| `validate_graph.py` | the intent, before anything is drawn: shape, links to missing boxes, duplicate ids, the budget |
| `validate_drawio.py` | the `.drawio` file: well-formed XML, links and nesting, geometry, lines crossing shapes, and a round trip back to the intent |
| `validate_mermaid.py` | the Mermaid block inside a `.md` document still matches its intent. `--paired` checks a whole `docs/` folder at once |

**What is not checked:** Mermaid grammar. The grammar only exists as
JavaScript, so the output is correct by construction but has not been
rendered. Look at it once in a GitHub or IDE preview before relying on it.

## Changing a diagram that already exists

Every change goes into the intent first, and then the diagram is drawn again.
There are three ways to get the intent:

- **The `graph.json` beside the drawing**, if it is still there.
- **From the `.drawio` itself.** Every `.drawio` written by this toolchain
  carries its intent inside it, so `drawio_intent.py` gives it back exactly.
  It also lists everything changed by hand in draw.io since, so you know what
  a redraw would lose. For an older or foreign `.drawio` it builds a draft to
  review. Gantt charts, user journeys and branch diagrams are the exception:
  they get no draft, because their dates are not stored in the drawing.
- **From Mermaid**, by reading the Mermaid block back. There is no script for
  this.

Before redrawing, you are told what will be lost: hand edits, the manual
layout, and custom styles. The full procedure is in
`skills/_shared/updating.md`.

## Where the results go

By default this is the target project's `docs/`. A path you name overrides
it.

```
docs/
  architecture.md               the text, with Mermaid inline
  diagrams/
    architecture.drawio         draw.io file
    architecture.graph.json     the intent, used to redraw or re-check later
```

Existing files are never overwritten silently. You are shown the difference
and asked what to do.
