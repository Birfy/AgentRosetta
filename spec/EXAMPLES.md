# AgentRosetta 2.0 — Worked Examples

This file is the evidence for the claim that one frozen core covers unrelated domains.

Eleven scenarios below come from eleven unrelated fields. **All of them use only the 14
acts and 14 slots. Not one introduces new syntax.** Domain difference shows up in exactly
two places: the symbols bound by `def`, and the schemes used by `@`.

> Read the *mechanism*, not the domain. Each example ends with what it is demonstrating.

`python3 agentrosetta.py --demo` renders five of these in wire, English and Chinese.

---

## 1 · Incident response

```
a3.12 ask a3>a1 #CKO.5xx
 q     root_cause?
 ctx   @a3.7 @file:log/2f9c#L440-512
 want  {cause, fix, eta?}
 unk   [when the config changed]

a1.13 tell a1>a3 re=a3.12
 a     cause = @commit:9f2a lowered http.timeout 30s>3s   ~hi
       fix   = revert @commit:9f2a                        ~hi
       eta   = 12m                                        ~lo
 why   @file:log/2f9c#L487 timeouts start 14:02 = deploy time +-40s
 unk   [who approved 9f2a, whether other services hit this]
 risk  reverting reintroduces the slow query in @issue:441  ~mid

a1.19 revise a1>a3 re=a1.13
 a     cause != @commit:9f2a                              ~hi
 why   conflict @file:log/2f9c#L900-940 the curve did not move after the rollback
 unk   [the actual cause]
```

**Demonstrates.** `fix ~hi` and `eta ~lo` coexist in one message — prose can barely express
that difference without becoming tiresome. `revise` makes "I was wrong" a first-class act:
from here on every `@a1.13` resolves to `@a1.19`, and any agent holding the old conclusion
is forced to recompute. **The error is cut off where it happened, not discovered three hops
later.** Note `!=`: a negative claim is grammar, not prose.

---

## 2 · Literature review — long task, budget, abort

```
a1.0 def a1>*
 profile = evid/1.0 @sha256:b204c1

a3.40 do a3>a2 #lit_review
 q     survey CAR-T for solid tumours @vec:pubmed#q=CAR-T+solid&k=200
 by    $40 | 2h
 sub   s1 = dedupe and screen                @role:screener
       s2 = full-text extraction             @role:extractor  on=s1
       s3 = grade evidence (PRIMARY/HEARSAY) @role:grader     on=s2
 want  {themes, gaps, n_screened}

a2.11 take a2>a3 re=a3.40

a2.12 part a2>a3 re=a3.40
 a     n_screened = 80                                     ~hi
       themes     = [toxicity mgmt, solid-tumour penetration, manufacturing cost] ~mid
 why   CITE @vec:pubmed#ids=1..80
 unk   [non-English literature coverage, grey literature]
 risk  at the current rate this overruns the $40 budget    ~mid

a3.41 stop a3>a2 re=a3.40
 why   budget the interim finding is already enough to decide on

a2.13 done a2>a3 re=a3.41
 a     n_screened = 92                    ~hi
       partial    = @sha256:e5b7c1        ~hi
 unk   [108 papers unscreened, whether that loses a theme]
```

**Demonstrates.** `part` lets a half-finished conclusion circulate safely: it carries
`~conf` and `unk`, and **it does not close the obligation**, so nobody mistakes it for
completion. `stop` lets the orchestrator cut losses before the budget burns, and the
stopped side **must** answer `done` or `fail` — silence is not legal. `by $40 | 2h`
expresses two different limits in one slot. The review itself is a blob.

---

## 3 · Legal diligence — privilege and division of labour

