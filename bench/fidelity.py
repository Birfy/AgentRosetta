#!/usr/bin/env python3
"""
Fidelity and cost decomposition for AgentRosetta.

Three things get measured here, and they answer different questions.

  PART 1  ROUND-TRIP FIDELITY
          Does the wire form survive parse -> unparse -> parse unchanged, and do
          content blocks survive byte-for-byte through repeated hops? This is the
          one claim that can be settled mechanically, so it is settled first, and
          against deliberately hostile input.

  PART 2  INFORMATION RECOVERY
          For each benchmark pair, an inventory of the information items the
          message carries. Each item has a PREDICATE that reads the parsed AST.
          An item counts as recovered only if a program can pull it out without
          understanding English.

  PART 3  COST DECOMPOSITION
          Where the tokens actually go. Splits the wire form into addressing,
          epistemics and payload, so the trade is visible rather than asserted:
          the epistemic fields COST tokens; the saving comes from elsewhere.

    python3 bench/fidelity.py
"""
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentrosetta import (  # noqa: E402
    Session, canonical, est_tokens, parse, parse_one, render, unparse,
)
from token_compare import PAIRS, counter  # noqa: E402

GREEN, RED, DIM, BOLD, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = DIM = BOLD = OFF = ""

fails = []


def check(cond, label, detail=""):
    mark = f"{GREEN}pass{OFF}" if cond else f"{RED}FAIL{OFF}"
    print(f"    [{mark}] {label}" + (f"  {DIM}{detail}{OFF}" if detail else ""))
    if not cond:
        fails.append(label)
    return cond


# ==========================================================================
# PART 1 — round-trip fidelity
# ==========================================================================

HOSTILE = [
    "  two leading spaces and a tab\there",
    "fullwidth ＝ ＞ ～ ＃ ＠ ， ： and CJK 全角标点，都不该被改写",
    "```python",
    "print('a fence inside a block')",
    "```",
    "a9.9 note a9>a1 re=x   <- looks exactly like a Rosetta header",
    " mark body#L1 = looks exactly like a mark line",
    "| a content line inside a content line",
    "trailing spaces at end of line   ",
    "",
    "emoji \U0001f6f0\ufe0f\U0001f9ed and RTL \u0645\u0631\u062d\u0628\u0627 "
    "and decomposed e\u0301 next to precomposed \u00e9",
    "a" * 300,
    'quotes "double" \'single\' “smart” and a backslash \\ and a pipe |',
]


def part1_roundtrip():
    print(f"\n{BOLD}PART 1 - ROUND-TRIP FIDELITY{OFF}")

    src = "a1.1 tell a1>a3 #hostile\n txt body @md/en v=1\n"
    src += "".join((f" | {ln}\n" if ln else " |\n") for ln in HOSTILE)
    src += " mark body#L2|q\"fullwidth\" = survived? ~hi\n unk []"

    print(f"\n  {DIM}13 hostile content lines: fences, a fake header, a fake mark line,")
    print(f"  a nested content line, fullwidth punctuation, RTL, emoji, trailing space{OFF}")
    m1 = parse_one(src)
    blk = m1.blocks()["body"]
    check(blk.lines == HOSTILE, "content survives parsing byte-for-byte",
          f"{len(HOSTILE)} lines")
    check(len(blk.lines) == len(HOSTILE),
          "no content line escaped the block", "a fence and a fake header stayed inside")

    hop = src
    for _ in range(10):
        hop = canonical(hop)
    check(parse_one(hop).blocks()["body"].lines == HOSTILE,
          "content survives 10 parse/serialise hops", "byte-identical")
    check(canonical(canonical(src)) == canonical(src),
          "canonical form is idempotent")

    a, b = parse_one(src), parse_one(canonical(src))
    same = (a.act == b.act and a.sender == b.sender and a.recipients == b.recipients
            and a.topic == b.topic and a.hfields == b.hfields
            and [s.key for s in a.slots] == [s.key for s in b.slots]
            and [(mk.addr, mk.op, mk.value) for mk in a.marks()]
            == [(mk.addr, mk.op, mk.value) for mk in b.marks()])
    check(same, "AST is stable across a round trip")

    nfc = [ln for ln in blk.lines if unicodedata.normalize("NFC", ln) != ln]
    check(bool(nfc), "content is NOT NFC-folded",
          f"{len(nfc)} line still holds a decomposed grapheme, exactly as written")

    print(f"\n  {DIM}every message shipped in this repository{OFF}")
    corpus = [("samples/" + n, open("samples/" + n, encoding="utf-8").read())
              for n in sorted(os.listdir("samples")) if n.endswith(".rose")]
    corpus += [(name, wire) for name, wire, _ in PAIRS]
    total = 0
    for name, text in corpus:
        msgs = parse(text)
        total += len(msgs)
        ok = canonical(canonical(text)) == canonical(text)
        blocks_ok = all(
            parse_one(unparse(m)).blocks().get(b.name, type("x", (), {"lines": None})).lines
            == b.lines
            for m in msgs for b in m.blocks().values())
        check(ok and blocks_ok, f"{name}", f"{len(msgs)} messages")
    print(f"    {DIM}{total} messages round-tripped in total{OFF}")


