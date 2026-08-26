# Contributing to AgentRosetta

Thank you for considering it. This project is a language specification with a reference
implementation, so contributions are held to slightly unusual standards. They are all
stated below, and none of them is about style.

## The three rules

### 1. A change to the core vocabulary must clear the three-domain bar

The core — 14 acts, 14 slots, 12 markers, 7 header fields — is **frozen**, and staying
frozen is what keeps it learnable from a single prompt card.

To add anything to it you must show it is **demonstrably necessary in at least three
unrelated domains**, and re-run the fourteen-domain coverage matrix in
[spec/SPEC.md §24](spec/SPEC.md). A proposal that improves one domain and does nothing for
the other thirteen is a **profile**, not a core change. That is not a rejection — profiles
are the intended extension mechanism and are much easier to land.

`part`, `stop`, `sub`, `at`, `txt` and `mark` cleared this bar. Evidence grading, quorum,
approval chains and register did not.

### 2. Every "must" needs a diagnostic; every invariant needs an assertion

If the specification says something must hold, a validator has to be able to detect that it
does not. If [§23](spec/SPEC.md) gains an invariant, the suite gains an assertion.

**A rule that cannot be checked is not finished.** The diagnostic codes are listed in I-10.

### 3. Exceptions get registered

Axiom 2.9 (consistency over convenience) means one concept gets one mechanism. When a
special case is genuinely unavoidable, it goes in the **registered exceptions table**
(§23.1) with its reason. There are six today. Adding a seventh needs an argument; adding
several needs a redesign.

## Working on it

```bash
git clone https://github.com/Birfy/AgentRosetta.git
cd AgentRosetta
python3 agentrosetta.py        # self-test + demos, no dependencies
pytest                          # same suite via pytest
python3 bench/token_compare.py  # pip install tiktoken for real BPE counts
```

The implementation is a single dependency-free file on purpose: anyone should be able to
read the whole thing in one sitting and drop it into a project without a build step. Keep
it that way.

The assertions live inside `agentrosetta.py` next to the code they describe.
`tests/test_agentrosetta.py` is a thin pytest wrapper so CI can fail loudly.

## What is most valuable right now

**Not a feature. Evidence.**

The specification's central claims are not measured yet. [§25](spec/SPEC.md) specifies the
evaluation in full: task success at a fixed token budget across at least four domains, with
ablations that isolate which mechanism actually pays.

Running that and reporting the result is the most useful thing anyone can do here —
**including, and especially, if the result is that this was a bad idea.** The epistemic
fields are the most expensive part of the format. If they do not earn their tokens, they
should be cut, and we would rather find that out from data than from adoption failures.

Other high-value work, roughly in order:

- **Implementations in other languages.** TypeScript first; the grammar is a line
  classifier and is deliberately easy to port.
- **Profiles.** `evid`, `plan`, `neg`, `human`, `data`, `safety`, `craft` are sketched but
  not published as content-addressed packs.
- **Open problems.** Annotation anchors after a rewrite (R-12), and channel-size limits
  (R-11). Both are documented honestly in §26 with what we tried and where it still fails.
- **Adversarial review of the security model** (§18). We would rather hear about a hole here
  than anywhere else.

## Prose in this repository

All example text is original. **Do not contribute copyrighted passages**, not even short
ones, and not even as translation fixtures. The language can carry a chapter of a novel;
that is not a reason to put someone else's chapter in it.

## Conduct

Argue with the design, not with the person. Bring the failing case — a message that should
parse and does not, an invariant that does not hold, a domain the matrix cannot express.
Concrete beats confident.
