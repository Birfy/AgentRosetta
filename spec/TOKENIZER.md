# Designing a Wire Format Against a BPE Tokenizer

> What we measured, what we changed, and what we tried and rejected.
> Everything here is reproducible: `python3 bench/tokenizer_audit.py`.

A protocol for language models is unusual in that **its syntax is priced by a
tokenizer, not by a parser.** A keyword that reads as one word may cost four
tokens; a symbol that looks compact may cost three. None of this is visible from
the grammar, so it has to be measured.

This document records that measurement for AgentRosetta. The headline: **the
syntax was already close to its floor, the interesting savings were in how values
are spelled, and going beyond ASCII made things worse rather than better.**

---

## Method

Three tokenizers, because optimising against one is overfitting:

| | used by |
|---|---|
| `o200k_base` | GPT-4o generation |
| `cl100k_base` | GPT-4 / GPT-3.5 generation, and widely embedded |
| `p50k_base` | older Codex generation; a useful pessimist |

A candidate is only adopted if it is cheap in **all three**. Anything that is one
token in the newest tokenizer and three in an older one is not an optimisation,
it is a bet on which model the reader is running.

---

## Finding 1 — Non-ASCII is a portability trap

The obvious idea is that a single CJK character or a typographic symbol carries
more meaning per byte, so it should be cheaper. Measured across the three
tokenizers, counting only symbols that cost **exactly one token everywhere**:

| Class | 1 token everywhere | 1 token in `o200k` only | Worst case |
|---|---|---|---|
| **ASCII punctuation** | **17 / 17** | 0 | — |
| Latin-1 and typographic (`§ † · » ¶ °`) | 9 / 11 | 2 | `÷` = 1, 2, 2 |
| Arrows and maths (`→ ← ⇒ ∴ ≈`) | 2 / 11 | 5 | `⇒` = 1, 3, 3 |
| CJK single characters | 1 / 11 | 9 | `據` = 1, 3, 3 |
| Emoji | 0 / 6 | 0 | — |

**ASCII punctuation is the only class that is uniformly one token.** CJK looks
attractive on a modern tokenizer and costs two to three times as much on an older
one. Emoji are never cheap anywhere.

So the axiom "stay in-distribution" and the practical rule "use ASCII" turn out to
coincide, but **for a different reason than we assumed**. It is not that ASCII is
inherently better understood. It is that ASCII punctuation is the only part of the
symbol space that every tokenizer agrees is cheap.

There is a second, weaker argument, and it is worth stating as weaker: a model has
strong priors about the word `why` and correspondingly vague ones about `∵`.
That intuition may be right, but we did not measure it, so it is not the reason
for the rule.

---

## Finding 2 — The syntax is already near its floor

Decomposing a 24-message conversation, and asking what would be left if every
piece of syntax cost **zero**:

| | tokens | share |
|---|---|---|
| **syntax** — slot keys, act names, `~conf`, `key=`, `@` sigils | 245 | **16%** |
| naming — message ids and reference bodies | 411 | 27% |
| payload — the actual words | 845 | 56% |

**Even a syntax that cost nothing at all would only shrink the conversation by
16%.** Every scheme for compressing keywords is competing for a sixth of the
message; the rest is names and content, which no notation can shorten.

Within that sixth:

| | tokens | can it be reduced |
|---|---|---|
| slot keys | 64 | no — all 14 are already single tokens |
| act names | 25 | no — all 14 are already single tokens |
| `@` sigils | 48 | no — a reference needs a sigil |
| `~confidence` | 52 | to ~26, at the cost of readability |
| `key=` header fields | 56 | to ~28, at the cost of readability |

**All 14 acts and all 14 slots are one token in all three tokenizers.** That was
not by design — the words were chosen for readability — but it means the frozen
core needed no changes at all. The theoretical best case for redesigning the
markers is around **3.5% of a conversation**, paid for in legibility.

We did not take it.

---

## Finding 3 — Separators are expensive, and that one is worth fixing

Every separator forces a BPE split:

| | `o200k` | `cl100k` | `p50k` |
|---|---|---|---|
| `a1.7` | 4 | 4 | 4 |
| `a1-7` | 4 | 4 | 4 |
| `a1_7` | 4 | 4 | 4 |
| `a1:7` | 4 | 4 | 4 |
| **`obs7`** | **2** | **2** | **2** |

