# API reference

**Answers:** what can I call, with what, and what comes back?

**Reader:** someone mid-task with the call half-written, looking for one
specific fact. They are scanning, not reading.

## Shape

Scanning is the whole design constraint. Same order for every entry, so the
eye learns where to land.

Per surface — an endpoint, a public function, a CLI command:

1. **Signature**, exactly as it is written in the code.
2. **One line** on what it does. A verb first.
3. **Parameters**, as a table: name, type, required, default, meaning.
   Defaults matter more than types; a reader can guess a type.
4. **Returns**: the shape, and what the fields mean.
5. **Errors**: what can go wrong, what the caller sees, what to do about it.
6. **Example**: one real call and its real output.

Group by what the reader is trying to do, not by module. Alphabetical order
is for indexes, not for pages.

## Errors are the point

Most API references are written from the success path and read from the
failure path. For every listed error, three things: the condition that
triggers it, what the caller receives, and whether retrying helps.

An error a caller cannot distinguish from another error is a bug in the API,
and saying so in the document is fair.

## What does not belong

- Internal call chains and private helpers. If it is not callable, it is not
  in the reference.
- Design rationale. Link the ADR.
- Tutorials. One example per surface; a walkthrough is its own document.

## Read this from the code, always

Signatures, defaults and error types are the three things that drift fastest
and are hardest to spot when wrong. Take every one from the source. A default
copied from an older document is the classic way a reference becomes actively
harmful.

Where the code and an existing document disagree, the code wins and the
disagreement goes in what you report back.

## Diagram

Usually none. A reference is a lookup table and a diagram interrupts it.

Two exceptions, both at the top of the page rather than inside an entry:

- A `state` diagram, when calls are only legal in certain states — a
  connection, a session, a multi-step upload.
- A `sequence` diagram, when a surface only makes sense as part of a fixed
  exchange, such as a token refresh or a handshake.

## Checks before handing it over

- Is every signature copied from the source, not retyped from memory?
- Does every entry list its errors, with what to do about each?
- Does every example use values a reader could actually send?
- Are the surfaces grouped by task rather than by file?
