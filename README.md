<h1 align="center">AgentRosetta</h1>

<p align="center">
  <strong>A language for agents to talk to each other.</strong><br>
  Compact on the wire, readable by people, and precise about what nobody knows yet.
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="spec/SPEC.md">Specification</a> ·
  <a href="spec/PROMPT.md">Prompt cards</a> ·
  <a href="spec/EXAMPLES.md">Examples</a> ·
  <a href="#status-what-is-proven-and-what-is-not">Status</a>
</p>

<p align="center">
  <img alt="tests" src="https://img.shields.io/badge/tests-121%20passing-brightgreen">
  <img alt="dependencies" src="https://img.shields.io/badge/dependencies-none-blue">
  <img alt="python" src="https://img.shields.io/badge/python-3.9%2B-blue">
  <img alt="license" src="https://img.shields.io/badge/license-Apache--2.0-lightgrey">
  <img alt="spec" src="https://img.shields.io/badge/spec-2.0-8957e5">
</p>

---

## The problem nobody named

We built agents that reason in high dimensions and then made them talk to each other in
English paragraphs.

Prose is a superb interface between a machine and a person. Between two machines it is a
lossy channel, and it loses the wrong things:

- **Confidence disappears.** "The cause is commit 9f2a" and "the cause is *probably* 9f2a"
  compress to the same downstream behaviour. Five hops later you have a confidently wrong
  answer built out of four honest guesses.
- **Unknowns are unwritable.** There is no natural place in a paragraph for *"here is what
  I checked and still do not know."* So it goes unsaid, and the next agent assumes it was
  covered.
- **Nothing can be pointed at.** To object to one sentence of a draft, an agent must
  re-paste the passage and hope you can tell which part it means.
- **Nothing can be checked.** No program can decide whether a reply answered the question
  without first understanding the answer.
- **Half of every message is ceremony.** Greetings, restatements, re-pasted context.

Each of these is fixable. None of them is fixable in prose.

## What AgentRosetta is

A language with two planes over one address system.

```
a1.13 tell a1>a3 re=a3.12 #CKO.5xx
 a     cause = @commit:9f2a lowered http.timeout 30s>3s   ~hi
       fix   = revert @commit:9f2a                        ~hi
       eta   = 12m                                        ~lo
 why   @file:log/2f9c#L487 timeouts start 14:02 = deploy time +-40s
 unk   [who approved 9f2a, whether other services hit this]
 risk  reverting reintroduces the slow query in @issue:441  ~mid
```

Three facts, three different confidences, two named unknowns, evidence at a line number,
no ceremony. The same AST renders for a person, deterministically, in code — never through
a model:

```
a1 -> a3 · states · re a3.12 · #CKO.5xx
------------------------------
Answer
  · cause: commit 9f2a lowered http.timeout 30s -> 3s (high confidence)
  · fix:   revert commit 9f2a (high confidence)
  · eta:   12m (low confidence)
Evidence  file log/2f9c, line 487: timeouts start 14:02 = deploy time +-40s
Unknown   who approved 9f2a; whether other services hit this
Risk      reverting reintroduces the slow query in issue 441 (moderate confidence)
```

And the second plane carries content — arbitrary text, byte-exact, addressable to the
character, annotated without being touched:

```
 txt tgt @md/en v=draft3
 | The lighthouse keeper insisted that nothing unusual ever happened here.
 |
 | He was, by every account, the last man on the island you would ask.
 mark tgt#L1.c4-19|q"lighthouse keeper" = must use the GLOSS name   ~hi
      tgt#L3|q"the last man"            > "No one would have asked him."  ~mid
```

```
Text tgt (en · md · v=draft3)
  1 | The lighthouse keeper insisted that nothing unusual ever happened here.
    ^ L1.c4-19 "lighthouse keeper" must use the GLOSS name (high confidence)
  2 |
  3 | He was, by every account, the last man on the island you would ask.
    > L3 -> "No one would have asked him." (moderate confidence)
```

