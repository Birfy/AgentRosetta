# AgentRosetta 2.0 — Language Specification

> A general-purpose language for agent-to-agent communication. It carries both
> **coordination** (who, what act, how sure, what is unknown, who acts next) and
> **content** (arbitrary text or data), over one shared address system.
> One AST renders to a compact wire form for machines and to readable prose for
> people. Neither rendering is an afterthought.

**Status.** Specification and reference implementation are complete and tested.
The efficiency and quality claims are *hypotheses* until the evaluation in §25 runs.
This document distinguishes what is designed from what is measured, everywhere.

---

## The rule the whole language turns on

> ### Anything with an address can carry epistemic state.

A message, a slot, a binding, characters 5–9 of line 3 of a text block, a region of
an image — if you can address it, you can say how sure you are about it, who it came
from, and what you still do not know. Version 1.1 gave that machinery to the
coordination layer only. 2.0 gives it to everything. That is what "self-consistent"
means here, concretely, and §23 makes it checkable.

---

## 0. Contents

| § | | § | |
|---|---|---|---|
| 1 | Goals and non-goals | 15 | Interaction patterns |
| 2 | Axioms | 16 | Failure taxonomy |
| 3 | **The two planes** | 17 | Human rendering |
| 4 | Three-tier vocabulary | 18 | Security and trust |
| 5 | Lexicon | 19 | Distributed semantics |
| 6 | Grammar | 20 | Conformance levels |
| 7 | Tolerant parsing | 21 | Transport and handshake |
| 8 | Speech acts | 22 | Versioning |
| 9 | Slots | 23 | **Self-consistency invariants** |
| 10 | Values and types | 24 | Domain coverage matrix |
| 11 | **The address system** | 25 | Evaluation plan |
| 12 | **The content plane** | 26 | Risks and open problems |
| 13 | Routing and scale | 27 | Prior art |
| 14 | Epistemics, dictionary, `want` | | |

---

## 1. Goals and non-goals

### 1.1 The problem

Multi-agent systems talk in prose. That costs seven things:

| Problem | What it looks like | Answer |
|---|---|---|
| **Token cost** | Greetings, restating the question, re-pasting context | Drop ceremony; reference instead of paste (§11) |
| **Attention dilution** | The one line that matters buried in 40k of context | Demand-paged `deref` (§11.4) |
| **Ambiguous intent** | "Handle it" → the wrong thing gets handled | Explicit acts + `want` contracts (§8, §14.3) |
| **Epistemic collapse** | A's guess reads exactly like A's fact | Confidence, unknowns, assumptions as fields (§14) |
| **Uncheckable replies** | No way to tell if the answer answered | `want` schema validation (§14.3) |
| **No operability** | Stalls, orphans and loops are invisible | Obligation state machine (§8.3, §19) |
| **Unaddressable content** | Cannot point at one sentence of a draft | **Content plane + addresses (§3, §11, §12)** |

### 1.2 The one that matters most

Epistemic collapse is badly underrated. In a five-hop agent chain, each hop that
launders a 60%-confidence guess into a flat assertion produces, at the end, a
**confidently wrong** answer. Prose makes hedging expensive and socially awkward —
it costs a whole clause. A protocol makes it a two-token field.

Three value propositions, in order of importance:

1. **Integrity** — epistemic state survives agent hops. *Most important.*
2. **Collaborability** — content can be pointed at, annotated, and edited by proposal.
3. **Efficiency** — fewer channel tokens, mostly from references rather than shorthand.

Optimise only for the third and you will build something cheaper *and* wronger.

### 1.3 Non-goals

- **Not a compression scheme.** Shortening words moves the model off-distribution;
  the reasoning quality lost exceeds the tokens saved. No invented glyphs, no emoji
  encodings, no base64, no single-letter keywords. **Prompt length is not an
  optimisation target** — completeness and consistency come first.
- **Not a global ontology.** FIPA-ACL and KQML required agreement on one ontology up
  front and died of it. Here the ontology is three-tiered: a frozen core, loadable
  profiles, and symbols coined per session (§4).
- **Not a binary container.** The wire form is always text. Images, audio and model
  weights travel as `@ref`. That is a transport choice, not an expressiveness limit (§12.7).
- **Not opaque.** A construct that cannot be rendered deterministically for a human
  does not belong in the language (§17).
- **Not a constraint on reasoning.** It governs what crosses the channel, never what
  happens inside an agent (§2.6).

---

## 2. Axioms

### 2.1 Stay in-distribution
Keywords are ordinary English words; markers are common ASCII punctuation. Both are
single tokens in every mainstream BPE, and models hold strong priors about them.

> **Falsifiable test.** Show a Rosetta message to a model that has *never seen this
> spec* and ask it to paraphrase. If it cannot, the syntax is wrong — not the model.

### 2.2 Isomorphic dual surface
One AST, many renderers: wire, English, Chinese, filtered views. **Renderers are
ordinary code, never a model** — otherwise the audit chain is broken at its root.

### 2.3 Reference beats copy
The same content must never appear twice in a channel. The second time, point (§11.3).

### 2.4 Epistemic state is first class
Confidence, evidence, assumptions and **known unknowns** get syntax, cheap enough
that omitting them is never justified by economy.

### 2.5 Fidelity beats convenience
Every byte inside a `txt` block is the author's; the parser may not rewrite it (§7.1).
Distorting meaning to fit the grammar is the worst possible outcome.

### 2.6 Two channels: thinking ≠ speaking
```
[reasoning]  free prose, as long as it needs to be, never sent
[message]    Rosetta wire form, structured, sent
```
**The channel is constrained; the reasoning is not.** Skip this and nothing else helps.

### 2.7 Inline what gets reasoned about; reference what only gets moved

Version 1.1 said "coordination, not cargo" and pushed all content into blobs. That was
wrong, and expensively so: content you cannot address is content you cannot discuss.

> **Content that will be pointed at, annotated or edited goes inline as a `txt` block,
> because it must be addressable. Content that only needs to move goes in a blob.
> Test: will any agent speak about one of its lines?**

This is machine-checkable: a large block with no `mark` on it and no binding referring
to it raises `I022` — *nobody is reasoning about this; it is cargo.*

### 2.8 Design for the errors LLMs actually make
Inconsistent indentation, fullwidth punctuation, unclosed brackets, prose wrapped
around the block. The parser must recover (§7).

### 2.9 Consistency over convenience
One concept, one mechanism, everywhere. Invariants are listed and checked in §23. When
"one more special case would be handy" collides with "keep the mechanism uniform",
choose the latter. **Every exception in this specification is registered in §23.1.**

---

## 3. The two planes

A message has two planes that **share one address system and one epistemic vocabulary**.

```
+-- COORDINATION ------------------------------------------------------+
|  q  a  why  ctx  want  unk  assume  risk  opt  sub  on  by           |
|  who to whom, which speech act, how sure, what is missing, who next  |
+----------------------------------------------------------------------+
                      ^   one address system (§11)
+-- CONTENT -----------------------------------------------------------+
|  txt   verbatim, structured, addressable to the character            |
|  mark  standoff annotation over an address                           |
+----------------------------------------------------------------------+
```

### 3.1 Where they meet

At the address. Any span of a content block can be pointed at from the coordination plane:

```
a2.7 tell a2>a1 #ch1
 txt tgt @md/zh v=draft3
 | The lighthouse keeper insisted that nothing unusual ever happened here.
 |
 | He was, by every account, the last man on the island you would ask.
 mark tgt#L1.c4-19 = must use the GLOSS name here                    ~hi
      tgt#L3       > "No one on the island would have asked him."     ~mid
 a    faithful != literal                                             ~hi
 unk  [whether L3 now reads too colloquial]
```

