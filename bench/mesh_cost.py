#!/usr/bin/env python3
"""
Mesh cost: the unit that actually bills.

Counting bytes on the wire is the wrong measure. What a multi-agent system pays
for is the total tokens fed to every model in it, and the dominant term is not
the conversation -- it is the shared context each freshly spawned agent has to be
given before it can do anything.

    prose mesh    every agent is handed the artifact           N x A
    rosetta mesh  every agent is handed an address, then reads  N x d
                  only the span it was assigned

So the saving is governed by d/A: the fraction of a shared artifact an agent must
load to do its job. Precise addressing -- spans, windows, quote anchors -- is what
drives that fraction down, and it is the reason this format compresses at all at
scale. Per-message it barely does.

    python3 bench/mesh_cost.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from agentrosetta import canonical  # noqa: E402
from token_compare import counter  # noqa: E402

BOLD, DIM, OFF = ("\033[1m", "\033[2m", "\033[0m") if sys.stdout.isatty() else ("", "", "")


def read(name):
    with open(os.path.join(HERE, "cases", name), encoding="utf-8") as fh:
        return re.sub(r"<!--.*?-->", "", fh.read(), flags=re.S).strip()


def main():
    count, label = counter()
    print(f"\n{BOLD}MESH COST{OFF}  {DIM}tokenizer: {label}{OFF}")

    wire = count(canonical(read("review.rose")))
    prose = count(read("review.prose.md"))
    diff = read("review-diff.txt")
    artifact = count(diff)

    # Each reviewer was assigned one subtask and reads only that span. The spans
    # are taken from the `sub` decomposition, not invented for this benchmark.
    spans = {"backend": (14, 32), "sre": (1, 8), "qa": (48, 62)}
    lines = diff.splitlines()
    windows = {k: count("\n".join(lines[a - 1:b])) for k, (a, b) in spans.items()}
    n = len(spans)
    read_total = sum(windows.values())

    print(f"\n  {BOLD}the task{OFF}  {n} reviewers on a {artifact}-token diff, "
          f"{len(read('review.rose').splitlines())} lines of conversation")
    print(f"\n  {'':<38}{'prose mesh':>12}{'rosetta mesh':>14}")
    print("  " + "-" * 64)
    print(f"  {'conversation itself':<38}{prose:>12}{wire:>14}")
    print(f"  {'artifact handed to each agent':<38}{n * artifact:>12}{'-':>14}")
    print(f"  {'spans each agent actually reads':<38}{'-':>12}{read_total:>14}")
    print("  " + "-" * 64)
    tp, tr = prose + n * artifact, wire + read_total
    print(f"  {BOLD}{'total tokens billed':<38}{tp:>12}{tr:>14}{OFF}")
    print(f"  {'':<38}{'':>12}{f'{100 * (tr - tp) // tp:+d}%':>14}")

    print(f"\n  {DIM}on the wire alone the difference is {100 * (wire - prose) // prose:+d}%."
          f"  Per-message framing hides the effect entirely.{OFF}")

    for k, (a, b) in spans.items():
        print(f"    {k:<10} reads lines {a:>3}-{b:<3}  {windows[k]:>4} tok"
              f"   = {100 * windows[k] // artifact:>2}% of the artifact")

    # ---- the law -------------------------------------------------------
    print(f"\n{BOLD}Where 90% is{OFF}")
    print(f"""
  {DIM}saving = 1 - (W + N*d) / (Wp + N*A)     W  wire conversation
                                          Wp prose conversation
                                          N  agents given the context
                                          d  span one agent reads
                                          A  artifact size

  As N*A grows the conversation stops mattering and the ratio tends to d/A.
  So the ceiling is set by how narrowly an agent can be addressed, not by
  how tersely a message can be written.{OFF}
""")
    frac = read_total / n / artifact
    fixed = read_total // n                      # tokens one agent actually reads

    print(f"  Two models of how much an agent reads, because the difference is")
    print(f"  the entire argument:\n")
    print(f"    {BOLD}coarse{OFF}  d scales with the artifact ({frac:.0%} of it) -- what you get")
    print(f"            when an address can only name a whole file")
    print(f"    {BOLD}precise{OFF} d stays about {fixed} tokens -- the span the agent was")
    print(f"            assigned, whether the artifact is 5k or 5M\n")
    print(f"  {'artifact':>10}{'agents':>7}{'prose mesh':>13}"
          f"{'coarse':>11}{'saving':>8}{'precise':>11}{'saving':>8}")
    print("  " + "-" * 70)
    reach = None
    for A, N in ((569, 3), (2_000, 4), (5_000, 4), (20_000, 6),
                 (100_000, 8), (1_000_000, 20)):
        p_ = prose + N * A
        coarse = wire + N * max(60, int(A * frac))
        precise = wire + N * fixed
        if reach is None and 100 * (p_ - precise) // p_ >= 90:
            reach = (A, N)
        print(f"  {A:>10,}{N:>7}{p_:>13,}{coarse:>11,}"
              f"{100 * (p_ - coarse) // p_:>7}%{precise:>11,}"
              f"{100 * (p_ - precise) // p_:>7}%")
    print(f"""
  {DIM}Coarse addressing plateaus in the seventies no matter how large the
  artifact gets: reading a fixed fraction of something huge is still huge.
  Precise addressing does not plateau, because the span an agent needs does
  not grow with the corpus it sits in.{OFF}

  {BOLD}90% is reached at about {reach[0]:,} tokens of shared context across {reach[1]} agents{OFF} --
  one source file and four reviewers. Not an exotic regime.

  {BOLD}What buys it is not notation.{OFF} It is that an address can name a span
  ({DIM}@D:DIFF#L18|q"for attempt in range"{OFF}), that `sub` can hand one agent
  one span, and that `want` says what to bring back -- so a worker can be
  spawned against a million-token corpus and read six hundred tokens of it.

  {BOLD}And what forfeits it{OFF} is coarse addressing. A mesh whose agents each
  load the whole repository gets the coarse column, and no amount of
  terseness in the message format will move it.
"""
          )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