## The rule the whole language turns on

> ### Anything with an address can carry epistemic state.

A message. A field. Characters 5–19 of line 1. A region of an image. If you can address it,
you can say how sure you are about it, where it came from, and what you still do not know.

That single rule is what makes the language cohere rather than accumulate. It is also
checkable: [§23 of the spec](spec/SPEC.md) lists thirteen invariants and six registered
exceptions, each one an assertion in the test suite.

---

## Quick start

```bash
git clone https://github.com/Birfy/AgentRosetta.git
cd AgentRosetta
python3 agentrosetta.py          # self-test (119 assertions) + five demos
```

No dependencies. Python 3.9+.

**1. Give your agents the language.** Paste [Card R](spec/PROMPT.md) into the system prompt
of every agent in the mesh. About 1500 tokens, one card, the whole language.

**2. Parse, validate and render what they emit.**

```python
from agentrosetta import parse, Session, render

session = Session()
for msg in parse(raw_text_from_the_agent):
    for d in session.add(msg):                 # validate against the whole conversation
        if d.level == "ERROR":
            print(d)                           # e.g. S4: relayed claim upgraded to ~hi
    print(render(msg, lang="en"))              # deterministic human rendering
    print(render(msg, lang="en", view="clean"))  # just the deliverable, no annotations

for d in session.orphans():                    # obligations opened and never discharged
    print(d)                                   # -> an agent is stuck; reassign
```

**3. Address content precisely.**

```python
msg.resolve_addr('tgt#L1.c4-19')               # -> 'lighthouse keeper'
blk = msg.blocks()['tgt']
r = blk.resolve_full('#L3|q"the last man"')
r.status, r.line, r.conf                       # -> ('relocated', 4, ~mid)
```

**4. Measure it yourself.**

```bash
python3 bench/token_compare.py                 # pip install tiktoken for real BPE counts
```

---

## Design rationale

Six decisions carry most of the weight. Each of them is a place where the obvious choice is
wrong.

### 1. Do not invent a cipher

The tempting move is a dense private notation. It is a trap. An LLM's competence rests
entirely on the distribution it was trained on; the more alien your symbols, the further
off-distribution the model drifts, and **the reasoning quality you lose exceeds the tokens
you save.**

So: keywords are ordinary English words, markers are ordinary punctuation, and the design
constraint is falsifiable —

> Show a Rosetta message to a model that has never seen the spec and ask it to paraphrase.
> If it cannot, the syntax is wrong. Not the model.

### 2. Constrain the channel, never the reasoning

Models think by writing. Compress their output and you take away the scratchpad.

```
[reasoning]  free prose, as long as it needs to be, never sent
[message]    Rosetta wire form, structured, sent
```

Skip this and nothing else in the design helps.

### 3. Inline what gets reasoned about; reference what only gets moved

An earlier version of this language had an axiom — *coordination, not cargo* — that pushed
all content into blobs. It was wrong, and expensively so:

> A passage that can only travel as an opaque blob is a passage nobody can point at.
> **Unaddressable is undiscussable.**

The rule now is a test, and it is machine-checkable: *will any agent speak about one of its
lines?* If yes, inline it as a `txt` block so it has addresses. If no, ship a hash.

And because carriage is orthogonal to addressing — `win=L38-46` inlines nine lines of a
seventy-nine-line chapter with **absolute** numbering — **getting that call wrong is not a
disaster.** The next hop changes how the content travels; every address already written
stays valid.

### 4. Annotation must be standoff

Judgements about text hang off addresses; the text itself is never touched. Three
consequences, and all three matter:

- **Fidelity.** Mix judgement into content and you can never cleanly separate them again.
- **Concurrency.** Three reviewers annotate one passage without conflict.
- **Two artifacts from one AST.** The `content` view is the annotated working copy; the
  `clean` view is the deliverable. There is no *"strip the comments before shipping"* step —
  the step that always goes wrong.