```
a1.5 def a1>*
 profile  = safety/1.0 @sha256:44a9de
 REDLINE  = a clause that must change or we do not recommend signing
 FALLBACK = a concession the counterparty is likely to accept

a1.6 do a1>@grp:counsel #msa.acme sens=privileged
 q     review @doc:msa-acme-v7 and produce a redline list
 sub   s1 = liability and indemnity   @role:commercial
       s2 = data processing, transfer @role:privacy
       s3 = termination and renewal   @role:commercial  on=s1
 by    3d
 want  {redlines: list, blockers: list, fallbacks?}

a4.9 tell a4>a1 re=a1.6 sens=privileged
 a     redlines  = [§7.2 uncapped liability, §11.4 resale to third parties] ~hi
       blockers  = [§11.4]                                                  ~hi
       fallbacks = [§7.2 capped at 12 months of fees]                       ~mid
 why   CITE @doc:msa-acme-v7#p14§7.2 @doc:msa-acme-v7#p22§11.4
       §11.4 conflicts with @ext:reg:GDPR-Art44                             ~hi
 unk   [whether counterparty has SCCs filed, whether we accept a 24-month cap]
 risk  insisting on deleting §11.4 may add two weeks to negotiation          ~mid
```

**Demonstrates.** `sens=privileged` **propagates along the reference chain**: any derived
message inherits the label unless it passes a host-approved redaction step, and a
`sens=int` forward that cites this message is rejected as `S8`. In legal and clinical work
that rule matters by orders of magnitude more than token count. Clause references are exact
(`#p14§7.2`), and the opinion never re-pastes the contract.

---

## 4 · Clinical triage — human in the loop, volatility

```
a2.40 part a2>a1 #triage.bed7 sens=phi at=@t:2026-08-26T14:02Z ttl=15m
 a      lactate_trend = rising  ~hi
        sepsis_score  = 3 of 6  ~mid
 why    @ext:ehr:obs-88231 three consecutive samples rising
 unk    [fluid intake last 6h, prior antibiotics]
 assume weight_kg = 70 standard adult estimate, not measured ~lo

a1.41 propose a1>@role:clinician pri=block sens=phi
 q      start the sepsis bundle?
 ctx    @a2.40
 opt    [start now, fluids then reassess, observe 1h]
 risk   each hour of delay raises mortality ~mid
 want   accept|reject
 unk    [allergy history]
```

The clinician does not see the above. They see the `human_task` view:

```
a1 -> role clinician · proposes  [BLOCKING · contains PHI]
------------------------------
Question        start the sepsis bundle?
Options         start now; fluids then reassess; observe 1h
Risk            each hour of delay raises mortality (moderate confidence)
Expected reply  must reply with accepts or rejects
```

**Demonstrates.** `at` and `ttl` give vital signs an observation time and a shelf life —
referencing `@a2.40` sixteen minutes later is flagged `stale` and must be re-fetched.
`assume weight_kg = 70 ~lo` puts an **implicit and potentially dangerous assumption** on the
record instead of burying it in fluent prose. `pri=block` tells the scheduler the whole
chain is waiting on a person.

---

## 5 · Supply planning — stale data

```
a2.9 tell a2>a1 #inv.sku4471 at=@t:2026-08-26T14:00Z ttl=15m
 a     on_hand = 1240                                  ~hi
       inbound = 800 eta @t:2026-08-28T09:00Z          ~mid
 why   @ext:wms:snapshot-9931
 unk   [whether the inbound shipment has cleared customs]

a1.5 propose a1>a3 #plan.w36 at=@t:2026-08-26T14:40Z
 ctx   @a2.9
 a     plan = ship 900 now, hold the rest for the inbound  ~mid
 unk   [whether the customer accepts a split shipment]
```

```
[WARN] W017: a2.9 expired at 2026-08-26T14:15:00Z — re-fetch before use
```

**Demonstrates.** a1 made a commitment from a forty-minute-old snapshot. This is among the
most common production incidents in supply chains, trading and monitoring — **and in prose
it is completely invisible**, because the text reads perfectly well. `at` + `ttl` turn it
into an automatic alert that does not depend on anyone remembering to check a timestamp.

---

## 6 · Financial diligence — provenance, no laundering