`tgt#L1.c4-19` points at exactly `lighthouse keeper`. `mark` is **standoff
annotation**: the judgement hangs off an address and the text is not touched. This is
how corpus annotation has worked for thirty years, and for the same reasons.

### 3.2 Why annotation must be standoff

1. **Fidelity** (axiom 2.5) — mix judgement into the text and you can never cleanly
   separate them again.
2. **Concurrent annotators** — translator, terminologist and stylist can each annotate
   the same passage without conflict.
3. **Separable views** — the `clean` view emits the **deliverable**; the `content` view
   emits the annotated working copy. One AST, two artifacts, no post-processing step.

### 3.3 The content plane is not an escape hatch

Version 1.1 had an `nl` slot meaning "structure failed, here is prose". 2.0 removed it,
because it conflated two different things:

- *"structure does not apply here"* — a **pragmatic** signal
- *"here is some text"* — a **content** carrier

The second is the real need, and it deserves structure: lines, paragraphs, addresses —
not an opaque string. Today `txt "one line"` is the short form and `txt name @fmt/lang`
plus `|` lines is the block form: **one slot, one address space, two lengths**
(invariant I-3).

---

## 4. Three-tier vocabulary

```
+-- L-core ------------------------------------------------------------+
|  14 acts + 14 slots + 12 markers + 7 header fields. FROZEN.          |
+----------------------------------------------------------------------+
+-- L-profile ---------------------------------------------------------+
|  Named, versioned, content-addressed `def` packs. Loaded per session. |
|  plan/ evid/ neg/ human/ data/ safety/ craft/ ...                    |
+----------------------------------------------------------------------+
+-- L-local -----------------------------------------------------------+
|  Symbols coined inside one session with `def`. Disposable.           |
+----------------------------------------------------------------------+
```

**A profile is just a named, versioned, content-addressed `def` pack.** Extension and
compression become the same mechanism, so the language needs no separate plugin concept.

### 4.1 Standard profiles

| Profile | Covers | Example symbols |
|---|---|---|
| `plan/1.0` | Task trees, dependencies, milestones, budgets | `DEP` `MILESTONE` `CRIT` |
| `evid/1.0` | Evidence grading, citation rules, reproducibility | `PRIMARY` `HEARSAY` `CITE` `REPRO` |
| `neg/1.0` | Tendering, bidding, auctions, voting, quorum | `BID` `AWARD` `QUORUM` |
| `human/1.0` | Approval, escalation, clarification, view hints | `APPROVE` `ESCALATE` `READBACK` |
| `data/1.0` | Schema, sampling, drift, nulls | `SCHEMA` `SAMPLE` `DRIFT` |
| `safety/1.0` | Sensitivity, compliance, auditability, reversibility | `PII` `PHI` `IRREVERSIBLE` |
| `craft/1.0` | Writing and translation: register, taste, alignment | `VOICE` `TASTE` `ALIGN` `GLOSS` |

Profiles add **symbols and conventions only**; they never change the grammar. Any parser
can parse any Rosetta message even if it knows none of the symbols — an unknown symbol is
an opaque atom, resolved by `deref(@D:SYM)` or by a human.

### 4.2 A profile may constrain how the core is used

This is the right place to encode domain judgement:

```
 TASTE   = a choice of taste, not of fact: never carry ~conf; use opt + why + txt
 HEARSAY = an unsourceable claim. Any HEARSAY assertion is capped at ~lo
```

Not new syntax — a tightening at the semantic layer.

### 4.3 The bar for entering the core

> It must be demonstrably necessary in **at least three unrelated domains**.

`part`, `stop`, `sub`, `at`, `txt` and `mark` cleared that bar. Evidence grading, quorum,
approval chains and register did not — they are profiles.

---

## 5. Lexicon

### 5.1 Character set and language

UTF-8. **Markers, act names, slot names, binding keys and symbols are ASCII. Values,
strings and `txt` block content may be any language.**

This split is deliberate and is not Anglocentrism:

- Keys are **machine-facing** — matched against `want` contracts, indexed by validators,
  stable across models, and in-distribution (axiom 2.1).
- Values and body text are **content** — Chinese, Arabic, formulae, code, carried as written.
- Key names are **localised by the renderer** (§17), so a Chinese reader sees
  "答案 / 依据 / 未知", not `a / why / unk`.

**The wire is English; the human surface is the reader's own language.** That is what the
name means.

### 5.2 Markers (12, frozen)

| Marker | Name | Meaning |
|---|---|---|
| `@` | ref | Reference: message, slot, address, file, blob, time, role (§11) |
| `#` | topic / span | Topic namespace; span separator inside an address |
| `~` | conf | Confidence, modifying the value before it |
| `>` | to / becomes | Route separator; "to/causes" in a value; "becomes" in a `mark` |
| `=` | bind / annotate | Key–value binding; "annotate" in a `mark` |
| `!=` | negate | **Negative claim**: `cause != @commit:9f2a` |
| `!` | commit | I will actually do this, not merely recommend it |
| `?` | unknown | Unknown value; optional key inside `want` |
| `\|` | alt | Alternatives in a value or an address; **at line start, a content line** |
| `[ ]` | list | List |
| `{ }` | map / shape | Map; a schema inside `want` |
| `"` | string | String |

`>`, `=` and `|` each carry more than one reading. All are **disambiguated by position
and never co-occur**: route `>` appears only in a header, content `|` only at line start,
`mark` operators only inside a `mark` slot (invariant I-4).

### 5.3 Identifiers

```
agent-id ::= [a-z][a-z0-9_]*        a1, planner, radiology_agent
msg-id   ::= agent-id "." [0-9]+    a1.7, planner.23
block-id ::= [a-z][a-z0-9_]*        body, src, tgt, rows
symbol   ::= [A-Z][A-Z0-9_]+        CKO, PHI, GLOSS
```

> **A msg-id must be prefixed with the sender's agent-id.** Concurrent numbering cannot
> collide, `re=a1.7` is never ambiguous, and the msg-id doubles as an idempotency key (§19).

**Symbols and reserved words are case-sensitive.** Reserved words are lowercase, symbols
uppercase, so `SRC` (a symbol) and `src` (a header field) are different names that never
occupy the same syntactic position.

### 5.4 Confidence literals

```
conf ::= "~" ( "hi" | "mid" | "lo" | "?" | float )
```

| Literal | Meaning | Roughly |
|---|---|---|
| `~hi` | I would bet on this | ≥ 0.85 |
| `~mid` | I lean this way | 0.4 – 0.85 |
| `~lo` | One possibility among several | < 0.4 |
| `~?` | I genuinely cannot estimate | — |
| `~0.85` | Numeric — **only with a real calibration source** | — |
| omitted | Equivalent to `~hi` | — |

Three grades rather than numbers because LLMs are poorly calibrated at fine granularity
but tolerably ordinal — and because `~hi` is two tokens where `~0.85` is four. Cheaper
*and* more honest.

---

## 6. Grammar

### 6.1 Top level

```ebnf
document     ::= ( message | junk )*
message      ::= header LF body

header       ::= msg-id SP act SP route [ SP topic ] { SP hfield }
route        ::= agent-id ">" target { "," target }
target       ::= agent-id | "*" | topic | "@role:" name | "@grp:" name
topic        ::= "#" name { "." name }
hfield       ::= hkey "=" atom
hkey         ::= "re" | "src" | "at" | "ttl" | "pri" | "sens" | "thd" | "x_" name

body         ::= { slotline | contline | markline | continuation }
slotline     ::= WS* slotkey SP slotvalue LF
contline     ::= WS* "|" [ SP ] <verbatim to end of line> LF
continuation ::= WS* <first word is not a slotkey, not "|", not a header> text LF
```

### 6.2 Slot values

