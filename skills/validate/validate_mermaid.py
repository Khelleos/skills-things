"""Check Mermaid where it landed, without pretending to parse Mermaid.

The third layer in plan section 6, and the one with the narrowest honest
scope. Mermaid's grammar exists only as JavaScript, and a hand-written parser
here would check the output against this project's belief about the grammar
rather than against the grammar, and would drift the first time Mermaid
changed. So this checks nothing about the grammar at all.

Three passes:

  1. shape        -- a known diagram header, balanced subgraph/end, no tabs
  2. escaping     -- no bare quote inside a quoted label, no raw angle bracket
  3. round trip   -- with --graph, the diagram in the file is the diagram the
                     intent produces now

**Be clear about what the round trip is worth.** It regenerates with
`mermaid_write` and compares, so both sides come out of the same code: a bug
*inside* the generator cancels itself out and is not caught here. What it
does catch is everything that happens to a diagram after the generator let go
of it -- a hand edit, a mangled paste, a document whose `graph.json` has since
moved on. That is the whole point of running it on the `.md`, where the
diagram actually lives, rather than on the `.mmd` the generator just wrote and
the workflow is about to throw away.

So: run it on the document, after the fence is in it. A failure means
regenerate from the intent, not patch the Markdown.

Usage:
    python validate_mermaid.py <file.mmd|file.md> [--graph <graph.json>]
                               [--fence N] [--json] [--quiet]
    python validate_mermaid.py docs/*.md --paired

A `.md` is read for its ```mermaid fences. With one fence, or with --fence N,
that is the one the round trip uses; with several, the fence whose title
matches `meta.title` is chosen, and an ambiguity is an error rather than a
guess. --paired finds each document's intents itself, in `<dir>/diagrams/`,
which is where both skills put them -- that is the form the "do the documents
still match their intents" sweep takes.

Exit code 0 when clean, 1 when any file has an error.

stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_SKILLS / "_shared"))
sys.path.insert(0, str(_SKILLS / "diagram-mermaid" / "scripts"))

import escape  # noqa: E402
import schema  # noqa: E402

HEADERS = (
    "flowchart",
    "graph",
    "stateDiagram-v2",
    "sequenceDiagram",
    "erDiagram",
    "classDiagram",
    "requirementDiagram",
    "gantt",
    "journey",
    "gitGraph",
)

#: A quoted label that still contains a bare double quote, which would end it
#: early. escape.py turns those into "#34;" -- this catches the case where
#: something bypassed it.
_BROKEN_LABEL = re.compile(r'"[^"]*"[^"|\]\)\}>:,;\s][^"]*"')

#: One fence line: up to three spaces of indent, then backticks or tildes,
#: then an info string on an opening fence and nothing on a closing one. The
#: info string may carry attributes -- ```mermaid title="x" -- and the first
#: word of it is the language.
_FENCE_LINE = re.compile(r"^(?P<indent> {0,3})(?P<marker>`{3,}|~{3,})[ \t]*(?P<info>[^`]*)$")

#: Something that reads like a Mermaid fence but sits where Markdown will not
#: treat it as one: four spaces in (an indented code block), or inside a
#: blockquote. Not read, and not passed over in silence either.
_LOOKS_LIKE = re.compile(r"^(?: {4,}|\s*>[ >]*)(?:`{3,}|~{3,})[ \t]*mermaid\b", re.IGNORECASE)

#: The title mermaid_write puts in a diagram's front matter.
_TITLE = re.compile(r"^title:\s*(.*?)\s*$", re.MULTILINE)


def _strip_front_matter(lines: list) -> list:
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                return lines[i + 1 :]
    return lines


def _body(text: str) -> list:
    """The diagram itself: front matter and %% comments removed."""
    lines = _strip_front_matter(text.splitlines())
    return [line for line in lines if line.strip() and not line.strip().startswith("%%")]


def _head(text: str) -> list:
    """What _body leaves behind: the front matter and the %% comments."""
    lines = text.splitlines()
    kept, rest = [], lines
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                kept = [l.rstrip() for l in lines[: i + 1]]
                rest = lines[i + 1 :]
                break
    return kept + [l.rstrip() for l in rest if l.strip().startswith("%%")]


def _unquote(value: str) -> str:
    """A YAML double-quoted scalar, back to the text it stands for.

    mermaid_write writes the title escaped, so a title with a quote in it
    arrives here as \\" and has to be read back or it will never match the
    intent it came from.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
        out, i = [], 0
        while i < len(value):
            if value[i] == "\\" and i + 1 < len(value):
                out.append(value[i + 1])
                i += 2
            else:
                out.append(value[i])
                i += 1
        return "".join(out)
    return value