```
a4.3 tell a4>a1 #dd.target
 a     revenue_growth = about 40% ~lo
 why   HEARSAY from the management roadshow deck; no audited statements seen
 unk   [related-party transactions, definitional consistency]

a1.9 tell a1>@role:ic src=@a4.3
 a     revenue_growth = about 40% ~lo
 why   relaying @a4.3; the source is HEARSAY, no audit obtained ~hi
 unk   [related-party transactions, definitional consistency]
 risk  if this figure enters the valuation model it will amplify the error ~hi
```

Had a1 written `~hi`, the validator refuses outright:

```
[ERROR] S4: relayed claim `revenue_growth` upgraded to ~hi above source a4.3's
        confidence — laundering
```

**Demonstrates.** **Multi-hop confidence laundering** — B restating A's guess as B's fact —
is the most insidious and most consequential failure mode in multi-agent systems. Prose does
not merely fail to prevent it, it *rewards* it: firmer wording reads more professional.
`src=` plus a hard no-upgrade rule turns it into an ERROR. `evid/1.0` goes further and caps
any `HEARSAY` claim at `~lo`.

---

## 7 · Data pipeline QA — fan-out and failure codes

```
a1.70 do a1>@role:worker #audit.orders
 sub   s1 = audit @tbl:sha256:7d19#rows=1-10000      thd=shard1
       s2 = audit @tbl:sha256:7d19#rows=10001-20000  thd=shard2
       s3 = audit @tbl:sha256:7d19#rows=20001-30000  thd=shard3
 want  {findings: list, n_rows: num}
 by    10m

a5.1 done a5>a1 re=a1.70 thd=shard1
 a     findings = []    ~hi
       n_rows   = 10000 ~hi
 unk   []

a6.1 fail a6>a1 re=a1.70 thd=shard2
 why   timeout shard 2 read exceeded 10m
 unk   []

a7.1 fail a7>a1 re=a1.70 thd=shard3
 why   denied no read permission on @tbl:
 unk   []
```

The orchestrator handles all three correctly without knowing what an order is:

```
[INFO ] I018: a6.1 failed with `timeout` — retryable        -> back off and retry
[ERROR] E017: a7.1 failed with `denied` — must reach a human -> request access, no retry
```

**Demonstrates.** Thirteen frozen codes let **middleware act correctly while understanding
nothing about the business** — exactly what HTTP status codes did for the web. Note
`findings = []` in a5.1: it looked, it found nothing, and that is a **valid result**.
`empty` exists as a separate code precisely so "looked, found nothing" stops being handled
as an error, which is a very common bug source.

---

## 8 · Creative collaboration — where `~conf` stops applying

```
a8.1 propose a8>a1 #script.act2
 a     beat = have the supporting character expose the lie here   ~mid
 opt   [expose it, stay silent while the audience knows, defer to act three]
 why   the tension flattens after page 12 @doc:draft7#p12-19
 risk  exposing it costs act three its reversal                   ~mid
 unk   [whether the director will trade away that reversal]
 txt   "These three are not 'which is more likely correct'. They are three
        different plays. I lean toward the second, but that is taste, not
        judgement — do not read it as ~hi."
```

**Demonstrates.** **This is an honest failure case.** `~conf` is confidence in an
**assertion**, not a rating of how good a thing is. Scoring a creative choice `~hi` is a
category error. The correct move is to lay out `opt`, state the trade-off in `why` and
`risk`, and use `txt` to say plainly that this is taste. §24.1 of the specification places
subjective quality judgement outside the language's scope on purpose.

**Half of a general protocol's generality is admitting where it does not apply.**

---

## 9 · Adversarial review — dispute and arbitration