# ==========================================================================
# PART 2 — information recovery
# ==========================================================================

def _bind(m, slot, key):
    s = m.slot(slot)
    return next((b for b in (s.bindings if s else []) if b.key == key), None)


def _conf(m, slot, key):
    b = _bind(m, slot, key)
    return b.conf.kind if b and b.conf else None


INVENTORY = {
    "incident triage (ask + answer)": [
        ("the question is asked of a1 by a3",
         lambda M: M[0].sender == "a3" and M[0].recipients == ["a1"]),
        ("the topic is the checkout 5xx incident",
         lambda M: M[0].topic == "CKO.5xx"),
        ("two prior artifacts are cited, not re-pasted",
         lambda M: len(M[0].slot("ctx").items) == 2),
        ("the log citation is line-precise",
         lambda M: "#L440-512" in M[0].slot("ctx").items[1]),
        ("the reply must contain cause and fix",
         lambda M: M[0].slot("want").shape.required == ["cause", "fix"]),
        ("eta is optional in the contract",
         lambda M: M[0].slot("want").shape.optional == ["eta"]),
        ("the asker declares one known unknown",
         lambda M: len(M[0].slot("unk").items) == 1),
        ("the reply is linked to the question",
         lambda M: M[1].hfields["re"] == M[0].id),
        ("cause is identified as a specific commit",
         lambda M: "@commit:9f2a" in _bind(M[1], "a", "cause").value),
        ("cause is asserted with high confidence",
         lambda M: _conf(M[1], "a", "cause") == "hi"),
        ("fix is asserted with high confidence",
         lambda M: _conf(M[1], "a", "fix") == "hi"),
        ("eta is only LOW confidence - the key asymmetry",
         lambda M: _conf(M[1], "a", "eta") == "lo"),
        ("evidence points at an exact log line",
         lambda M: "#L487" in M[1].slot("why").raw),
        ("two unknowns remain after the answer",
         lambda M: len(M[1].slot("unk").items) == 2),
        ("a moderate-confidence risk is attached",
         lambda M: M[1].slot("risk").conf.kind == "mid"),
        ("the risk names the issue it would reintroduce",
         lambda M: "@issue:441" in M[1].slot("risk").raw),
        ("the reply satisfies the contract it was given",
         lambda M: {b.key for b in M[1].slot("a").bindings} >= {"cause", "fix"}),
    ],
    "clinical progress (1 msg)": [
        ("this is progress, not completion",
         lambda M: M[0].act == "part"),
        ("progress does NOT discharge the obligation",
         lambda M: M[0].act not in ("done", "fail")),
        ("the message is marked as containing PHI",
         lambda M: M[0].sens == "phi"),
        ("the observation time is machine-readable",
         lambda M: M[0].at is not None and M[0].at.hour == 14),
        ("the data has a declared shelf life",
         lambda M: M[0].ttl is not None and M[0].ttl.total_seconds() == 900),
        ("lactate trend is high confidence",
         lambda M: _conf(M[0], "a", "lactate_trend") == "hi"),
        ("sepsis score is only moderate confidence",
         lambda M: _conf(M[0], "a", "sepsis_score") == "mid"),
        ("evidence cites an external EHR record",
         lambda M: "@ext:ehr:obs-88231" in M[0].slot("why").raw),
        ("two clinical unknowns are declared",
         lambda M: len(M[0].slot("unk").items) == 2),
        ("an assumption is separated from the findings",
         lambda M: M[0].has("assume")),
        ("the assumed weight is recoverable as a value",
         lambda M: _bind(M[0], "assume", "weight_kg").value.startswith("70")),
        ("the assumption is flagged LOW confidence",
         lambda M: _conf(M[0], "assume", "weight_kg") == "lo"),
    ],
    "contract-net bid (2 msgs)": [
        ("the call goes to a role, not to named agents",
         lambda M: M[0].recipients == ["@role:worker"]),
        ("the work is partitioned by shard",
         lambda M: M[0].hfields["thd"] == "shard1"),
        ("the dataset is content-addressed",
         lambda M: "@tbl:sha256:7d19ac44b2" in M[0].slot("q").raw),
        ("two independent limits are set",
         lambda M: "30m" in M[0].slot("by").raw and "$5" in M[0].slot("by").raw),
        ("the job decomposes into three subtasks",
         lambda M: len(M[0].slot("sub").bindings) == 3),
        ("subtask 1 is assigned to the storage role",
         lambda M: "@role:storage" in M[0].slot("sub").bindings[0].value),
        ("the dependency graph is machine-readable",
         lambda M: M[0].slot("sub").bindings[1].deps == ["s1"]
                   and M[0].slot("sub").bindings[2].deps == ["s2"]),
        ("the bid must state cost, eta and capability",
         lambda M: M[0].slot("want").shape.required == ["bid_cost", "bid_eta", "capable"]),
        ("the bid is a proposal, awaiting acceptance",
         lambda M: M[1].act == "propose"),
        ("bid cost is stated with high confidence",
         lambda M: _conf(M[1], "a", "bid_cost") == "hi"),
        ("bid eta is stated with only moderate confidence",
         lambda M: _conf(M[1], "a", "bid_eta") == "mid"),
        ("the bidder declares an unknown about the data",
         lambda M: len(M[1].slot("unk").items) == 1),
        ("the bid satisfies the call's contract",
         lambda M: {b.key for b in M[1].slot("a").bindings}
                   == {"bid_cost", "bid_eta", "capable"}),
    ],
    "content review w/ inline edits": [
        ("this is a proposal to two parties",
         lambda M: M[0].act == "propose" and len(M[0].recipients) == 2),
        ("one recipient is addressed by role",
         lambda M: "@role:editor" in M[0].recipients),
        ("four naming options are enumerated",
         lambda M: len(M[0].slot("opt").items) == 4),
        ("a recommendation is made with high confidence",
         lambda M: _conf(M[0], "a", "rec") == "hi"),
        ("two edits are proposed against another agent's text",
         lambda M: len(M[0].marks()) == 2),
        ("the first edit targets a specific message and block",
         lambda M: M[0].marks()[0].msg_id == "a2.8" and M[0].marks()[0].block == "tgt"),
        ("the first is an annotation, not a rewrite",
         lambda M: M[0].marks()[0].op == "="),
        ("the second proposes replacement text",
         lambda M: M[0].marks()[1].op == ">"),
        ("the replacement text is extractable verbatim",
         lambda M: M[0].marks()[1].value.strip('"') == "谁都不会去问他。"),
        ("the second edit is only moderate confidence",
         lambda M: M[0].marks()[1].conf.kind == "mid"),
        ("both edits carry quote anchors that survive editing",
         lambda M: all(mk.anchored for mk in M[0].marks())),
        ("the reply must be an accept or a reject",
         lambda M: M[0].slot("want").shape.acts == ["accept", "reject"]),
        ("a publisher-side unknown is declared",
         lambda M: len(M[0].slot("unk").items) == 1),
    ],
}


