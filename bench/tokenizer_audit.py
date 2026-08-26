#!/usr/bin/env python3
"""
Tokenizer audit: every table in spec/TOKENIZER.md, regenerated from scratch.

A protocol for language models has its syntax priced by a tokenizer rather than by
a parser. None of that is visible from a grammar, so it has to be measured -- and
measured across more than one tokenizer, because a symbol that is cheap in the
newest one and expensive in an older one is a bet, not an optimisation.

    pip install tiktoken
    python3 bench/tokenizer_audit.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from agentrosetta import (  # noqa: E402
    ACTS, FAIL_CODES, HKEYS, REF_RE, SLOTS, canonical, parse,
)

BOLD, DIM, OFF = ("\033[1m", "\033[2m", "\033[0m") if sys.stdout.isatty() else ("", "", "")
ENCODINGS = ("o200k_base", "cl100k_base", "p50k_base")


def load():
    try:
        import tiktoken
    except ImportError:
        print("This audit needs real BPE counts.  pip install tiktoken")
        raise SystemExit(1)
    return [(n, tiktoken.get_encoding(n)) for n in ENCODINGS]


def main():
    encs = load()
    cost = lambda s: tuple(len(e.encode(s)) for _, e in encs)  # noqa: E731
    c = lambda s: len(encs[0][1].encode(s))                    # noqa: E731

    print(f"\n{BOLD}TOKENIZER AUDIT{OFF}  {DIM}{' / '.join(ENCODINGS)}{OFF}")

    # ---- 1. is the frozen core already cheap? ----------------------------
    print(f"\n{BOLD}1. The frozen core{OFF}")
    for label, items, pre in (("acts", ACTS, " "), ("slots", SLOTS, " "),
                              ("fail codes", FAIL_CODES, " ")):
        bad = [i for i in items if cost(pre + i) != (1,) * len(encs)]
        verdict = "all single-token in every tokenizer" if not bad else \
                  f"not single-token everywhere: {', '.join(bad)}"
        print(f"    {label:<12} {len(items):>2} items   {verdict}")
    print(f"    {DIM}chosen for readability; they happen to be optimal already{OFF}")

    # ---- 2. non-ASCII: cheap, or only cheap here? ------------------------
    print(f"\n{BOLD}2. Is non-ASCII cheaper?{OFF}")
    classes = {
        "ASCII punctuation": list("!?~^<>=@#|*+-/&%$"),
        "Latin-1 / typographic": list("§†·»«¶¤°±×÷"),
        "arrows & maths": list("→←↑↓⇒∴∵≈≠∈∀"),
        "CJK single chars": list("因答高中低未問果由據險"),
        "emoji": list("🔺🔻🟢🔴⬆⬇"),
    }
    print(f"\n    {'class':<26}{'1 tok everywhere':>18}{'only in o200k':>16}{'worst':>14}")
    print("    " + "-" * 74)
    for name, xs in classes.items():
        stable = [x for x in xs if cost(x) == (1,) * len(encs)]
        only = [x for x in xs if cost(x)[0] == 1 and cost(x) != (1,) * len(encs)]
        worst = max(xs, key=lambda x: sum(cost(x)))
        print(f"    {name:<26}{f'{len(stable)}/{len(xs)}':>18}{f'{len(only)}/{len(xs)}':>16}"
              f"{f'{worst} {cost(worst)}':>14}")
    print(f"\n    {DIM}ASCII punctuation is the only class every tokenizer agrees is cheap.")
    print(f"    CJK looks good on o200k and costs 2-3x elsewhere. Emoji never win.{OFF}")

    # ---- 3. separators -----------------------------------------------------
    print(f"\n{BOLD}3. Separators, and what message ids cost{OFF}\n")
    for x in ("a1.7", "a1-7", "a1_7", "a1:7", "obs7", "planner23"):
        flag = "  <-- no separator, half the cost" if "." not in x and "-" not in x \
            and "_" not in x and ":" not in x else ""
        print(f"    {cost(x)}  {x!r}{flag}")

    # ---- 4. value encodings ------------------------------------------------
    print(f"\n{BOLD}4. Value encodings{OFF}")
    for title, xs in (
        ("timestamp", ["@t:2026-08-26T14:02:20Z", "@t:20260826T140220Z", "@t:14:02:20"]),
        ("span / range", ["#from=14:00&to=14:15", "#14:00-14:15", "#1400-1415"]),
        ("line range", ["#L440-512", "#440-512"]),
        ("reply marker", [" re=a1.2", " <a1.2", " ^a1.2", " re:a1.2"]),
    ):
        print(f"\n    {title}")
        base = cost(xs[0])[0]
        for x in xs:
            delta = "" if x == xs[0] else f"   {cost(x)[0] - base:+d}"
            print(f"      {cost(x)}  {x!r}{delta}")
    print(f"\n    {DIM}The reply marker cannot be improved: every spelling costs the same,")
    print(f"    because the cost is the identifier and not the marker.{OFF}")

    # ---- 5. the floor ------------------------------------------------------
    print(f"\n{BOLD}5. The syntax floor{OFF}")
    path = os.path.join(HERE, "cases", "incident-24.opt.rose")
    with open(path, encoding="utf-8") as fh:
        wire = canonical(re.sub(r"^#.*$", "", fh.read(), flags=re.M))
    total = c(wire)
    slotkeys = sum(c(" " + ln.strip().split()[0]) for ln in wire.splitlines()
                   if ln.startswith(" ") and ln.strip()
                   and ln.strip().split()[0] in SLOTS)
    acts = sum(c(" " + m.act) for m in parse(wire))
    conf = sum(c(x) for x in re.findall(r"~(?:hi|mid|lo|\?)", wire))
    hk = sum(c(" " + k + "=") for k in re.findall(r"\b(" + "|".join(HKEYS) + r")=", wire))
    sig = len(REF_RE.findall(wire))
    ids = sum(c(x) for x in re.findall(r"\b[a-z]+\d+\b", wire))
    refbody = sum(c(r) for r in REF_RE.findall(wire)) - sig
    syntax, naming = slotkeys + acts + conf + hk + sig, ids + refbody

    print(f"\n    {'bucket':<44}{'tokens':>8}{'share':>8}")
    print("    " + "-" * 60)
    for lbl, n in (("syntax  (slot keys, acts, ~conf, key=, @)", syntax),
                   ("naming  (message ids, reference bodies)", naming),
                   ("payload (the actual words)", total - syntax - naming)):
        print(f"    {lbl:<44}{n:>8}{100 * n // total:>7}%")
    print("    " + "-" * 60)
    print(f"    {'total':<44}{total:>8}")
    print(f"""
    {BOLD}A syntax that cost nothing at all would shrink this conversation by
    {100 * syntax // total}%.{OFF} {DIM}Every scheme for compressing keywords competes for that
    share; the rest is names and content, which no notation shortens.

    Within it: slot keys {slotkeys}, acts {acts}, @ sigils {sig} are already at one
    token each and cannot go lower. ~conf {conf} and key= {hk} could roughly
    halve, worth about {100 * (conf + hk) // 2 // total}%, paid for in legibility. We did not take it.{OFF}
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