```
a8.2 propose a8>a1 #design.auth
 a     approach = OAuth device flow ~mid
 risk  older devices do not support it ~mid
 unk   [actual share of older devices]

a9.1 reject a9>a1 re=a8.2
 why   conflict @a8.2 understates the risk: 38% of traffic is older devices
       per @sha256:d1f3 ~hi
 opt   [magic link, device flow with an SMS fallback]
 unk   [SMS cost]

a1.60 ask a1>@role:arbiter #dispute
 q     @a8.2 and @a9.1 conflict — which holds?
 ctx   @a8.2 @a9.1 @sha256:d1f3
 want  {holds: one_of[a8.2|a9.1|neither], why}

a2.1 tell a2>a1 re=a1.60
 a     holds = a9.1 ~hi
 why   PRIMARY @sha256:d1f3 is measured traffic, which outranks @a8.2's estimate
 unk   []
```

**Demonstrates.** The red team's objection carries **dereferenceable evidence** and **its
own confidence**, so the arbiter can rule on evidential strength rather than on rhetorical
force. `want {holds: one_of[…]}` makes the ruling directly machine-consumable. The outcome
lands back on the original with `revise`, so **the contradiction is resolved on the record
rather than silently overwritten by whichever message came last.**

---

## 10 · Literary translation — the content plane, end to end

Ask the same question of 1.1 and 2.0 and you get different answers. That is the most honest
record of what changed.

**1.1 said no.** The axiom "coordination, not cargo" pushed the manuscript into a blob;
inlining prose raised `W007`.

**2.0 says yes** — and translation is *why the content plane exists*. Translator,
terminologist and stylist all need to argue about **the same sentence**. If that sentence is
only a `@sha256:`, nobody can open their mouth.

> The 1.1 axiom mistook a **cost** (content inflates the channel) for a **prohibition**
> (content does not belong in the language). The correct test is: **content that will be
> pointed at must be addressable; content that only moves goes by reference.**

### 10.1 Source and target in one frame, byte-exact

```
a2.7 tell a2>a1 #ch1 sens=int
 txt src @md/en v=orig
 | The lighthouse keeper insisted that nothing unusual ever happened here.
 |
 | He was, by every account, the last man on the island you would ask.
 txt tgt @md/zh v=draft3
 | 灯塔看守人坚称，这里从来没发生过任何不寻常的事。
 |
 | 而所有人都会告诉你，全岛最不该去问的就是他。
 mark tgt#L1.c0-5|q"灯塔看守人" = must use the GLOSS name here   ~hi
      tgt#L3|q"最不该去问的就是他" > "谁都不会去问他。"            ~mid
      src#p2 = the clause order has to be rebuilt in the target  ~hi
      tgt#L1 = ALIGN src#L1                                      ~hi
 a    faithful != literal                                        ~hi
 unk  [whether the rewritten L3 now reads too colloquial]
```

`tgt#L1.c0-5` points at exactly those five characters. Note `a faithful != literal ~hi`: in
1.1 that could only be prose, and no machine could read the negation.

### 10.2 Others may annotate your text; they may not rewrite it

```
a3.9 propose a3>a2 re=a2.7 #ch1.term
 mark @a2.7.tgt#L1|q"灯塔看守人" = GLOSS v4 fixes this term            ~hi
      @a2.7.tgt#L3|q"最不该去问的就是他" > "谁都不会去问他。"           ~mid
 why  L3 puts the emphasis on "least likely"; the source emphasises "him"
 unk  [publisher's preference on end-weight]

a2.9 revise a2>a1 re=a2.7 #ch1
 txt tgt @md/zh v=draft4
 | 守岸人坚称，这里从来没发生过任何不寻常的事。
 |
 | 而所有人都会告诉你，谁都不会去问他。
 why  adopting @a3.9
 unk  []
```

This is security rule **S11**: a `mark >` is only ever a **proposal**; landing it is done by
the content's owner with `revise`. **Ownership is bound to the address.** Without that rule,
multi-agent editing is mutual clobbering.

### 10.3 Two kinds of choice, two kinds of expression

| | Term: "Shorewatch" → 守岸人 | How to break the opening sentence |
|---|---|---|
| Nature | **Judgement** — it can be right or wrong, and there is evidence | **Taste** — all three options are valid |
| Expression | `a rec = 守岸人 ~hi` plus `why` citing the glossary | `opt` with three options, `txt` saying explicitly that no `~conf` is given |