Message ids are about **14% of a long conversation** — they appear once as the
sender's own id and again in every `re=` and every cross-reference. Halving them
is the single largest lever in the format, and it costs nothing in legibility:
`obs`, `dba`, `release` are better agent names than `a1`, `a2`, `a3`.

Hence §5.3: letters are the agent, trailing digits the sequence. The dotted form
stays valid and is required when an agent name contains digits.

---

## Finding 4 — Value encoding is where the money actually is

Once the syntax is at its floor, what remains is how values are spelled. This is
where measurement pays, and none of it requires leaving ASCII.

**Timestamps.** ISO 8601 is a poor fit for a tokenizer:

| | tokens |
|---|---|
| `@t:2026-08-26T14:02:20Z` | 16 |
| `@t:20260826T140220Z` | 10 |
| **`@t:14:02:20`** (session declares the date) | **8** |

A conversation that stamps every observation carries eight of these. Declaring
`epoch = @t:2026-08-26` once in the handshake and writing times of day is worth
about **3%** on its own (§11.7).

**Spans.** URI query conventions are expensive and buy nothing here:

| | tokens |
|---|---|
| `#from=14:00&to=14:15` | 11 |
| **`#14:00-14:15`** | **8** |
| `#1400-1415` | 6 |

A span is opaque to Rosetta, so this needs no language change — only the habit of
not reaching for URL syntax when a range will do.

**Repeated references.** `@dash:grafana/cko-5xx` at 10 tokens, used four times, is
40 tokens for one idea. Binding it once with `def` costs 8 and then 2 per use.
This was never a language gap; the dictionary existed and the original transcript
simply did not use it.

---

## What this produced

| Change | Where | Worth |
|---|---|---|
| Elide derivable header parts | §6.2.1 | ~9% |
| Compact msg-ids, letters-only agents | §5.3 | ~6% |
| Bind repeated references with `def` | §14.2 | ~1% |
| Session-relative timestamps | §11.7 | ~3% |
| Compact span syntax | convention | ~1% |

Total on the long case: **1782 → 1437 tokens, 19% smaller**, flipping the
comparison against equally informative prose from +6% to −14%.

Nothing was removed but redundancy. The AST, the round trip and the human
rendering are identical at every step, which `bench/fidelity.py` verifies.

---

## What we rejected, and why

**Non-ASCII markers.** Measured. Cheap on one tokenizer, expensive on the others
(Finding 1). No adoption.

**Single-character replacements for `~hi`, `~mid`, `~lo`.** Available — `!`, `?`,
`^` and `±` are all one token everywhere — and worth about 1.7%. Rejected: each
of those characters already carries a meaning in the language or a strong prior
from elsewhere, and confidence is the field most likely to be read by a human
during an incident. **The cheapest field to write is not the one to make cryptic.**

**A shorter reply marker.** Measured and it does not exist: ` re=a1.2`, ` <a1.2`,
` ^a1.2` and ` re:a1.2` all cost five tokens. The cost is the identifier, not the
marker, so there was nothing to win.

**Renaming `notfound` to `missing`** to save its one extra token. Rejected as not
worth an alias in a frozen table. One token is not a reason to break a code that
somebody may already be matching on.

**Packing act and slot into one token.** BPE vocabularies do contain multi-word
entries, so a specific pairing could be made cheap on a specific tokenizer. This
is overfitting in its purest form and generalises to nothing.

---

## If you are designing your own

1. **Measure across at least three tokenizers before adopting any symbol.**
   One-tokenizer wins are bets, not optimisations.
2. **Compute your syntax floor first.** If keywords are a sixth of your traffic,
   redesigning them is a sixth-sized opportunity, and you will spend legibility
   to get part of it.
3. **Look at separators.** They are invisible in a grammar and expensive in a
   tokenizer. Identifiers are usually the largest structural cost.
4. **Look at value encodings before syntax.** Timestamps, ranges and URIs are
   often two to three times more expensive than they need to be, and fixing them
   costs no readability at all.
5. **Do not make your most human-read field your most cryptic one** to save 2%.

## Reproducing

```bash
pip install tiktoken
python3 bench/tokenizer_audit.py     # every table in this document
python3 bench/long_cases.py          # the end-to-end effect
python3 bench/fidelity.py            # proof that nothing was lost
```
