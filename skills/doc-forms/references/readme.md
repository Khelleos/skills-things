# README

**Answers:** what is this, how do I run it, how is it put together?

**Reader:** someone who arrived from a search result or a link and has about
ninety seconds before deciding whether to keep reading.

## Shape

1. **Name and one sentence.** What it does, for whom. Not what it is built
   with — nobody chooses a tool by its dependency list.
2. **The shortest thing that works.** Install, then one command that produces
   visible output. Real values, real output shown.
3. **What it is for**, in three or four bullets: the cases it handles well.
4. **What it is not for.** The cases it does not handle, or handles badly.
   Two lines here save a reader an afternoon.
5. **How it is put together.** Only if a contributor needs it: the pieces and
   what talks to what. This is where an `architecture` diagram belongs, if
   the shape is worth a picture.
6. **Configuration**, as a table: name, default, what it changes. Defaults
   are the important column.
7. **Where to go next.** Links to the API reference, the runbooks, the ADRs.

## What does not belong

- The full option list. That is the API reference.
- Why the design is the way it is. That is an ADR — link to it.
- Recovery procedures. That is a runbook.
- A changelog, a licence essay, a contributor covenant. Link them.

## The opening sentence

The hardest part, and the part most worth rewriting. Test it: could this
sentence sit on a competitor's README unchanged? If it could, it says nothing.

- Weak: "A modern, flexible library for working with tasks."
- Better: "Runs Python functions on other machines, and tells you what
  happened to them."

## Diagram

At most one, and only in section 5. `architecture` is nearly always the right
type — the reader wants the pieces and the traffic between them, not an
ordering. A README with a sequence diagram in it is usually a README that
should have linked to something else.

Six blocks is plenty here. The budget allows nine; a README that needs nine
is describing a system whose overview belongs in its own document.

## Checks before handing it over

- Does the first command work from a clean checkout, exactly as written?
- Does the "not for" section exist, and is it honest?
- Are the configuration defaults the real defaults, read from the code?
- Is there a date, or a version this describes?