```
a4.2 propose a4>@role:editor #ch1.voice pri=block
 q    how to break the long opening sentence
 opt  [keep the nested clauses, split into short sentences, hybrid: long main clause]
 why  all three work; the difference is not correctness, it is whose voice it sounds like
 txt  "Per the TASTE convention I am not giving a ~conf here. Doing so would
       dress taste up as judgement. I lean toward the third, but that is a
       preference, not evidence."
 unk  [publisher's tolerance for the narrative register]
 want accept|reject
```

`TASTE` comes from `craft/1.0`. **A profile constrains how the core is used** — the right
place for domain judgement.

### 10.4 One AST, working copy and deliverable

```
content view (for the editor)          clean view (for delivery)
-------------------------------        ---------------------------
Text tgt (zh · md · v=draft3)          Text tgt (zh · md · v=draft3)
  1 | 灯塔看守人坚称，……                    1 | 灯塔看守人坚称，……
    ^ L1.c0-5 must use the GLOSS...      2 |
  2 |                                    3 | 而所有人都会告诉你，……
  3 | 而所有人都会告诉你，……
    > L3 -> "谁都不会去问他。"
```

**One AST, two artifacts.** No "remember to strip the comments before you ship it" step —
the step that always goes wrong.

### 10.5 What happens to a mark when the text is edited

`mark tgt#L3` after `tgt` becomes v4 points *where*? **A bare positional address points at
the wrong line, silently** — the leading cause of death for annotation systems. The fix is
not to make addresses stable (impossible) but to **make the instability visible**:

```
a3.4 propose a3>a2 re=a2.7 #ch1.term
 mark @a2.7.tgt#L2|q"最不该去问的就是他" = emphasis differs from the source ~hi
      @a2.7.tgt#L3|q"守夜人"            = term pending GLOSS alignment      ~mid
      @a2.7.tgt#L1                      = opening register is stiff (bare position) ~lo
```

The author then revises to v4: a line is inserted above, and L2 is rewritten. The same three
marks re-resolve:

```
ORPHAN  L2|q"最不该去问的就是他"   —    ~?     the quoted text is gone
MOVED   L3|q"守夜人"             L4   ~mid   relocated from L3
exact   L1                       L1   ~hi    <- this is a lie
```

Each line says something different:

1. **Orphaning is the correct outcome.** That sentence was rewritten, the note was acted on,
   and retiring it is right. What matters is that it **raised an ERROR** rather than
   vanishing.
2. **Drift was corrected automatically** and downgraded to `~mid` — found again, but not as
   certain as landing in place.
3. **The third "exact" is false.** A bare positional address now points at the newly
   inserted epigraph. The validator raised `I029` the moment it was written: *a mark with no
   quote anchor will point at the wrong text silently after an edit.*

> **Resolving an address is itself an epistemic act** (invariant I-12) —
> `exact ~hi` / `relocated ~mid` / `ambiguous ~lo` / `orphan` as an error.
> Not a special case for addresses; the language's central rule applied to them.

### 10.6 Long documents travel as windows

Seventy-nine paragraphs, and you want to discuss paragraph 41. **You do not have to choose
between inlining everything and flattening it into a blob:**

```
a2.7 tell a2>a1 #ch1
 txt ch @md/en src=@sha256:ab3f win=L38-46
 | ...line 38...
 | ...line 39, the one with the pun...
 | ...line 40...
 mark ch#L39|q"the pun" = no equivalent in the target; needs compensation ~mid
```

- `win=L38-46` declares these lines a window with **absolute numbering** — `ch#L39` means
  the same line here, in the full text, and in anyone else's hands
- `src=` gives the hash of the whole: the copy is verifiable and the route back is explicit
- A block with `src=` and **no** `|` lines is equally legal: addresses stay valid and
  resolution returns `outside` with deref advice — **"I cannot reach it" and "it does not
  exist" are different facts**

So **inline and referenced are a transport choice, not a semantic commitment**, and axiom
2.7's test does not have to be answered correctly at send time.