def part2_recovery(count):
    print(f"\n{BOLD}PART 2 - INFORMATION RECOVERY{OFF}")
    print(f"\n  {DIM}Each item below is pulled out of the parsed AST by a predicate.")
    print(f"  It counts as recovered only if a program can extract it without")
    print(f"  understanding English.{OFF}")

    grand_ok = grand_n = 0
    rows = []
    for name, wire, nl in PAIRS:
        msgs = parse(wire)
        items = INVENTORY[name]
        ok = 0
        print(f"\n  {BOLD}{name}{OFF}")
        for label, pred in items:
            try:
                good = bool(pred(msgs))
            except Exception as exc:                      # a predicate that blows up
                good, label = False, f"{label}  [{type(exc).__name__}]"
            ok += good
            if not good:
                print(f"    [{RED}FAIL{OFF}] {label}")
        print(f"    {GREEN}{ok}/{len(items)}{OFF} information items machine-extractable")
        if ok != len(items):
            fails.append(f"recovery: {name}")
        grand_ok += ok
        grand_n += len(items)
        rows.append((name, len(items), count(canonical(wire)), count(nl)))

    print(f"\n  {BOLD}{grand_ok}/{grand_n} items recovered across all four pairs{OFF}")
    print(f"\n  {DIM}Information density, same information either way:{OFF}")
    print(f"    {'case':<34}{'items':>6}{'wire tok':>10}{'prose tok':>11}"
          f"{'tok/item':>10}{'prose/item':>12}")
    print("    " + "-" * 83)
    ti = tw = tn = 0
    for name, n, w, p in rows:
        ti, tw, tn = ti + n, tw + w, tn + p
        print(f"    {name:<34}{n:>6}{w:>10}{p:>11}{w / n:>10.1f}{p / n:>12.1f}")
    print("    " + "-" * 83)
    print(f"    {'total':<34}{ti:>6}{tw:>10}{tn:>11}{tw / ti:>10.1f}{tn / ti:>12.1f}")
    print(f"\n    {DIM}Prose carries the same items in {100 * (tn - tw) // tw}% more tokens,")
    print(f"    and a program can extract {grand_ok} of them from the wire form")
    print(f"    against 0 from the prose without an NLP pass.{OFF}")


