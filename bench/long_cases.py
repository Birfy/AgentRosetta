#!/usr/bin/env python3
"""
Long-case compression: does the saving scale with conversation length?

It does not. That is the finding, and it contradicts what this project assumed
before the measurement existed.

The short benchmark (bench/token_compare.py) shows ~21% on one- and two-message
exchanges. The reasoning attached to that number used to be: "the saving comes from
reference discipline, which a short exchange barely exercises" - implying longer
conversations would do better.

A 24-message incident investigation says otherwise. Against equally informative
prose written by a disciplined agent, the wire form comes out slightly LARGER.
The decomposition explains why, and the crossover model below says when it flips.

    python3 bench/long_cases.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from agentrosetta import REF_RE, canonical, parse, unparse  # noqa: E402
from token_compare import counter  # noqa: E402

BOLD, DIM, OFF = ("\033[1m", "\033[2m", "\033[0m") if sys.stdout.isatty() else ("", "", "")

CASES = [
    ("incident-24", "a 24-message incident investigation: five agents, one human,"
                    " deploy correlation, rollback, a retraction, a drafted statement"),
]


def read(path):
    with open(os.path.join(HERE, "cases", path), encoding="utf-8") as fh:
        return re.sub(r"<!--.*?-->", "", fh.read(), flags=re.S).strip()


def decompose(wire, count):
    """Split the wire form into envelope, references, epistemics, keys, payload."""
    msgs = parse(wire)
    hdr = sum(count(unparse(m).splitlines()[0]) for m in msgs)
    refs = REF_RE.findall(wire)
    ref_tok = sum(count(r) for r in refs)
    conf_tok = sum(count(c) for c in re.findall(r"~(?:hi|mid|lo|\?)", wire))
    keys = sum(count(" " + ln.strip().split()[0]) for ln in wire.splitlines()
               if ln.startswith(" ") and ln.strip() and not ln.strip().startswith("|"))
    total = count(wire)
    return {
        "messages": len(msgs), "total": total, "envelope": hdr, "refs": ref_tok,
        "n_refs": len(refs), "conf": conf_tok, "keys": keys,
        "payload": total - hdr - ref_tok - conf_tok - keys,
    }


def main():
    count, label = counter()
    print(f"\n{BOLD}AgentRosetta - long-case compression{OFF}\n{DIM}tokenizer: {label}{OFF}")

    for name, blurb in CASES:
        wire = canonical(read(f"{name}.rose"))
        disc = read(f"{name}.prose.md")
        rep = read(f"{name}.repaste.md")
        w, d, r = count(wire), count(disc), count(rep)
        parts = decompose(wire, count)

        print(f"\n{BOLD}{name}{OFF}  {DIM}{blurb}{OFF}")
        print(f"\n    {'variant':<38}{'tokens':>8}{'vs wire':>10}")
        print("    " + "-" * 56)
        print(f"    {'rosetta wire':<38}{w:>8}{'-':>10}")
        print(f"    {'prose, disciplined agent':<38}{d:>8}{100 * (w - d) // d:>9}%")
        print(f"    {'prose, re-pasting agent':<38}{r:>8}{100 * (w - r) // r:>9}%")

        print(f"\n    {BOLD}Against disciplined prose the wire form is "
              f"{abs(100 * (w - d) // d)}% "
              f"{'LARGER' if w > d else 'smaller'}.{OFF}")

        print(f"\n    {DIM}where the wire form's {parts['total']} tokens go"
              f" ({parts['messages']} messages){OFF}")
        for k, lbl in (("envelope", "message headers"), ("refs", "@references"),
                       ("keys", "slot keys"), ("conf", "~confidence"),
                       ("payload", "payload")):
            n = parts[k]
            bar = "#" * round(40 * n / parts["total"])
            print(f"      {lbl:<18}{n:>6}  {100 * n // parts['total']:>3}%  {DIM}{bar}{OFF}")

        per = parts["envelope"] / parts["messages"]
        prose_hdr = count("**a4 -> a1.**")
        print(f"""
    {BOLD}Why.{OFF} Two fixed costs grow linearly with the message count and
    swamp what the format saves per message.

      1. {BOLD}The envelope.{OFF} {per:.0f} tokens per header x {parts['messages']} messages
         = {parts['envelope']}. Prose addresses the same thing in about
         {prose_hdr} tokens, so the structure costs
         ~{parts['envelope'] - prose_hdr * parts['messages']} tokens over the conversation.

      2. {BOLD}References are not free.{OFF} {parts['n_refs']} of them, {parts['refs']} tokens,
         {100 * parts['refs'] // parts['total']}% of the message. A machine-readable address such as
         @dash:grafana/cko-5xx#from=14:00&to=14:15 costs MORE than the English
         phrase it replaces. Pointing only pays when the alternative is
         carrying the thing pointed at.

    {BOLD}What is cheap.{OFF} The epistemic markers, at {parts['conf']} tokens
    ({100 * parts['conf'] // parts['total']}%). Confidence, the part of this design that
    actually changes behaviour downstream, is nearly free. It is the
    addressing that costs.""")

        crossover(w, d, parts, count)

    print(f"""
{BOLD}WHAT THIS CHANGES{OFF}

    The 21% headline from bench/token_compare.py holds for what it measures:
    single exchanges, where prose ceremony is a large share of a short message.
    {BOLD}It does not generalise to long conversations, and this repository no
    longer claims that it does.{OFF}

    Treat AgentRosetta's token story as: roughly neutral to modestly positive on
    coordination traffic, clearly positive when agents would otherwise re-paste
    artifacts, and negative if you address everything with long URIs out of habit.

    The case for the format was never mainly compression. This is the measurement
    that makes that sentence honest rather than defensive.
""")
    return 0


def crossover(wire, prose, parts, count):
    """When does referencing beat carrying? Arithmetic, stated openly."""
    print(f"""
    {BOLD}Crossover.{OFF} {DIM}An agent that cannot dereference has to carry the
    artifact. One that can sends an address. Suppose a conversation needs S
    tokens of artifact content that prose must inline and the wire form
    references at ~{parts['refs'] // max(1, parts['n_refs'])} tokens each.{OFF}
""")
    gap = wire - prose
    per_ref = max(1, parts["refs"] // max(1, parts["n_refs"]))
    print(f"      {'artifact content needed':<28}{'prose':>9}{'wire':>9}{'delta':>9}")
    print("      " + "-" * 55)
    for s in (0, 200, 500, 1000, 2000, 5000):
        n_new = 0 if s == 0 else max(1, s // 400)
        p, w = prose + s, wire + n_new * per_ref
        print(f"      {s:>6} tokens ({n_new:>2} artifacts) {p:>9}{w:>9}"
              f"{100 * (w - p) // p:>8}%")
    print(f"""
      {DIM}Break-even sits near {max(0, gap) * 400 // max(1, 400 - per_ref)} tokens of shared artifact content.
      Below it, disciplined prose wins. Above it, addressing wins, and the
      margin widens without bound - which is the regime multi-agent systems
      spawning fresh workers actually live in.{OFF}""")


if __name__ == "__main__":
    raise SystemExit(main())