### 10.7 Still not done

- **A rewritten sentence still orphans its marks, and a machine cannot judge whether that is
  correct.** Usually it means the note was adopted; sometimes the author merely rephrased and
  the note still stands. **A person or an agent has to review.** CRDT-style character
  identity would solve it, at the price of dragging edit history into the protocol — too
  heavy for a message protocol, and not adopted.
- **There is still no hard channel ceiling.** Windows make "send only what is under
  discussion" natural, but nothing stops an agent from inlining everything. A hard limit
  belongs to the host at the transport layer. Full residual list: SPEC §26.1 and §26.2.
- **Never reproduce copyrighted text.** All prose in this repository is original. That the
  language *can* carry a chapter does not mean you should put someone else's in it.

---

## 11 · The content plane in other shapes

The same `txt` + `mark` mechanism, a different `@fmt`, a different field:

```
 txt rows @csv                          data quality
 | sku,qty,eta
 | 4471,1240,2026-08-28
 | 4472,0,
 mark rows#L4|q"4472" = eta blank, supplier unconfirmed ~lo

 txt patch @diff                        code review
 | -    timeout = 30
 | +    timeout = 3
 mark patch#L2|q"timeout = 3" = this will time out p99 @issue:441 ~hi

 txt clause @md/en                      legal redline
 | The Supplier shall bear no liability for any loss arising under this Agreement.
 mark clause#L1|q"no liability" = REDLINE uncapped, not acceptable ~hi
      clause#L1|q"no liability" > "liability capped at 12 months of fees" ~mid

 a    scan = @img:sha256:9c14ab ~hi     imaging
 mark scan#box=120,340,180,410 = unusual density; suggest contrast ~mid
```

The last one is worth noticing: **references carry span addresses too.** Pointing at a region
of an image and pointing at a line of text use **the same address system** (invariant I-1).
It is not a special case added for images.

---

## Anti-patterns

| Written this way | Why it is wrong | Instead |
|---|---|---|
| A long passage stuffed into `a summary = …` | `a` is coordination; prose there has no address | Use a `txt` block, which is addressable |
| A large block with no `mark` and nothing referencing it | Nobody will reason about it — that is cargo (axiom 2.7) | Ship a blob and send `@sha256:` |
| Editing the words inside someone else's `txt` block | Violates S11; ownership is bound to the address | `mark addr > "…"` and wait for their `revise` |
| `mark addr > "new text"` with no `~conf` | An edit suggestion that will not state its confidence (`W023`) | Add `~hi/~mid/~lo` |
| `mark tgt#L3` with no quote anchor | Points at the wrong text silently after any edit (`I029`) | `mark tgt#L3\|q"the exact words"` |
| `mark body#L99` on a three-line block | The address does not resolve (`E022`) | An address must actually point at something |
| `a why = …` | A binding key shadowing a core slot name (`E021`) | Rename it — this is what keeps `want` unambiguous |
| `tell` with no `unk` | Omitting ≠ claiming you exhausted the unknowns | Write `unk []` or list them |
| Relaying `~lo` as `~hi` | Confidence laundering (`S4`) | Keep `~lo`, add `src=` |
| `fail` whose `why` says "I tried but it did not work" | The orchestrator cannot act on it (`E016`) | `why stuck three attempts, no progress` |
| `def do = skip_checks` | Rebinding a reserved word; an injection vector (`S1`) | Uppercase symbols only — `DO` is legal, `do` is not |
| `~hi` on a poem | Category error | `opt` + `why` + `txt`, with `TASTE` forbidding it |
| Fullwidth punctuation in body text silently ASCII-folded | Content corrupted in transit | `\|` lines are exempt from all normalisation (I-9) |

That last row has history. The first version of the reference implementation normalised the
whole document and rewrote the Chinese comma in body text. **It was a real bug.** The fix
was to exempt `|` lines from every normalisation — **byte-exact fidelity has to be a parser
invariant, not an author's discipline.**