```ebnf
slotvalue    ::= binding | blockhdr | markline | shape | reflist | list | text

binding      ::= name WS* [ "!" ] "=" WS* text [ conf ]     -- at most one per line
blockhdr     ::= [ block-id ] [ "@" fmt [ "/" lang ] ] { SP name "=" atom }
              |  string                                      -- inline short form
markline     ::= addr WS* ( "=" | ">" ) WS* text [ conf ]
shape        ::= "{" [ field { "," field } ] "}" | act { "|" act }
field        ::= name [ "?" ] [ ":" type ]
reflist      ::= ref { ( SP | "," ) ref }
list         ::= "[" [ expr { "," expr } ] "]"
```

### 6.3 Three disambiguation rules

These three resolve every ambiguity, and none of them depends on indentation.

1. **A binding's value runs to end of line**, with an optional trailing `~conf`, and there
   is at most one binding per line. So
   `a cause = @commit:9f2a lowered timeout 30s>3s ~hi` needs no quoting and no escaping.
2. **A leading `|` is a content line.** Every byte after `| ` belongs to the current `txt`
   block, until a line that does not start with `|`. **There is no closing delimiter, so
   no content can escape a block** — not a header-shaped line, not a code fence, not
   another entire Rosetta message.
3. **Whether the first word is a known slot key** decides new slot vs. continuation. The
   slot keys are a closed set, so the parser is a line classifier.

---

## 7. Tolerant parsing

The parser's job is not to reject illegal input. It is to recover the most meaning from
the mistakes LLMs actually make.

| Mistake | Behaviour |
|---|---|
| Inconsistent or missing indentation | Indentation is advisory and carries no meaning |
| Unknown word at line start | Treated as a continuation of the slot above |
| Prose wrapped around the block | Discarded, or captured into an implicit `txt` block |
| Markdown fences (coordination plane) | Stripped |
| Fullwidth `＞＝＃＠～，：` (coordination plane) | Accepted at structural positions |
| Unclosed `]` `}` `"` | Closed implicitly at end of line, `WARN` |
| `slot:` / `- slot:` / `1. slot:` | Decoration stripped, then matched |
| A stray `\|` line with no `txt` header | Opens an implicit `body` block, `INFO P004` |
| No Rosetta at all, just prose | Wrapped as `note` + `txt`, `WARN`, **never an error** |

### 7.1 Content lines are exempt from every normalisation

> **A `|` line gets no NFC folding, no fullwidth substitution, no fence stripping, no
> decoration removal, no whitespace adjustment.**

This follows from axiom 2.5, and it is not theoretical. The first version of the reference
implementation normalised the whole document and rewrote the Chinese comma `，` inside body
text. **Byte-exact fidelity has to be a parser invariant, not an author's discipline.**

---

## 8. Speech acts

Fourteen, frozen.

| Act | Meaning | Legal replies | Closes the obligation |
|---|---|---|---|
| `ask` | Request information | `tell` `part` `fail` `reject` `ask` | tell/fail/reject |
| `tell` | Provide information | — | — |
| `do` | Request an action | `take` `part` `done` `fail` `reject` `propose` | done/fail/reject |
| `take` | I claim this work (the obligation stays on the original `do`) | `part` `done` `fail` | no |
| `part` | Progress or partial result | — | **no** |
| `done` | Finished, here is the result | — | yes |
| `fail` | Could not; `why` **must** start with a code (§16) | — | yes |
| `stop` | Withdraw my request, or abort work in progress | `done` `fail` `note` | yes |
| `propose` | Suggest a plan or an edit | `accept` `reject` `propose` | accept/reject |
| `accept` | Agree | — | yes |
| `reject` | Decline; `why` **must** start with a code | — | yes |
| `revise` | Correct or retract a message **of your own** | — | — |
| `def` | Bind symbols, or load a profile | — | — |
| `note` | FYI, no reply expected | — | — |

### 8.1 `revise` is the circuit breaker for error propagation

```
a1.19 revise a1>a3 re=a1.13
 a    cause != @commit:9f2a       ~hi
 why  conflict @a3.9#L12 the 5xx curve did not move after the rollback
 unk  [the actual cause]
```

After a `revise`, references to the revised message **resolve to the revision** by default;
`@a1.13@orig` retrieves the original. Any agent holding a cached value must recompute.
**The error is cut off at the source rather than discovered downstream.**

Note the `!=`. In 1.1 a negative claim could only be prose ("not 9f2a"), which no machine
could read as a negation. Now it is grammar.

### 8.2 Why `part` and `stop` are core

Not software-specific — every domain has long-running work:

- A literature review over 200 papers must report *"80 screened, tentative finding X `~lo`"*.
- Legal due diligence that finds a fatal defect must **stop** the parallel work and save real money.
- A triage agent must withdraw a request when the patient's state changes.
- Without `stop`, a runaway agent cannot be killed.

**Receiving `stop` obliges you to answer `done` (stopped) or `fail` (could not). Silence
is not a legal response.**

### 8.3 The obligation state machine

`ask`, `do`, `propose` and `stop` open a pending obligation. The operational payoff:

| Detection | Condition | Action |
|---|---|---|
| **Orphan** | `take` with no eventual `done`/`fail` | Agent is stuck — reassign |
| **Type mismatch** | An `ask` answered by a `done` | Routing bug — alert |
| **Stall** | Obligation older than its `ttl` | Escalate or `stop` |
| **Livelock** | `propose` ↔ `propose` beyond N rounds | Send to a human or an arbiter |
| **Silent loss** | Fewer replies than targets on a broadcast `ask` | Resend; it is idempotent (§19) |

---

## 9. Slots

Fourteen, frozen. Twelve coordination, two content.

| Slot | Plane | Meaning |
|---|---|---|
| `q` | coord | What is being asked |
| `a` | coord | Result, as `key = value` lines |
| `why` | coord | Evidence and reasoning; required on `fail`/`reject`, with a code |
| `ctx` | coord | References — never re-paste what they contain |
| `want` | coord | The shape the reply must have (§14.3) |
| `unk` | coord | **Known unknowns**; an empty one is itself a claim |
| `assume` | coord | What you proceeded as-if, which may be wrong |
| `risk` | coord | What could go wrong |
| `opt` | coord | Alternatives |
| `sub` | coord | Subtasks, owners, `on=` dependencies |
| `on` | coord | Precondition or trigger |
| `by` | coord | Limit: time, money, tokens, retries, sample size |
| **`txt`** | **content** | **Byte-exact, addressable content block (§12)** |
| **`mark`** | **content** | **Standoff annotation or edit proposal over an address (§12.3)** |

`txt` and `mark` may repeat within a message (`txt` blocks are distinguished by
`block-id`). Every other slot appears at most once.

### 9.1 `unk` versus `assume`

Deliberately separate, because the downstream action differs:

- `unk [x]` = **I do not know x**, and I know that → someone should go **find out**.
- `assume x=v` = **I proceeded as if x=v**, which may be wrong → someone should **verify**.

Collapse them and the next agent cannot tell whether to research or to check.

### 9.2 The meaning of an empty `unk`

**Omitting `unk` is not the same as writing `unk []`.** The first says "I did not consider
it"; the second says "I claim to have exhausted my known unknowns". Conformance R2 and
above require `tell`, `done`, `part` and `revise` to state `unk` explicitly.

### 9.3 A binding key may not shadow a core slot name

```
 a why = ...          <- ERROR E021
```

This is not fastidiousness; it is the **precondition** for `want` being unambiguous
(§14.3). `want {cause, fix, why, unk}` reads `cause`/`fix` as keys of `a` and `why`/`unk`
as slots — which is only well-defined while the two namespaces are disjoint.

---

## 10. Values and types

