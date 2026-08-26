# Changelog

All notable changes to the language and the reference implementation.
This project follows the versioning rules in [spec/SPEC.md §22](spec/SPEC.md):
MINOR releases are additive only, and anything new must be safely ignorable by an older
parser as a continuation line.

## [2.0.0] — 2026-08-26

The content plane. Version 1.1 had an axiom — *coordination, not cargo* — that pushed all
content into blobs. It was wrong: **content that can only travel as an opaque blob is
content nobody can point at.** 2.0 brings content into the language with structure and
addresses.

### Added

- **`txt` slot** — byte-exact content blocks with `|` line prefixes, an open `@fmt/lang`
  tag, and arbitrary attributes. No closing delimiter, so content can never escape a block.
- **`mark` slot** — standoff annotation over an address. `=` annotates, `>` proposes a
  replacement. Both carry `~conf`. Marks may target another agent's blocks.
- **Address selectors** — an address may carry several selectors separated by `|`, including
  **quote anchors** (`q"text"`, `q"text"@n`) that survive edits.
- **Typed address resolution** — `exact` / `relocated` / `ambiguous` / `outside` / `orphan`,
  each with a resolution confidence. An orphan is an ERROR, never a silent drop.
- **`win=` and `src=`** on blocks — a window into a larger text with **absolute** line
  numbering, plus the content hash of the whole. Inline and referenced become
  interconvertible with addresses unchanged.
- **Elided blocks** — `src=` with no content lines. Addresses stay valid; resolution returns
  `outside` with deref advice, distinguishing *cannot reach* from *does not exist*.
- **`!=` negation** in bindings. A negative claim is now grammar rather than prose.
- **`content` and `clean` views** — the annotated working copy and the deliverable, from one
  AST.
- **Invariants I-12 and I-13**, exception X-6, and diagnostics `E021 E022 W021 W023 W025
  W026 I022 I028 I029`.

### Changed

- **Axiom 2.7 rewritten.** From "content never enters the channel" to "inline what gets
  reasoned about; reference what only gets moved" — a machine-checkable test.
- **`nl` removed**, replaced by `txt`. The old slot conflated a pragmatic signal ("structure
  does not apply") with a content carrier. `txt "one line"` is the short form.
- **`want` disambiguation formalised.** A bare name that is a core slot name requires that
  slot; otherwise it requires that key in `a`. Enforced by a new rule that binding keys may
  not shadow slot names (`E021`).
- Reserved-word checking is **case-sensitive**, so `SRC` is a legal symbol and `src` is not.
- Content lines are **exempt from every normalisation** — no NFC folding, no fullwidth
  substitution, no fence stripping.

### Fixed

- **`def` messages lost their first binding on a round trip.** Serialisation emitted the
  bindings under an `a` slot key, which a `def` body does not accept, so re-parsing silently
  dropped the first line — handshakes and dictionary definitions being exactly the messages
  least able to afford it. Found by `bench/fidelity.py`.
- Fullwidth punctuation in body text was silently ASCII-folded, rewriting Chinese commas.
  Normalisation now applies only at structural positions.
- A `fail` reply was checked against the sender's `want` contract, turning every honest
  failure into a false contract violation.
- Uppercase symbols collided with lowercase header fields under case-folded comparison.
- The degradation path emitted a slot key that no longer existed in the language.

## [1.1.0]

Three-tier vocabulary and profiles. Added `part`, `stop`, `sub`, `at`/`ttl`, `sens`,
role and topic routing, and the thirteen frozen failure codes. Version 1.0 had grown out of
one domain and was not general enough.

## [1.0.0]

Coordination protocol and dual-surface rendering: speech acts, epistemic slots, references,
the obligation state machine, and deterministic human rendering.