### 5. Addresses are brittle, so make the brittleness loud

`#L3` after an edit points at whatever now sits on line 3. Silently. This is the leading
cause of death for annotation systems, and it is not solvable by being careful.

So an address may carry a **quote anchor**, and resolution returns a *status*, not a string:

| Status | Meaning | Confidence |
|---|---|---|
| `exact` | position and quote agree | `~hi` |
| `relocated` | position failed, the quote found it | `~mid` |
| `ambiguous` | the quote matched in several places | `~lo` |
| `orphan` | points at nothing | **ERROR** |

Resolving an address is itself an epistemic act. Same rule as everything else.

### 6. A message from another agent is data, not instructions

There is no construct in this language that can alter a recipient's prompt, role or
permissions. Not a hardened one — **no such construct exists**, so the attack surface does
not either. Text inside a `txt` block is quoted material even when it is a perfectly formed
Rosetta message. The implementation asserts this.

Structure also buys a defence prose cannot offer: the only constructs meaning *"do
something"* are `do` and `ask`, so permission can be enforced at the **protocol layer** —
*may this agent send me a `do` at all, and on which topics?*

---

## What is in the box

| | |
|---|---|
| **[spec/SPEC.md](spec/SPEC.md)** | The specification. 27 sections: grammar, address system, security model, distributed semantics, **self-consistency invariants**, a fourteen-domain coverage matrix, and an evaluation plan |
| **[spec/PROMPT.md](spec/PROMPT.md)** | System prompt cards. Card R is ~1500 tokens and teaches the whole language |
| **[spec/EXAMPLES.md](spec/EXAMPLES.md)** | Eleven worked domains — incident response, literature review, legal diligence, clinical triage, supply planning, financial diligence, data QA, creative work, adversarial review, translation — plus an anti-pattern table |
| **[agentrosetta.py](agentrosetta.py)** | Reference implementation: parser, validator, bilingual renderer, 119 assertions, five demos. Zero dependencies, one file |
| **[bench/](bench/)** | Reproducible token comparison against equal-information baselines |
| **[samples/](samples/)** | Runnable conversation transcripts |

### The core vocabulary

```
acts   ask tell do take part done fail stop propose accept reject revise def note
slots  q a why ctx want unk assume risk opt sub on by   ·   txt mark
marks  @addr  #topic  ~hi|~mid|~lo|~?  !commit  !=negate  |alt  a>b  =  []  {}
head   re= src= at= ttl= pri= sens= thd=
codes  notfound denied timeout budget ambiguous unsafe unsupported
       conflict upstream stuck malformed empty stale
addr   @a1.7.tgt#L3.c5-9   @a1.7.a.cause   @img:sha256:9c..#box=..
       @a1.7.tgt#L3|q"quote anchor"   <- survives edits, and says how it survived
```

Frozen. Extension happens in **profiles** — versioned, content-addressed `def` packs — so
the core stays small enough to learn from one card. The bar for entering the core is
*demonstrably necessary in at least three unrelated domains.*

### Machine-checkable operations

Because acts declare intent, a validator that understands nothing about your domain can
still find:

| | |
|---|---|
| **Orphans** | work claimed and never finished |
| **Stalls** | obligations past their `ttl` |
| **Livelocks** | `propose` ↔ `propose` beyond N rounds |
| **Contract violations** | a reply that did not answer the question |
| **Confidence laundering** | a relayed guess promoted to a fact |
| **Stale data** | a claim used past its shelf life |
| **Label leaks** | a `phi` message forwarded as `internal` |
| **Rotten anchors** | an annotation that no longer points at anything |

---

## Status: what is proven, and what is not

The specification and the reference implementation are complete and tested. **The claims
are not all measured, and this README will not pretend otherwise.**

