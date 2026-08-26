# Benchmarks

```bash
pip install tiktoken                    # optional; without it, counts are estimates
python3 bench/token_compare.py          # compression
python3 bench/fidelity.py               # round-trip fidelity, recovery, cost split
```

Two scripts answering two different questions. **The second one matters more.**

## What `token_compare.py` measures

Four hand-written pairs. Each pair carries **the same information** — including the parts
prose usually drops: per-claim confidence, known unknowns, and precise references. Anything
less would not be a comparison, it would be a strawman.

On those four pairs the wire form runs roughly **20% smaller**.

## What it does not measure

**Anything that matters most.** Four examples measure a format, not a system. The number
worth having is task success rate at a fixed token budget across a multi-domain suite,
specified in [spec/SPEC.md §25](../spec/SPEC.md) and **not yet run**.

Two things to keep in view when reading the output:

- Against a **chatty** baseline the same comparison shows 3–4×. That figure is meaningless
  and this project does not quote it. The baselines here are deliberately not chatty.
- **Content-heavy messages compress least**, because the content is the same bytes either
  way. The fourth row shows this, and that is the honest shape of the result.

## Disagree with the baselines?

They are our own prose, and they are the weakest link in the whole comparison. They live in
the source file rather than in a table in a README precisely so you can edit them and rerun.
If you can write a tighter equal-information baseline, that is a genuinely useful pull
request — including if it makes our numbers worse.


---

# What `fidelity.py` measures

Compression is worthless if the message no longer says what it said. This is the check.

### Part 1 — round-trip fidelity

A block of thirteen deliberately hostile content lines — code fences, a line shaped exactly
like a Rosetta header, a line shaped exactly like a `mark`, a nested content line, fullwidth
punctuation, RTL script, emoji, a decomposed grapheme, trailing whitespace, a 300-character
line — pushed through ten parse/serialise cycles.

**Result: byte-identical, every time.** Nothing escapes a block, and nothing inside one is
normalised. Every message shipped in this repository round-trips as well.

This is the one claim that can be settled mechanically, so it is settled first.

### Part 2 — information recovery

For each benchmark pair, an inventory of the information items the message carries, each
with a **predicate that reads the parsed AST**. An item counts as recovered only if a
program can pull it out without understanding English.

**Result: 55 of 55 items recovered.** From the equal-information prose baselines a program
can extract **zero** of them without an NLP pass — the prose contains the same facts, but
only a reader can get at them.

Density, same information either way:

| | items | wire | prose | tok/item | prose/item |
|---|---|---|---|---|---|
| total | 55 | 589 | 752 | 10.7 | 13.7 |

### Part 3 — where the tokens go

The wire form split into addressing, epistemics and payload, so the trade is visible rather
than asserted:

| | wire | without epistemics | without addressing | prose |
|---|---|---|---|---|
| total | 589 | 492 | 489 | 752 |

**The epistemic fields cost 97 tokens — 16% of the wire form.** They are the most expensive
thing in the format, and the point of showing this is that the saving is *net of* them: 21%
smaller than prose **while** carrying 97 tokens of confidence, unknowns and assumptions that
prose has to spell out in clauses no program can read.

If a future evaluation shows those fields do not improve outcomes, this table is where you
would look to decide what to cut.

### What neither script tests

Whether a **model** reading the wire form ends up as well informed as one reading the prose.
That needs an independent judge and a task suite ([spec/SPEC.md §25](../spec/SPEC.md)), and
it has not been run. The baselines here were written by the same author as the wire forms,
which is precisely the bias such an evaluation exists to remove.