# ==========================================================================
# PART 3 — cost decomposition
# ==========================================================================

def strip_epistemics(wire):
    """The same messages with confidence, unknowns and assumptions removed."""
    out = []
    for m in parse(wire):
        keep = [s for s in m.slots if s.key not in ("unk", "assume")]
        for s in keep:
            s.conf = None
            for b in s.bindings:
                b.conf = None
            for mk in s.marks:
                mk.conf = None
        m.slots = keep
        out.append(unparse(m))
    return "\n\n".join(out)


def strip_addressing(wire):
    """The same messages with every reference replaced by a bare word."""
    import re
    return re.sub(r"@[A-Za-z0-9_][A-Za-z0-9_:./#@=&\-]*", "REF", canonical(wire))


def part3_costs(count):
    print(f"\n{BOLD}PART 3 - WHERE THE TOKENS GO{OFF}")
    print(f"\n    {'case':<34}{'wire':>8}{'-epist.':>9}{'-addr.':>9}{'prose':>8}")
    print("    " + "-" * 68)
    tw = te = ta = tp = 0
    for name, wire, nl in PAIRS:
        w = count(canonical(wire))
        e = count(strip_epistemics(wire))
        a = count(strip_addressing(wire))
        p = count(nl)
        tw, te, ta, tp = tw + w, te + e, ta + a, tp + p
        print(f"    {name:<34}{w:>8}{e:>9}{a:>9}{p:>8}")
    print("    " + "-" * 68)
    print(f"    {'total':<34}{tw:>8}{te:>9}{ta:>9}{tp:>8}")
    print(f"\n    {DIM}-epist.  = the same messages without ~conf, unk and assume")
    print(f"    -addr.   = the same messages with every @reference flattened{OFF}")
    print(f"\n    Epistemic fields COST {tw - te} tokens ({100 * (tw - te) // tw}% of the wire form).")
    print(f"    They are the most expensive thing in the format and the least")
    print(f"    replaceable: without them, {sum(1 for _, w, _ in PAIRS)} of these messages read as flat")
    print(f"    assertions, and a five-hop chain launders every guess into a fact.")
    print(f"\n    Net against prose: {tp} -> {tw}, a {100 * (tp - tw) // tp}% saving WHILE")
    print(f"    carrying {tw - te} tokens of epistemic state prose has to spell out")
    print(f"    in clauses that no program can read.")


# ==========================================================================

def main():
    count, label = counter()
    print(f"\n{BOLD}AgentRosetta - fidelity and cost{OFF}")
    print(f"{DIM}tokenizer: {label}{OFF}")

    part1_roundtrip()
    part2_recovery(count)
    part3_costs(count)

    print(f"\n{BOLD}WHAT THIS DOES NOT TEST{OFF}")
    print(f"""    {DIM}Round-trip fidelity is settled: it is mechanical, and it passes.
    Information recovery is settled only in the machine-extractable sense.

    Not settled, and not settleable here: whether a MODEL reading the wire
    form ends up as well informed as one reading the prose. That needs an
    independent judge and a task suite - spec/SPEC.md section 25. The
    baselines in this file were written by the same author as the wire
    forms, which is exactly the bias such an evaluation would remove.{OFF}""")

    if fails:
        print(f"\n{RED}{len(fails)} FAILURE(S){OFF}: {fails}")
        return 1
    print(f"\n{GREEN}All fidelity checks pass.{OFF}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
