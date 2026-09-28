---
name: doc-forms
description: Write one of the five standard technical documents from a codebase - a README, an API reference, an architecture decision record in MADR format, a runbook, or an architecture overview. Each form has a fixed shape, a fixed set of questions it must answer, and a rule for what belongs in it and what belongs somewhere else. Use when producing or updating documentation from source, and when deciding which of these forms a piece of writing should take.
---

# Document forms

Five forms. Each answers a different question, and the commonest failure in
technical writing is answering one form's question inside another's document.

| Form | The question it answers | File |
|---|---|---|
| README | What is this, how do I run it, how is it put together? | `references/readme.md` |
| API reference | What can I call, with what, and what comes back? | `references/api-reference.md` |
| ADR | Why is it like this, and what did we turn down? | `references/adr.md` |
| Runbook | It is broken at 3am. What do I do? | `references/runbook.md` |
| Architecture overview | How does this actually work, and why this shape? | `references/architecture-overview.md` |

Read the form's file before writing.

## Rules that hold for all five

**Write from the code, not from around it.** Open the entry point and follow
it. Every claim in the document should be one you could point at a line for.
If you could not, either go and read, or write the sentence so it says what
you actually know.

**The reader is not you.** They have the problem the document is named after
and no context. They do not know the internal name for anything. Say what a
thing does before saying what it is called.

**Show the shortest thing that works first.** The minimal working example
comes before the options, always. A reader who needs the options will read
on; a reader who needs to get going has already gone.

**Every command is copy-pasteable.** Real flags, real paths, no `<your-value>`
where a plausible value would do. If a value has to be substituted, say what
it looks like.

**Say what it does not do.** Limits, unsupported cases and known sharp edges
belong in the document, not in the issue tracker. This is the single thing
that most separates documentation people trust from documentation they check
against the code.

**Diagrams answer shape questions.** A diagram earns its place when the thing
being explained has an ordering, a branching, or a set of relations that
prose needs three sentences to reconstruct. Otherwise it is decoration.
See `diagram-mermaid` for one that reads in a diff, `diagram-drawio` for one
somebody will open and rearrange, and either for the rule that the diagram's
own type file may tell you a table is better.

**Date and scope every document.** A document with no date is a document a
reader cannot judge. Say what it covers and, in an ADR or a runbook, when it
was last true.

## The reader check

After a document is written, predict the questions its reader will arrive
with, and check whether the document answers them.

The point is that a document can be complete, accurate, well organised and
still not answer the thing anyone actually opens it for.

**How it runs:** the writer returns three to five predicted questions along
with the document. The **caller** — not the writer, and not a subagent of the
writer — puts each question to a separate reader who has only the document,
and asks whether it can be answered from what is written. A question that
comes back unanswered is a gap, not a style note.

Make the questions specific and answerable from a document or not:

- Good: "How do I rotate the signing key without dropping live sessions?"
- Good: "Which of these endpoints needs the admin scope?"
- Useless: "Is the document clear?"

The check is optional. Run it on documents someone will depend on, and on
anything long enough that a gap can hide in it.

## Where documents go

The target project's `docs/`, unless a path was named.

```
docs/
  README.md            or the repository root, for a README
  architecture.md      the overview
  api/<surface>.md
  adr/NNNN-slug.md     four digits, sequential across the whole project
  runbooks/<alert>.md
  diagrams/            graph.json beside anything drawn
```

**Never overwrite silently.** Read what is there, report the difference, and
write alongside. Replacing someone's document is the caller's decision.