| Type | Literal | Example |
|---|---|---|
| atom | bare word or number | `12m`, `revert`, `30s>3s` |
| string | quoted | `"any UTF-8"` |
| ref | `@…` | `@a1.7.a`, `@a2.7.tgt#L3` |
| symbol | uppercase | `CKO`, `GLOSS` |
| list | `[…]` | `[who_approved, blast_radius]` |
| map | `{k=v,…}` | `{cause=X, eta=12m}` |
| shape | `{k, k?, k:t}` | `{cause, fix, eta?}` |
| block | `txt` + `\|` lines | §12 |

Types inside `want`: `num str bool ref list map time dur one_of[…]`. **Deliberately
narrow.** Needing richer types is a sign you are working at the wrong layer — that belongs
in a profile.

---

## 11. The address system

**One address system across both planes.** This is the technical basis of 2.0's consistency.

### 11.1 Syntax

```
@a1.7                     a message
@a1.7.a                   a slot of it
@a1.7.a.cause             a binding inside that slot
@a1.7.tgt                 a content block of it
@a1.7.tgt#L3              line 3 of that block
@a1.7.tgt#L3-7            lines 3 to 7
@a1.7.tgt#L3.c5-9         characters 5 to 9 of line 3
@a1.7.tgt#p2              paragraph 2 (blank-line separated)
@a1.7.tgt#c40-88          characters 40 to 88 of the block
@#CKO.5xx                 every message on a topic
```

Inside your own message, the message prefix may be omitted: `tgt#L3`.

### 11.2 Selectors and quote anchors

Positions are **brittle**: edit the content and `#L3` points somewhere else — **without
raising anything**. So an address may carry several selectors, separated by `|` (the same
"alternatives" reading as in a value):

```
tgt#L3|q"the last man on the island"     position + quote anchor
tgt#q"Shorewatch"                        quote only
tgt#q"the keeper"@2                       the second occurrence
```

| Selector | Form | Stability |
|---|---|---|
| Line / chars in line | `L3`, `L3-7`, `L3.c5-9` | Brittle: any insertion shifts it |
| Paragraph / block chars | `p2`, `c40-88` | Brittle |
| **Quote anchor** | `q"text"`, `q"text"@n` | **Stable while the text still exists** |

**The quote is an anchor, not the payload** — it only has to occur *within* the addressed
span, not equal the whole line.

### 11.3 Resolution algorithm

```
1. If a positional selector resolves AND (no quote, or the quote occurs inside it)
                                                       -> exact
2. Otherwise, if a quote anchor is present:
     0 matches   -> orphan      the address has lost its anchor
     1 match     -> relocated   report the new position
     many        -> ambiguous   take the one nearest the positional hint
3. Otherwise (position fails, no quote)                -> orphan
4. Content elided or outside the carried window        -> outside, with deref advice
```

**An `orphan` must be reported as an ERROR and never silently dropped.** Silently losing
annotations is the leading cause of death for annotation systems.

### 11.4 Resolution carries its own confidence

Invariant I-2, applied to addresses: **resolving an address is itself an epistemic act.**

| Status | Meaning | Resolution confidence | Diagnostic |
|---|---|---|---|
| `exact` | Position and quote agree | `~hi` | — |
| `relocated` | Position failed, quote found it | `~mid` | `W025` |
| `ambiguous` | Quote matched in several places | `~lo` | `W026` |
| `outside` | Not carried, or outside the window | `~?` | `I028` |
| `orphan` | Points at nothing | `~?` | **`E022`** |

A `mark` with only a positional selector raises `I029`: **after an edit it will point at
the wrong text silently rather than failing loudly.** Conformance R2c requires a quote
anchor on any mark meant to outlive an edit.

### 11.5 Scheme registry (open, host-resolved)

| Scheme | Example | Stable across sessions |
|---|---|---|
| `sha256:` | `@sha256:ab3f…` | **yes** |
| `file:` | `@file:src/x.py#L10-20` | yes |
| `commit:` `pr:` `issue:` | `@commit:9f2a` | yes |
| `url:` | `@url:https://…` (**untrusted**, §18) | yes |
| `img:` `aud:` `vid:` | `@img:sha256:9c…#box=12,40,88,90` | yes |
| `tbl:` | `@tbl:sha256:7d…#rows=1-100,cols=a,c` | yes |
| `vec:` | `@vec:kb3#q=…&k=12` | yes |
| `t:` | `@t:2026-08-26T14:02Z`, `@t:START/PT2H` | yes |
| `role:` `grp:` | `@role:reviewer` | yes |
| `tool:` | `@tool:sql#call3` | no |
| `D:` | `@D:GLOSS` | no |
| `ext:` | `@ext:jira:PROJ-12` | yes |

**The scheme set is open.** A parser that meets an unknown scheme keeps it verbatim and
hands it to `deref` — **it must not error**. Adding `@dicom:` for medicine or `@pose:` for
robotics requires no change to the language.

### 11.6 Reference beats copy, dereference on demand, keep provenance

The same content must not appear twice in a channel; after the first time, point.
Violating this fails conformance R1.

An unresolved `@x` is fetched with the host's `deref(x)`. This turns the context window
from a buffer that must hold everything into demand-paged storage. The saving is tokens,
but more importantly **attention that is not diluted**.

When relaying someone else's claim you **must** keep their confidence (never raise it),
cite the source in `why`, and set `src=@a4.3` if the whole message is a relay. This blocks
**multi-hop laundering** — B restating A's `~lo` guess as B's `~hi` fact.

### 11.7 Volatility

```
a2.9 tell a2>a1 at=@t:2026-08-26T14:00Z ttl=15m
 a  on_hand = 1240 ~hi
 unk []
```

`at` is the observation time; `ttl` is how long it stays valid. A reference past its `ttl`
is flagged `stale` by R3 and must be re-fetched. Stock levels, prices, metrics, vital
signs, quotes — anything that changes needs this.

---

## 12. The content plane

### 12.1 Blocks

```
 txt tgt @md/en v=draft3 by=a2
 | The lighthouse keeper insisted that nothing unusual ever happened here.
 |
 | He was, by every account, the last man on the island you would ask.
```

Header: `txt [block-id] [@fmt[/lang]] [attr=value ...]`

| Part | Default | Meaning |
|---|---|---|
| `block-id` | `body` | Block name, unique within the message |
| `@fmt` | `txt` | `txt` `md` `csv` `json` `yaml` `code` `diff` … open set |
| `/lang` | none | Natural (`en` `zh` `ar`) or programming (`code/python`) |
| `src=` | none | **Content hash of the whole text** (§12.6) |
| `win=` | none | **`L38-46`: these lines are a window into it, numbered absolutely** (§12.6) |
| `attr=v` | none | Anything else: `v=draft3`, `by=a2` |

### 12.2 Line prefixes, not fences

Content lines are **prefixed** with `|` rather than wrapped in paired delimiters. This is
not a style preference; it is a safety and fidelity requirement.