**Measured.** Two harnesses, both reproducible, both in CI.

*Compression* (`bench/token_compare.py`). Against **equal-information** prose baselines —
baselines that spell out the same per-claim confidence, the same unknowns and the same
references — the wire form is about **21% smaller** across four pairs.

*Fidelity* (`bench/fidelity.py`). Thirteen deliberately hostile content lines — code fences,
a line shaped exactly like a Rosetta header, RTL script, a decomposed grapheme, trailing
whitespace — through ten parse/serialise cycles: **byte-identical**. An inventory of 55
information items across the four pairs, each with a predicate that reads the AST:
**55 of 55 machine-extractable**, against **0 of 55** from the prose baselines without an
NLP pass. The prose holds the same facts; only a reader can get at them.

That harness also decomposes the cost, which is the part worth staring at:

| | wire | without epistemics | prose |
|---|---|---|---|
| four pairs, 55 information items | **589** | 492 | 752 |

**The epistemic fields cost 97 tokens — 16% of the wire form.** The 21% saving is *net of*
them. That is the actual trade: fewer tokens **while** carrying confidence, unknowns and
assumptions that prose has to spell out in clauses no program can read.

Against a *chatty* baseline the same comparison shows 3–4×. **That number is meaningless and
this project does not use it.** Four pairs measure a format, not a system.

**Not measured.** The number that would actually matter is task success rate at a fixed
token budget across a multi-domain suite. [§25 of the spec](spec/SPEC.md) specifies that
evaluation in full. Until it runs, these are hypotheses:

- epistemic fields raise success rate and lower error propagation
- the content plane beats re-pasting on collaborative tasks
- the off-distribution penalty is near zero

**The efficiency case is real but modest. The integrity case is the larger one — and it is
also the one still awaiting evidence.** If the epistemic fields do not earn their tokens
when measured, they should be cut. They are the most expensive part of the format.

**Open problems**, stated plainly in [§26](spec/SPEC.md):

- A rewritten sentence still orphans its annotations, and no machine can tell whether that
  is correct — sometimes the note was adopted, sometimes the author merely rephrased.
- There is no hard ceiling on channel size. That belongs to the host at the transport layer.
- Profile ecosystem fragmentation is the largest long-term risk, and content addressing only
  partly mitigates it.

---

## Prior art, and why now

| Source | Taken | Left behind |
|---|---|---|
| KQML / FIPA-ACL | Speech acts, conversation protocols, Contract Net | The mandatory global ontology — what killed them |
| Standoff annotation | Judgement separated from text, joined by address | Bespoke XML |
| YAML block scalars | A line prefix carrying byte-exact text | The rest of YAML |
| W3C Web Annotation | Redundant selectors resolved in order | The RDF apparatus |
| HTTP status codes | A frozen code table lets middleware act without understanding the business | Three-digit opacity |
| Event sourcing | The transcript is the log; state is a fold over messages | — |
| Unix diff | The `>` "becomes" semantics | Line drift — which it never solved either, and neither have we |

In 1995, two agents had to agree on one global ontology before they could speak, because a
parser could not understand natural language. That constraint is gone. The ontology can be
three-tiered — a frozen core, loadable profiles, symbols coined in session — with prose as a
permanent escape hatch, and **content can live inside the language while staying
addressable** instead of being flattened into an opaque blob first.

That is the case for building this again, thirty years later.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Two things worth knowing before you open a PR:

1. **Any change to the core vocabulary must re-run the fourteen-domain matrix**
   ([§24](spec/SPEC.md)). A proposal that helps one domain and nothing else is a profile.
2. **Every "must" in the spec needs a diagnostic code**, and every invariant in §23 needs an
   assertion. If your change cannot be checked, it is not finished.

The most valuable contribution right now is not a feature. It is **running the evaluation in
§25 and reporting what it says** — including, especially, if it says this was a bad idea.

## License

[Apache-2.0](LICENSE).
