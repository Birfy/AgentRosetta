# Benchmarks

```bash
python3 bench/token_compare.py          # heuristic counts
pip install tiktoken                    # then real BPE counts
python3 bench/token_compare.py
```

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