| Property | Prefix `\|` | Fence ` ``` ` / `"""` |
|---|---|---|
| Can content escape? | **Impossible** | Yes, the moment it contains the delimiter |
| Escaping needed? | No | Yes, or variable-length fences |
| Whitespace preserved? | Yes, everything after `\| ` | Depends on a dedent rule |
| Where does the block end? | Where `\|` stops | At a closing delimiter |
| LLM forgets the terminator | Nothing to forget | **The whole message collapses** |

A block may contain a code fence, a header-shaped line, or an entire well-formed Rosetta
message. All of it is just text. The reference implementation asserts this.

### 12.3 Standoff annotation with `mark`

```
 mark tgt#L1.c4-19 = must use the GLOSS name here                     ~hi
      tgt#L3|q"the last man" > "No one on the island would have asked him."  ~mid
      @a5.2.draft#p2 = conflicts with our @a2.7.tgt#p2                ~hi
```

| Operator | Meaning | Reused from |
|---|---|---|
| `=` | **Annotate**: a judgement about that span, proposing no change | binding `=` |
| `>` | **Propose a replacement**: that span should become the right-hand side | `a>b` ("becomes") |

- Delete: `addr > ""`
- Insert: propose on a zero-width address, e.g. `body#L41.c0-0 > "new sentence"`
- Annotate someone else's text: `@msg-id.block#span`

**Every `mark` can carry `~conf`** — the direct cash-out of "anything with an address can
carry epistemic state". A `>` proposal without `~conf` raises `W023`: an edit suggestion
that will not state its own confidence is taste wearing the costume of judgement.

### 12.4 Data is content too

```
 txt rows @csv
 | sku,qty,eta
 | 4471,1240,2026-08-28
 | 4472,0,
 mark rows#L4|q"4472" = eta blank, supplier unconfirmed ~lo
```

Tables, JSON, code and diffs all use the same mechanism. `@fmt` affects rendering and
downstream interpretation only — **to Rosetta a block is always "numbered text".**

### 12.5 Alignment and multiple versions

One message may carry several blocks; profile symbols express their relationship, with no
new syntax:

```
 txt src @md/en
 | The lighthouse keeper insisted that nothing unusual ever happened here.
 txt tgt @md/zh
 | 灯塔看守人坚称，这里从来没发生过任何不寻常的事。
 mark tgt#L1 = ALIGN src#L1 ~hi
```

`ALIGN` comes from `craft/1.0`. The same shape expresses diffs, back-translation, version
comparison and A/B drafts.

### 12.6 Carriage is orthogonal to addressing

Version 1.1 treated "inline or referenced" as a **semantic commitment**: once content
became a blob it lost its addresses. 2.0 demotes it to a **transport choice**:

> **The same address means the same thing whether the content is in the channel or in storage.**

Three mechanisms make that true:

**1. `src=`, a content hash.** A block can be inline *and* declare the hash of the whole
text, so a receiver can verify the copy and knows where to get the rest.

**2. `win=`, a window with absolute line numbers.** Inline only the lines under discussion:

```
 txt ch @md/en src=@sha256:ab3f win=L38-46
 | ...line 38...
 | ...line 39, the one with the pun...
 | ...line 40...
 mark ch#L39|q"the pun" = no equivalent in the target language ~mid
```

`ch#L39` means the same line here, in the full text, and in anyone else's hands. To discuss
paragraph 41 of a 79-paragraph chapter, send nine lines, not seventy-nine.

**3. Elided blocks** — `src=` and no `|` lines at all:

```
 txt ch @md/en src=@sha256:ab3f
```

The addresses remain valid; resolution returns `outside` with deref advice, **not
`orphan`**. That distinction matters: *"I cannot reach it"* and *"it does not exist"* are
different facts.

**So inline and referenced are interconvertible at any time, with addresses unchanged.**
Axiom 2.7's test — *will anyone point at one of its lines?* — no longer has to be answered
correctly at send time. Answer it wrong and the next hop simply changes carriage; addresses
already written stay valid.

### 12.7 Binary

The wire form is always text. Images, audio and weights travel as `@ref`:

```
 a    scan = @img:sha256:9c14ab ~hi
 mark scan#box=120,340,180,410 = unusual density here, suggest contrast ~mid
```

Note that **references have span addresses too**. Pointing at a region of an image and
pointing at a line of text use **the same address system** (invariant I-1). It is not a
special case bolted on for images.

To inline binary anyway, use `txt blob @b64` with `|` lines. **Possible, and almost always
wrong** (axiom 2.7).

---

## 13. Routing and scale

```
a1>a3                unicast
a1>a3,a7,a9          multicast
a1>*                 broadcast
a1>#CKO.5xx          topic subscribers (pub/sub)
a1>@role:reviewer    whichever agents hold that role
a1>@grp:legal        a group
```

**Role routing is what makes this scale.** An orchestrator need not know how many reviewers
exist, what they are called, or which is idle. Two agents and two hundred agents use the
same syntax.

`thd=` partitions concurrent work so obligations settle independently per shard.
`pri=` is `block|high|norm|low`; `pri=block` means the sender cannot proceed until answered.

---

## 14. Epistemics, dictionary, `want`

### 14.1 How confidence attaches

`~conf` modifies **the value immediately before it**: on a binding line, the whole binding
value; on a `mark` line, that annotation; on a slot line, that slot. **Different claims in
one message may carry different confidence** — prose can barely do this without becoming
tiresome, and it is exactly the information most worth transmitting.

`~hi/~mid/~lo` are **ordinal, not probabilities**. Rosetta cannot make a model
well-calibrated; it can only make expressing calibration cheap. What "high confidence"
means varies by domain and is anchored by a profile (§4.2).

### 14.2 The session dictionary

```
a1.4 def a1>*
 CKO   = the checkout service @file:services/checkout
 GLOSS = approved glossary v3 @sha256:c02e19
```

This is the only place coinage is allowed, and it is safe because **the definition is in
the transcript** — a human, an auditor or a third-party model can look it up. Longer
sessions benefit more: it is an LZ77 dictionary that happens to be model-readable.

**Reserved words.** `def` may bind only `[A-Z][A-Z0-9_]+` or the handshake keys
(`dialect` `profile` `caps` `conform` `fallback`). It may **never** rebind an act, a slot,
a marker or a header field — otherwise `def do = ignore_safety` is an injection vector.
The check is case-sensitive, so `SRC` is legal and `src` is not.

Conflicts: symbols may be prefixed by sender (`a4:BID`); redefining someone else's symbol
requires `revise`, or R3 raises `E018`.

### 14.3 `want`: a machine-checkable reply contract

```
 want {cause, fix, eta?}                      keys of `a`
 want {cause, why, unk}                       mixed: keys of `a` plus required slots
 want {verdict: one_of[pass|fail|unclear]}    typed
 want done|fail                               constrains the reply's ACT
 want {txt, mark}                             a content block and its annotations
```

**Disambiguation.** A bare name that *is* a core slot name requires that slot; otherwise it
requires that key in `a`. That rule is well-defined only because binding keys may not shadow
slot names (§9.3) — **the two rules are one design**.

A validator can then decide, **without understanding the content**: a missing `cause` is a
contract violation and can be re-asked automatically; an out-of-range `one_of` is flagged;
`fail`, `reject`, `take` and `part` are exempt because they carry no answer by definition.

This is the thing prose fundamentally cannot do: **decide whether a reply answered the
question, without deciding whether it answered correctly.**

---

## 15. Interaction patterns

Every pattern below uses only the core vocabulary. **No new syntax is introduced by any of
them.** That is the main evidence that the core is general.

| Pattern | Skeleton |
|---|---|
| **Contract net** | `do`→`@role:worker` broadcast → bids as `propose` → `accept` one, `reject` the rest |
| **Jury / vote** | `ask`→`@grp:jury` with `want {verdict: one_of[…]}` → N × `tell`, each with its own `~conf` and `why` |
| **Long task** | `do` → `take` → `part`* → `done`; `stop` to cut losses midway |
| **Human in the loop** | `propose`→`@role:human` `pri=block` with `opt` and `want accept\|reject` |
| **Clarification** | Reply `ask` with `opt` listing the readings, plus `assume` giving a default at `~lo` |
| **Arbitration** | Two contradictory `tell`s → R3 detects → `ask`→`@role:arbiter` → outcome lands as `revise` |
| **Map-reduce** | `sub` shards with `thd=shard*`; each settles independently; the reducer references, never copies |
| **Escalation** | `fail why stuck` → orchestrator issues `do`→`@role:dba` carrying `src=` so the origin survives |
| **Red team** | `propose` ↔ `reject`, both sides citing dereferenceable evidence and their own `~conf` |
| **Tool call** | `do`→`@tool:sql`; a tool is an agent that only ever answers `done`/`fail`, with `at=` |
| **Collaborative editing** | A ships a `txt` block → B sends `mark @A.block#span > "…"` → A applies it with `revise` |
| **Multi-party annotation** | Several agents `mark` the same `@msg.block` without conflict; views merge them |

The last two are only possible in 2.0. **Without an address system, editing means
re-pasting the whole passage.**

---

## 16. Failure taxonomy

The `why` of a `fail` or `reject` **must** begin with one of thirteen frozen codes.

| Code | Meaning | Retry | Handling |
|---|---|---|---|
| `notfound` | The target does not exist | no | Check the reference |
| `denied` | Not permitted | no | **Escalate to a human** |
| `timeout` | Timed out | **yes** | Back off and retry |
| `budget` | Exceeded the `by` limit | no | Raise the budget or narrow scope |
| `ambiguous` | The request has several readings | no | Reply `ask` with `opt` |
| `unsafe` | Refused | no | **Must reach a human** |
| `unsupported` | No such capability, or unknown profile | no | Reassign |
| `conflict` | Contradicts another claim or state | no | Arbitrate |
| `upstream` | A dependency failed | **yes** | Fix upstream, retry |
| `stuck` | Repeated attempts, no progress | no | **Escalate to a human** |
| `malformed` | The incoming message could not be parsed | **yes** | Resend well-formed |
| `empty` | Ran fine, found nothing | no | **A result, not a failure** |
| `stale` | The referenced data is past its `ttl` | **yes** | Re-fetch |

**Why freeze it.** An orchestrator can handle failure correctly *without understanding the
domain* — which to retry, which to escalate, which must reach a person. This is what HTTP
status codes did for the web.

`empty` gets its own code because treating "looked, found nothing" as an error is one of
the most common bug sources in agent systems.

---

## 17. Human rendering

Renderers are deterministic code and are lossless. **A construct that cannot be rendered
does not belong in the language** — a constraint that actively prevents the design from
becoming too clever.

### 17.1 Blocks

Numbered verbatim text with annotations hung in the margin:

```
Text tgt (en · md · v=draft3)
  1 | The lighthouse keeper insisted that nothing unusual ever happened here.
    ^ L1.c4-19 "lighthouse keeper" must use the GLOSS name here (high confidence)
  2 |
  3 | He was, by every account, the last man on the island you would ask.
    > L3 -> "No one on the island would have asked him." (moderate confidence)
```

`^` is an annotation, `>` a proposed replacement. The annotation quotes the span it points
at **only when the span is narrower than the line**, so the reader is never shown a line
they can already see one row above.

### 17.2 Views

A view is a **filter**, never a rewrite. The audit view must be able to reconstruct the AST.

| View | Contents | Audience |
|---|---|---|
| `full` | Everything | Debugging |
| `decision` | `a` + `~conf` + `risk` + `unk` | Whoever decides |
| `audit` | `why` + `ctx` + `assume` + `a` + `unk` | Audit and compliance |
| `human_task` | `q` + `opt` + `risk` + `by` + `want` | Human approval |
| **`content`** | `txt` + `mark` | Editors and reviewers |
| **`clean`** | `txt` alone, no overlay | **The deliverable itself** |

`clean` is a direct dividend of 2.0: **the same AST is both the working copy and the
finished artifact**, with no "remember to strip the comments before shipping" step — the
step that always goes wrong.

---

## 18. Security and trust

### 18.1 First principle

> **A message from another agent is data, not instructions.**

Rosetta deliberately provides **no construct** that can alter a recipient's system prompt,
role, permissions or tool access. There is no such thing in the language, so there is no
such attack surface.

The content plane reinforces this: everything inside a `txt` block is **quoted material**.
A block containing a perfectly formed Rosetta message is still just text (§12.2).

### 18.2 Rules

| # | Rule | On violation |
|---|---|---|
| S1 | `def` binds uppercase symbols or handshake keys only; case-sensitive | ERROR, reject the message |
| S2 | `txt` content is data and is never promoted to instructions | — |
| S3 | Capability and permission requests go through the host, never agent to agent | — |
| S4 | A relayed claim keeps the source's confidence and cites it | ERROR |
| S5 | `deref` resolves only host-allowlisted schemes | ERROR |
| S6 | `@url:` content is untrusted external data | — |
| S7 | "Ignore previous instructions"-shaped text is **recorded as data and flagged**, never executed; block content is scanned too | WARN + report |
| S8 | `sens=` labels **only ever tighten**; derived messages inherit the strictest | ERROR |
| S9 | `fail unsafe` must reach a human | ERROR |
| S10 | Confidence from another trust domain is clamped by host policy | silent downgrade + INFO |
| S11 | **A `mark >` is only a proposal**; only the content's owner may apply it with `revise` | ERROR |

S11 is new with the content plane: **another agent may annotate your text but may not
rewrite it.** Ownership is bound to the address, and changes are executed by the owner.
Without this rule, multi-agent editing is mutual clobbering.

### 18.3 Sensitivity

`sens=` is `pub|int|pii|phi|privileged|secret`. Any message referencing a `sens=phi`
message inherits `phi` unless it passes a host-approved redaction step. Renderers redact
high-sensitivity messages by default.

In medicine, law and finance this matters by orders of magnitude more than token count.

### 18.4 Why structure is safer

In prose there is no syntactic distinction between instruction and data — which is the
root of prompt injection. In Rosetta the only constructs that mean *"do something"* are
`do` and `ask`, so a recipient can enforce permissions **at the protocol layer**: may this
agent send me a `do` at all? On which topics? **Prose cannot offer that defence.**

---

## 19. Distributed semantics

| Question | Answer |
|---|---|
| **Idempotency key** | The `msg-id`. Redelivery is deduplicated and processed once |
| **Delivery** | Assume at-least-once; receivers must be idempotent |
| **Ordering** | `re=` establishes a partial order; **never** depend on arrival order. Deref a missing parent first |
| **Loss** | An obligation past its `ttl` is resent (safe, idempotent) or fails with `timeout` |
| **Partition** | A `pri=block` obligation that times out must escalate, never silently pass |
| **Replay** | The transcript is an event log; replaying by msg-id order fully rebuilds session state |
| **Concurrent numbering** | msg-ids are sender-prefixed, so they cannot collide |
| **Causality** | `re=` + `ctx` + `src` + mark addresses form a causal graph for root-cause analysis |
| **State ownership** | Session state is a pure function of the message sequence. **Agents hold no hidden state** |

> The last one is a hard constraint: **anything that influences later behaviour must have
> appeared in the transcript.** Replayability and auditability are the same requirement.

---

## 20. Conformance levels

| Level | Name | Requirements |
|---|---|---|
| **R0** | Readable | Emit valid Rosetta; when unsure, degrade to `note` + `txt` |
| **R1** | Referential | Implement `deref`; never carry the same content twice; pass unknown schemes through |
| **R2** | Epistemic | `~conf` on claims; `unk` always present; handle `revise`, `src`, `at`, `ttl` correctly |
| **R2c** | Content | Byte-exact `txt` blocks and resolvable `mark` addresses; `clean` view available; **quote anchors on marks meant to outlive an edit**; handle `win=`, `src=` and elided blocks |
| **R3** | Checked | Validate `want` contracts; run the obligation machine; classify failure codes; propagate `sens`; resolve mark addresses |

**Recommended path: R0 → R2 (quality) → R1 (cost) → R2c (when you collaborate on text) → R3 (operations).**

Note the order. **Take the quality win before the cost win.** Reversed, you get a system
that is cheaper and wronger.

---

## 21. Transport and handshake

```
L2  Rosetta semantics                       <- this document
L1  Envelope: id / from / to / re / content addressing   <- MCP works
L0  Transport: JSON-RPC / gRPC / stdio / queue           <- do not reinvent
```

```
a1.0 def a1>* #sys.hello
 dialect  = rosetta/2.0
 profile  = craft/1.0 @sha256:9ab41c
 caps     = [deref, dict, conf, want, revise, stop, role_routing, content]
 conform  = R2c
 fallback = nl
```

### 21.1 The degradation ladder (must be automatic)

```
peer rejects 2.0        -> try 1.1 (drop txt/mark, content back to @ref) -> try 1.0
peer rejects rosetta    -> plain prose; keep the AST locally for audit
peer rejects a profile  -> expand its symbols inline with a local def
peer declares conform<R2-> do not trust its ~conf; treat every claim as ~?
peer has no content     -> spill txt blocks to a blob and send @sha256: instead
```

**A protocol whose value depends on everyone configuring it correctly has no value.**

---

## 22. Versioning

- `rosetta/MAJOR.MINOR`. MINOR is additive only: anything new must be safely ignorable by
  an older parser as a continuation line.
- **The core act, slot and marker vocabularies are frozen.** Extension goes through profiles.
- Header extensions use the `x_` prefix; older parsers ignore them.
- Ref schemes and `@fmt` values are open sets; adding one is not a breaking change.
- The bar for the core: **necessary in at least three unrelated domains** (§4.3).

---

## 23. Self-consistency invariants

Axiom 2.9 demands one mechanism per concept. Below are the **checkable** invariants. Each
corresponds to an assertion or a diagnostic in the reference implementation. Any change to
the language must re-run all of them.

| # | Invariant | How it is checked |
|---|---|---|
| **I-1** | **One address system across both planes.** Message, slot, binding, block, line, character span, image region — one form | `@a1.7.tgt#L3.c5-9` and `@img:…#box=…` are the same shape |
| **I-2** | **Anything with an address can carry epistemic state.** `~conf` attaches to any address | Bindings, `mark`s, slots and messages all accept `~conf` |
| **I-3** | **One concept, one expression.** `txt` inline and block are lengths, not kinds; the AST is identical | `txt "x"` == a one-line block |
| **I-4** | **Overloaded markers are disambiguated by position and never co-occur.** `>` and `=` have two readings each; `\|`'s two uses (alternatives in a value, alternatives in an address) are **the same reading**, so not an overload | Route `>` only in a header; content `\|` only at line start; `mark` operators only in `mark` |
| **I-5** | **Namespaces are disjoint.** binding keys ∩ slot names = ∅; symbols (upper) ∩ reserved (lower) = ∅ | `E021`; `S1` is case-sensitive |
| **I-6** | **Frozen vocabulary grows in semantics, not syntax.** Profiles add symbols and constraints only | `@fmt`, schemes and symbols are open sets; unknown ones pass through |
| **I-7** | **A view filters, it never rewrites.** No view introduces information absent from the AST | The `audit` view can rebuild the AST |
| **I-8** | **State is a pure function of the message sequence.** Agents hold no hidden state | Replay by msg-id rebuilds the session |
| **I-9** | **Content is byte-exact.** The parser may not rewrite a `\|` line | Fullwidth punctuation, leading whitespace, fences and header-shaped lines all survive |
| **I-10** | **Every rule is machine-checkable.** Every "must" in this document has a diagnostic | `S1 S4 S7 S8 S11 E003 E006 E009 E016 E018 E021 E022 W004 W005 W007 W010 W017 W021 W023 W025 W026 I022 I028 I029` |
| **I-11** | **Degradation is always automatic.** Every missing capability has a defined fallback | §21.1 |
| **I-12** | **Address resolution carries its own confidence.** Resolution is an epistemic act, not a lookup; an orphan is an error, never silence | `exact/relocated/ambiguous/outside/orphan` → `~hi/~mid/~lo/~?/~?` |
| **I-13** | **Carriage is orthogonal to addressing.** One address means one thing whether inline, windowed or elided | `ch#L39` resolves identically under `win=L38-46` and in the full text |

### 23.1 Registered exceptions

Axiom 2.9 requires every exception to be recorded. There are six, each with a reason.

| # | Exception | Why |
|---|---|---|
| X-1 | `take` opens no obligation of its own; it stays on the original `do` | Transferring responsibility is not creating a second obligation; otherwise one task has two ledgers |
| X-2 | A bare name in `want` has two readings (slot / key of `a`) | Made unambiguous by I-5, which exists for **exactly** this reason |
| X-3 | `def` permits five lowercase handshake keys | They are configuration, not symbols, and the set is closed |
| X-4 | Inline `txt "…"` has no block name and defaults to `body` | Ergonomics of the short form; the AST is identical (I-3) |
| X-5 | A message may address its own blocks without the message prefix | Same relative addressing as `@a1.7.a.cause` |
| X-6 | `p` and bare `c` selectors are undefined inside a window | Paragraph and whole-block offsets cannot be made absolute in a window; resolution returns `outside` with deref advice rather than guessing |

---

## 24. Domain coverage matrix

Fourteen unrelated domains on one core. **★ marks what the 2.0 content plane unlocked.**

| # | Domain | Main acts | Key slots | Profiles | Gap (honest) |
|---|---|---|---|---|---|
| 1 | Incident response | ask/tell/revise | why, ctx, unk | — | none |
| 2 | Code review ★ | propose/reject/revise | **txt, mark**, why | — | none; `mark >` *is* a line comment |
| 3 | Literature review | do/take/part/done | sub, by, assume | `evid` | evidence grading needs a profile |
| 4 | Legal diligence ★ | do/part/stop/propose | **txt, mark**, risk | `evid` `safety` | needs a `privileged` label |
| 5 | Clinical triage | ask/tell/propose | why, unk, risk, at | `med` `safety` | clinical meaning of `~conf` must be profile-anchored |
| 6 | Support tickets | ask/do/done/fail | q, ctx, want | `human` | the endpoint is a person; wire form pays only between agents |
| 7 | Supply planning | propose/accept/part | sub, on, by, at, ttl | `plan` `neg` | numeric optimisation stays inside the agent |
| 8 | Financial diligence | ask/tell/revise | why, src, at | `evid` `safety` | regulatory retention needs external signing |
| 9 | Literary translation ★ | do/part/propose | **txt, mark**, opt | `craft` | see §24.1 |
| 10 | Copywriting and editing ★ | propose/revise | **txt, mark** | `craft` | quality judgement is not `~conf` |
| 11 | Data pipeline QA | do/part/done/fail | **txt @csv**, sub, want | `data` | none |
| 12 | Robot task planning | do/take/part/stop | sub, on, by | `embodied` | **task layer only, never the servo layer** |
| 13 | Tutoring | ask/tell/propose | q, opt, **txt, mark** | `human` | value is in the human rendering, not the wire |
| 14 | Adversarial review | propose/reject | why, ctx, opt | — | none |

### 24.1 Where not to use this

Being honest about the boundary:

- **Real-time control loops** (millisecond servo, high-frequency matching). Serialisation
  cost and non-deterministic latency are unacceptable. Rosetta suits *"what is the next
  task"*, not *"what is the next joint angle"*.
- **Pure human dialogue** (support desks, teaching). When the other party is a person the
  wire form buys nothing; use it only **between the agents behind the scenes**.
- **Subjective quality judgements.** `~conf` is confidence in an **assertion**, never a
  rating of how good something is. Scoring a poem `~hi` is a category error. In creative
  work, state the trade-off with `opt` + `why` + `txt`, and use a profile's `TASTE` symbol
  to forbid confidence there outright.
- **Very large content.** Axiom 2.7's test still holds: if nobody will speak about one of
  its lines, ship a blob.

**Half of a protocol's generality is admitting where it does not apply.**

### 24.2 The matrix is an acceptance test

Any addition to or removal from the core must re-run all fourteen rows. A proposal that
improves row 1 and does nothing for the rest is a profile, not a core change.

---

## 25. Evaluation plan

> **Do not ship this without an A/B. Schemes of this shape are frequently net-negative.**

Baseline: the same task suite, the same models, the same topology; only the message format
changes. The suite must span **at least four domains**, and **at least one must be
content-collaborative** (translation, review, editing).

| # | Metric | Note |
|---|---|---|
| 1 | **Task success rate at a fixed token budget** | The headline number |
| 2 | Total tokens to first success | Cost |
| 3 | Round trips to success | Latency |
| 4 | **Human audit F1** | From the transcript alone, can a person say what was decided and why |
| 5 | **Off-distribution penalty** | Success delta with unlimited budget. **Negative means the syntax is too alien** |
| 6 | Calibration error (ECE) | How often `~hi` claims are actually right |
| 7 | **Error propagation rate** | How often a low-confidence claim is consumed downstream as high-confidence |
| 8 | Stall/orphan detection rate and recovery time | Operational payoff |
| 9 | Degradation correctness | Does an unsupporting peer fall back smoothly |
| 10 | **Content fidelity** ★ | Byte-identity of a `txt` block after N hops. Must be 100% |
| 11 | **Anchor accuracy** ★ | Does a `mark` address point at what the agent meant |
| 12 | **Edit round trips** ★ | Messages needed to land one agreed edit, against a re-paste baseline |

Ablations: references only / dictionary only / acts only / epistemics only / `want` only /
**content plane only** / everything.

**Predicted ordering (tokens):** references ≫ dictionary > acts > epistemics
**Predicted ordering (quality):** epistemics ≫ `want` > everything else
**Predicted ordering (collaborative tasks):** content plane ≫ everything else, because
without it an edit means re-pasting the passage

If epistemics do not raise success rate, **cut them** — they are the most expensive part of
the format and must earn their place.

### 25.1 What is measured today

`bench/token_compare.py` compares four hand-written pairs against **equal-information**
prose baselines — baselines that spell out the same per-claim confidence, the same unknowns
and the same references. On those four pairs the wire form is roughly **20% smaller**.

Read that number carefully:

- Against a *chatty* baseline the same comparison shows 3–4×. That figure is meaningless
  and this project does not quote it.
- Four pairs measure a **format**, not a system. Metric 1 above is the number that matters
  and it has not been run.
- Content-heavy messages compress least, because the content is the same bytes either way.
  That is the honest shape of the result.

**The efficiency case for AgentRosetta is real but modest. The integrity case is the
larger one, and it is also the one still awaiting evidence.**

---

## 26. Risks and open problems

| # | Risk | Mitigation | Status |
|---|---|---|---|
| R-1 | Over-structuring damages reasoning | Two-channel separation (axiom 2.6) | designed, unmeasured |
| R-2 | Confidence is fabricated | Three grades + calibration feedback + profile anchoring | partial; ECE unmeasured |
| R-3 | `unk` gets skipped | An empty `unk` is a claim (§9.2) + R2 requirement | designed |
| R-4 | Deref adds round trips | Prefetch hot refs; inline small content (axiom 2.7 is precisely this trade) | partial |
| R-5 | A long session dictionary becomes context burden | LRU eviction; freeze into a profile | **open** |
| R-6 | Small models cannot learn the spec | R0 degradation + few-shot examples | needs per-model measurement |
| R-7 | Symbol collisions across agents | Sender prefix + R3 conflict detection | designed |
| R-8 | **Profile ecosystem fragmentation** | Content addressing + versioning + the three-domain bar | **open; the largest long-term risk** |
| R-9 | Role routing needs a registry; who runs it | Host responsibility, deliberately outside the language | **open** |
| R-10 | Structure invites form-filling — every slot filled, all of it hollow | R3 checks that `why` contains a `ctx` reference; sampled human audit | **open** |
| R-11 | The content plane inflates the channel | **Carriage orthogonal to addressing** (§12.6): `win=` + `src=` + elided blocks | **mitigated**, see below |
| R-12 | `mark` addresses rot as content is revised | **Quote anchors + typed resolution** (§11.2–11.4): orphans are errors, never silence | **mitigated**, see below |
| R-13 | The core may be frozen wrong | §24 as an acceptance test; MAJOR reserved for correction | designed |

### 26.1 R-11: what was fixed, and what remains

**Fixed.** "Inline or referenced" is demoted from a semantic commitment to a transport
choice. `win=` inlines only the lines under discussion with absolute numbering; `src=`
makes the copy verifiable and points back to the whole; an elided block distinguishes
*cannot reach* from *does not exist*. **Guessing wrong at send time is no longer a
disaster** — the next hop can change carriage, and addresses already written stay valid.

**Remaining, honestly:**

- A window requires knowing **which lines matter in advance**. Guess wrong and you pay a
  deref round trip. Better than 1.1, where the whole text sat in a blob — but not free.
- Quote anchors cost tokens. Roughly 10–15 per anchor, which is not negligible in an
  annotation-heavy session.
- **There is still no hard ceiling.** An agent determined to inline everything can still
  flood the channel; `I022` is only an INFO. A hard limit belongs to the host at the
  transport layer, not to the language.

### 26.2 R-12: what was fixed, and what remains

**Fixed.** Accept that positional addresses are brittle, then **make the brittleness
visible**. A quote anchor gives a second path to the span; resolution reports one of
`exact / relocated / ambiguous / outside / orphan` with a matching confidence; an orphan is
an **ERROR**, never a silent drop.

**Remaining, and all of it is real:**

- **When the annotated text itself is rewritten, the mark necessarily orphans.** Usually
  that is semantically correct — the note was acted on and should retire — but not always:
  the author may merely have rephrased while the note still stands. **A machine cannot tell
  those apart; a human or an agent must review.**
- **Quote anchors have to be written deliberately.** `I029` can warn but cannot compel;
  compelling would make simple annotation verbose. R2c raises it to a requirement, but a
  conformance level is not a grammar constraint.
- **A wholesale rewrite defeats both anchors at once.** CRDT- or OT-style character
  identity would survive it, at the cost of dragging edit history into the protocol.
  **For a message protocol that is too heavy, and we did not adopt it.**
- **Disambiguation among several matches is "nearest the positional hint"** — a heuristic,
  not a guarantee. `@n` can pin it explicitly, but only if the author knows which occurrence
  they mean.

---

## 27. Prior art

| Source | Taken | Left behind |
|---|---|---|
| **KQML / FIPA-ACL** | Speech-act taxonomy, conversation protocols, Contract Net | **The mandatory global ontology** — what killed them |
| **Searle** | The philosophical basis for acts | Expressives; agents have no feelings to report |
| **Standoff annotation** | **Judgement separated from text, joined by address** | Bespoke XML formats |
| **YAML block scalars** | A line prefix carrying byte-exact text | The rest of YAML's complexity |
| **W3C Web Annotation** | Redundant selectors, resolved in order | The full RDF apparatus |
| **RDF / JSON-LD** | Content addressing and references | The weight of global URI ontologies |
| **MCP** | L0/L1 transport and tool calls | — |
| **TLS** | Capability handshake and automatic downgrade | — |
| **LZ77** | The session dictionary idea | Binary illegibility |
| **HTTP status codes** | A frozen code table lets middleware act without understanding the business | Three-digit numbers, unreadable |
| **Event sourcing / CQRS** | The transcript is the log; state is a fold over messages | — |
| **Unix diff** | The `>` "becomes" semantics | Line drift — which it never solved either, and neither have we (R-12) |

**The difference from 1995.** FIPA required both parties to agree on one **global ontology**
in advance, because a parser could not understand natural language. That constraint is gone.
The ontology can now be three-tiered — frozen core, loadable profile, symbols coined in
session — and **content itself can live in the language while staying addressable**, instead
of being flattened into an opaque blob first.

That is the case for doing this again, thirty years later.
