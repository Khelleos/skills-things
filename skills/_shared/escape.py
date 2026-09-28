"""Label escaping for both diagram formats.

One place, per plan section 9. Labels arrive from source code, from commit
messages and from other people's diagrams: they are data, never instructions.
Nothing leaves this module still able to act as syntax in the target format.

stdlib only.
"""

from __future__ import annotations

import re
import unicodedata

MAX_LABEL = 120

# Control characters, minus tab and newline which normalize() handles itself.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

# Mermaid reads "#NNN;" inside a label as a character entity, so a literal '#'
# has to be replaced first or it swallows whatever follows it.
# An apostrophe is not escaped: the label it sits in is already double-quoted,
# so it is plain text there, and encoding it risks a literal "#39;" on any
# renderer that does not expand entity codes in that position.
_MERMAID = (
    ("#", "#35;"),
    ("&", "#38;"),
    ("<", "#60;"),
    (">", "#62;"),
    ('"', "#34;"),
)

_HTML = (
    ("&", "&amp;"),
    ("<", "&lt;"),
    (">", "&gt;"),
    ('"', "&quot;"),
    ("'", "&#39;"),
)

_ID_RE = re.compile(r"[^A-Za-z0-9_]")

# Characters that end a class-diagram member early or open a comment.
_MEMBER_DROP = re.compile(r"""[{}|"'`%;\\]""")
_MEMBER_TIGHTEN = re.compile(r"\s*([(),])\s*")


def normalize(text: object) -> str:
    """Coerce to a single clean string: NFC, no control characters, no CR."""
    s = "" if text is None else str(text)
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    s = _CONTROL.sub("", s)
    return s.strip()


def clip(text: str, limit: int = MAX_LABEL) -> str:
    """Cut over-long labels. A label past the limit is a section 7 problem
    (too much detail in one block), but the renderer must not be the place
    where that goes wrong."""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "\u2026"


def _sub(text: str, table: tuple[tuple[str, str], ...]) -> str:
    for src, dst in table:
        text = text.replace(src, dst)
    return text


def mermaid_text(text: object, limit: int = MAX_LABEL) -> str:
    """Escaped label for places where Mermaid takes bare text up to the end of
    the line: sequence messages, titles, notes. Newlines cannot survive here."""
    s = clip(normalize(text), limit)
    s = " ".join(s.split("\n"))
    return _sub(s, _MERMAID)


def mermaid_quoted(text: object, limit: int = MAX_LABEL) -> str:
    """Escaped label wrapped in quotes, for node and edge labels. Quoting is
    what makes brackets, pipes and semicolons inside a label harmless, so this
    returns the quotes as part of the token - a caller cannot forget them."""
    s = clip(normalize(text), limit)
    parts = [_sub(p, _MERMAID) for p in s.split("\n")]
    return '"' + "<br/>".join(parts) + '"'


def mermaid_plain(text: object, limit: int = MAX_LABEL) -> str:
    """Single-line label for the parts of Mermaid that are neither a quoted
    flowchart label nor free text to end of line: sequence participants and
    messages, state captions, ER relation labels.

    Entity codes are a flowchart feature and print literally elsewhere, so
    here the dangerous characters are removed rather than encoded. A quote
    becomes an apostrophe, a doubled percent would open a comment, and a
    newline has nowhere to go.
    """
    s = clip(normalize(text), limit)
    s = " ".join(s.split("\n"))
    s = s.replace('"', "'")
    while "%%" in s:
        s = s.replace("%%", "%")
    return s


def mermaid_member(text: object, limit: int = 60) -> str:
    """A class-diagram member: a field name, a type, a method signature.

    Mermaid reads a member as bare tokens, so 'expires at' would parse as a
    type and a name and take the rest as an error. Whitespace closes up, and
    angle brackets become the tildes Mermaid uses for generics.
    """
    s = normalize(text).replace("<", "~").replace(">", "~")
    s = _MEMBER_DROP.sub("", s)
    # A space next to a bracket or a comma is layout, not part of a name:
    # 'store_result(task_id, result)' must not become 'task_id,_result'.
    s = _MEMBER_TIGHTEN.sub(r"\1", s)
    s = "_".join(s.split())
    return clip(s, limit)


def drawio_value(text: object, limit: int = MAX_LABEL) -> str:
    """Escaped label for the mxCell 'value' attribute.

    Two layers escape here, and both are needed. draw.io parses the file as
    XML, then renders the resulting string as HTML. So a literal '<' has to
    survive XML parsing as '&lt;' and therefore be written as '&amp;lt;'.
    A real line break is the opposite case: it must survive XML parsing as a
    live '<br>' tag, so it is escaped once and not twice.
    """
    s = clip(normalize(text), limit)
    html = "<br>".join(_sub(p, _HTML) for p in s.split("\n"))
    return _sub(html, (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;")))


def drawio_attr(text: object) -> str:
    """Plain XML attribute escaping, for attributes that are not rendered as
    HTML."""
    return _sub(normalize(text), _HTML)


def identifier(text: object, fallback: str = "n") -> str:
    """Reduce free text to something usable where a format demands a bare
    identifier - Mermaid ER attribute names, for one."""
    s = _ID_RE.sub("_", normalize(text))
    s = s.strip("_")
    if not s or s[0].isdigit():
        s = fallback + ("_" + s if s else "")
    return s


def untrusted(text: object, limit: int = MAX_LABEL) -> str:
    """Text lifted out of a diagram somebody else wrote.

    This is the boundary where a label that tries to talk to the agent gets
    flattened into one short piece of data: normalised, put on a single line
    so it cannot forge a second one in a listing, and clipped.
    """
    s = " ".join(normalize(text).splitlines())
    return clip(" ".join(s.split()), limit)