def _title_of(text: str) -> str:
    """The title in a diagram's front matter, or empty."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        found = _TITLE.match(line.strip())
        if found:
            return _unquote(found.group(1))
    return ""


def fences(text: str) -> tuple:
    """Every fenced Mermaid block in a document, and any fence left open.

    Read line by line rather than by one regular expression, because the two
    ways this goes wrong are both structural: a fence indented under a list
    item is a real diagram and is easy to miss, and a fence *inside* a longer
    fence is an example of how to write one and must not be checked as a
    diagram. Markdown settles both by the marker: three to five backticks
    inside a four-backtick block are content, not a fence.

    Returns (blocks, unclosed, missed): the blocks as (line number, content),
    the line an unclosed mermaid fence opened on, and the lines that read like
    a fence but sit where Markdown will not treat them as one.
    """
    blocks, missed, open_at = [], [], None
    lines = text.splitlines()
    body: list = []

    for i, line in enumerate(lines, 1):
        found = _FENCE_LINE.match(line)
        if open_at is None:
            if found:
                info = found.group("info").strip()
                open_at = (
                    found.group("marker")[0],
                    len(found.group("marker")),
                    info.split()[0].lower() if info else "",
                    i,
                    len(found.group("indent")),
                )
                body = []
            elif _LOOKS_LIKE.match(line):
                missed.append(i)
            continue

        char, length, info, start, indent = open_at
        closes = (
            found
            and found.group("marker")[0] == char
            and len(found.group("marker")) >= length
            and not found.group("info").strip()
        )
        if closes:
            if info == "mermaid":
                blocks.append((start, "\n".join(body) + "\n"))
            open_at = None
        else:
            # The indent belongs to the list item or the quote, not to the
            # diagram. Left on, every line of a diagram under a numbered step
            # would differ from what the generator produces, and the report
            # would accuse a correct document of having been edited by hand --
            # with a diff whose two sides look identical.
            body.append(line[indent:] if line[:indent].strip() == "" else line)

    unclosed = open_at[3] if open_at and open_at[2] == "mermaid" else None
    return blocks, unclosed, missed


def _missed_note(line: int) -> str:
    """What this checker cannot read -- said as its own limit, not as Markdown's.

    Markdown is perfectly happy with a fence inside a blockquote or in the
    content column of a list item; it is this checker that stops at three
    spaces of indent, because reading further means tracking list context,
    which means writing a Markdown parser. Saying it the other way round was
    wrong twice over: the claim was false, and the remedy it suggested --
    unindent to three spaces -- breaks the nesting it is sitting in.
    """
    return (
        f"line {line} reads like a mermaid fence, but this checker only reads fences "
        "indented up to three spaces and never inside a blockquote, so nothing "
        "checked it. Move it to the top level, or check it on its own with --graph"
    )


def check_shape(text: str, errors: list, warnings: list) -> str:
    lines = _body(text)
    if not lines:
        errors.append("nothing here but comments")
        return ""

    header = lines[0].strip()
    kind = next((h for h in HEADERS if header.startswith(h)), "")
    if not kind:
        errors.append(
            f"first line is {header!r}, which is not a diagram type this toolchain "
            f"writes ({', '.join(HEADERS)})"
        )

    if "\t" in text:
        errors.append("a tab in the output. Mermaid indentation is spaces")

    # 'end' closes different things in different diagrams: a subgraph in a
    # flowchart, a fragment in a sequence diagram. Counting them together
    # would flag every alt block as an error.
    if kind in ("flowchart", "graph"):
        openers, what = ("subgraph ",), "subgraph"
    elif kind == "sequenceDiagram":
        openers = ("alt ", "opt ", "loop ", "par ", "critical ", "break ", "rect ")
        what = "fragment"
    else:
        return kind

    depth = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if any(stripped.startswith(o) for o in openers):
            depth += 1
        elif stripped == "end":
            depth -= 1
            if depth < 0:
                errors.append(f"line {i}: 'end' with no open {what}")
                depth = 0
    if depth:
        errors.append(f"{depth} {what}(s) left open at the end of the file")
    return kind


def check_escaping(text: str, errors: list, warnings: list) -> None:
    for i, line in enumerate(_body(text), 1):
        if _BROKEN_LABEL.search(line):
            errors.append(f"line {i}: a quoted label looks like it ends early")
        for raw in ("<", ">"):
            # Legitimate in arrows and in class-diagram stereotypes; a bare one
            # inside a quoted label is what escape.py exists to prevent.
            for chunk in re.findall(r'"([^"]*)"', line):
                if raw in chunk:
                    errors.append(
                        f"line {i}: {raw!r} inside a quoted label, which escape.py "
                        "would have turned into an entity code"
                    )


def check_round_trip(text: str, graph_path, errors: list, warnings: list) -> None:
    try:
        graph = schema.load(graph_path)
    except ValueError as exc:
        errors.append(str(exc))
        return

    try:
        import mermaid_write
    except ImportError as exc:  # pragma: no cover - only if the tree is broken
        errors.append(f"cannot import the generator: {exc}")
        return

    try:
        regenerated = mermaid_write.render(graph)
    except mermaid_write.GenerationError as exc:
        errors.append(f"the intent no longer generates: {exc}")
        return

    # The diagram is compared; the title and the %% loss report are not. A
    # document gets tidied, and a rewritten caption above a correct diagram is
    # worth saying out loud and not worth refusing over. The diagram itself is
    # the thing nobody may edit by hand.
    actual, expected = _body(text), _body(regenerated)
    if actual != expected:
        for i, (a, b) in enumerate(zip(actual, expected), 1):
            if a != b:
                errors.append(
                    f"round trip: line {i} of the diagram differs. Regenerate from "
                    f"the intent rather than editing this by hand.\n"
                    f"      in the file:  {a.strip()}\n"
                    f"      regenerated:  {b.strip()}"
                )
                break
        else:
            errors.append(
                f"round trip: the diagram has {len(actual)} lines, "
                f"regenerating gives {len(expected)}"
            )
        return

    if _head(text) != _head(regenerated):
        warnings.append(
            "the diagram matches the intent, but the title or the %% loss report "
            "around it does not. Whatever changed them, they are what tells a "
            "reader what the diagram leaves out"
        )

    payload = graph.get("payload") or {}
    wanted = []
    for key in ("nodes", "actors", "tracks"):
        wanted += [(n["id"], n.get("label", "")) for n in payload.get(key) or []]
    for entity in payload.get("entities") or []:
        wanted.append((entity["id"], entity.get("label", "")))
    for span in payload.get("spans") or []:
        wanted.append((span["id"], span.get("label", "")))

    for node_id, label in wanted:
        clean = escape.normalize(label)
        if not clean:
            continue
        # Either the label survives whole, or its identifier form does -- ER
        # and class diagrams name a box with a bare token.
        if clean not in text and escape.identifier(clean, "x") not in text:
            warnings.append(
                f"{node_id!r} is in the intent but its label {clean!r} is nowhere "
                "in the output"
            )


def pick_fence(blocks: list, graph_path, wanted: int, errors: list):
    """Which fence the round trip is about.

    One fence, or --fence N, settles it. Otherwise the title in the front
    matter picks it out, because that is what the generator writes there. Two
    candidates is an error and not a guess: checking the wrong diagram against
    an intent produces a confident, wrong answer.
    """
    if wanted is not None:
        if not 1 <= wanted <= len(blocks):
            errors.append(f"--fence {wanted}, but this document has {len(blocks)}")
            return None
        return blocks[wanted - 1]
    if len(blocks) == 1:
        return blocks[0]

    title = ""
    try:
        meta = schema.load(graph_path).get("meta") or {}
        title = escape.normalize(meta.get("title") or "")
    except ValueError:
        pass

    matches = [b for b in blocks if title and _title_of(b[1]) == title]
    if len(matches) == 1:
        return matches[0]

    listed = ", ".join(f"line {line} {_title_of(body)!r}" for line, body in blocks)
    errors.append(
        f"{len(blocks)} fences here and {len(matches)} of them titled {title!r}, "
        f"so which one the intent describes is a guess. Name it with --fence N: {listed}"
    )
    return None


def validate_file(path, graph_path=None, fence=None) -> tuple:
    errors: list = []
    warnings: list = []
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {path}: {exc}"], []

    # A fence, wherever it is: a document, or a .mmd written with --fence.
    # Dispatching on the content rather than on the suffix is what stops a
    # fenced file being read as a diagram whose first line is backticks.
    blocks, unclosed, missed = fences(text)
    if unclosed:
        errors.append(
            f"the mermaid fence opened at line {unclosed} is never closed, so what "
            "follows it is anybody's guess"
        )
    warnings += [_missed_note(line) for line in missed]
    if not blocks and not unclosed and not missed and path.suffix.lower() in (".md", ".markdown"):
        return [f"no ```mermaid fence in {path.name}"], []
    # A document, even a malformed one, is never read as though it were a bare
    # diagram: that produced a second, baffling error about its first line.
    if blocks or unclosed or missed:
        for line, body in blocks:
            here_errors: list = []
            check_shape(body, here_errors, warnings)
            check_escaping(body, here_errors, warnings)
            errors += [f"fence at line {line}: {e}" for e in here_errors]
        if graph_path:
            chosen = pick_fence(blocks, graph_path, fence, errors)
            if chosen is not None:
                line, body = chosen
                here_errors, here_warnings = [], []
                check_round_trip(body, graph_path, here_errors, here_warnings)
                errors += [f"fence at line {line}: {e}" for e in here_errors]
                warnings += [f"fence at line {line}: {w}" for w in here_warnings]
    else:
        check_shape(text, errors, warnings)
        check_escaping(text, errors, warnings)
        if graph_path:
            check_round_trip(text, graph_path, errors, warnings)

    if not graph_path:
        warnings.append(
            "no --graph, so only the shape and the escaping were checked. "
            "The round trip is the pass worth running"
        )

    warnings.append(
        "nothing here has rendered this diagram, and nothing here can: Mermaid's "
        "grammar exists only as JavaScript. Preview it before shipping it"
    )
    return errors, warnings


def check_paired(path: Path) -> tuple:
    """A document against the intents kept beside it, in <dir>/diagrams/.

    This is the sweep: it answers "do the documents still say what their
    intents say", which is the question nobody asks until a diagram has been
    wrong for a month.
    """
    errors: list = []
    warnings: list = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {path}: {exc}"], []

    blocks, unclosed, missed = fences(text)
    if unclosed:
        errors.append(f"the mermaid fence opened at line {unclosed} is never closed")
    # Elsewhere this is a note, because a person looking at one file will read
    # it. Here it is an error: --paired exists to answer "do the documents
    # still match their intents", and that is a claim about all of them. A
    # diagram this cannot reach is a hole in the only answer it gives.
    errors += [_missed_note(line) for line in missed]
    if not blocks:
        return errors, warnings + [f"{path.name} holds no ```mermaid fence"]

    diagrams = path.parent / "diagrams"
    if not diagrams.is_dir():
        return (
            [
                f"{path.name} has {len(blocks)} diagram(s) and there is no "
                f"{diagrams.name}/ beside it, so not one of them can be held against "
                "an intent. Either the intents were never kept or the directory moved"
            ],
            warnings,
        )

    graphs = sorted(diagrams.glob("*.graph.json"))
    titles: dict = {}
    for graph_path in graphs:
        try:
            meta = schema.load(graph_path).get("meta") or {}
        except ValueError as exc:
            errors.append(str(exc))
            continue
        titles.setdefault(escape.normalize(meta.get("title") or ""), []).append(graph_path)

    # The same refusal pick_fence makes, for the same reason. Choosing between
    # two intents of one name by filename order would report a correct
    # document as drifted and tell its author to destroy it.
    by_title, ambiguous = {}, set()
    for title, found in titles.items():
        if len(found) == 1:
            by_title[title] = found[0]
            continue
        ambiguous.update(found)
        errors.append(
            f"{', '.join(p.name for p in found)} are all titled {title!r}, so which "
            "one a fence describes is a guess. Give them different titles, or check "
            "them one at a time with --graph"
        )

    used = set()
    for line, body in blocks:
        here_errors: list = []
        check_shape(body, here_errors, warnings)
        check_escaping(body, here_errors, warnings)

        graph_path = by_title.get(_title_of(body))
        if graph_path is None:
            warnings.append(
                f"fence at line {line}: nothing in {path.parent.name}/diagrams/ is "
                f"titled {_title_of(body)!r}, so this one cannot be checked against "
                "an intent or redrawn in the other format"
            )
        else:
            used.add(graph_path)
            here_warnings: list = []
            check_round_trip(body, graph_path, here_errors, here_warnings)
            warnings += [f"fence at line {line}: {w}" for w in here_warnings]
        errors += [f"fence at line {line}: {e}" for e in here_errors]

    for graph_path in graphs:
        if graph_path not in used and graph_path not in ambiguous:
            warnings.append(
                f"{graph_path.name} is kept but no fence in {path.name} carries its "
                "title. Either the diagram was dropped or the title was edited"
            )
    return errors, warnings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Mermaid where it landed: a .mmd, or the fences in a document."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--graph", type=Path, help="the graph.json it came from")
    parser.add_argument("--fence", type=int, help="which fence in the document, counting from 1")
    parser.add_argument(
        "--paired",
        action="store_true",
        help="find each document's intents in <dir>/diagrams/ instead of naming one",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true", help="print only problems")
    args = parser.parse_args(argv)

    if args.graph and len(args.paths) > 1:
        print("error: --graph takes one file at a time", file=sys.stderr)
        return 2
    if args.paired and args.graph:
        print("error: --paired finds the intents itself, so it takes no --graph", file=sys.stderr)
        return 2

    results, failed = [], False
    for path in args.paths:
        if args.paired:
            errors, warnings = check_paired(Path(path))
        else:
            errors, warnings = validate_file(path, args.graph, args.fence)
        failed = failed or bool(errors)
        results.append(
            {"path": str(path), "ok": not errors, "errors": errors, "warnings": warnings}
        )

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for r in results:
            if r["errors"]:
                print(f"FAIL  {r['path']}")
            elif not args.quiet:
                print(f"ok    {r['path']}")
            for e in r["errors"]:
                for i, line in enumerate(str(e).splitlines()):
                    print(f"  {'error:' if i == 0 else '      '} {line}")
            if not args.quiet:
                for w in r["warnings"]:
                    print(f"  note:  {w}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
