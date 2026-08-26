#!/usr/bin/env python3
"""
Token comparison: AgentRosetta wire form vs. an equivalent natural-language message.

WHAT THIS IS
    Four hand-written pairs. Each pair carries the SAME information — including
    the parts natural language usually drops: per-claim confidence, known
    unknowns, and precise references. Anything less would not be a comparison,
    it would be a strawman.

WHAT THIS IS NOT
    A benchmark. Four examples measure a format, not a system. The number that
    would actually matter is task success rate at a fixed token budget across a
    multi-domain suite — see spec/SPEC.md §25. Until that runs, treat everything
    here as illustrative.

    The weakest link is the baselines: they are our own prose. We tried to write
    what a competent model actually emits, not padding. Disagree? Edit them and
    rerun — that is why they are in this file rather than in a table in a README.

    python3 bench/token_compare.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agentrosetta import canonical  # noqa: E402

# --------------------------------------------------------------------------

INCIDENT_R = """
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
 risk  reverting reintroduces the slow query in @issue:441   ~mid
"""

INCIDENT_N = """\
Could you look into the elevated 5xx rate on the checkout service? I've already \
pulled the context in my earlier message and the log lines 440-512 of log/2f9c. \
I need three things back: the root cause, the fix, and ideally an ETA. One thing \
I genuinely don't know is when the config change happened.

I found it. Commit 9f2a lowered http.timeout from 30s to 3s, and I'm confident \
that's the cause — the timeout errors in log/2f9c start at line 487, at 14:02, \
which matches the deploy time to within about 40 seconds. The fix is to revert \
9f2a; I'm confident about that too. For the ETA I'd guess around 12 minutes, but \
that's a low-confidence guess since CI timing varies. Two things I couldn't \
determine: who approved 9f2a, and whether other services are affected. One \
moderate risk to flag: reverting will probably reintroduce the slow query from \
issue 441."""

# --------------------------------------------------------------------------

TRIAGE_R = """
a2.40 part a2>a1 #triage.bed7 at=@t:2026-08-26T14:02Z ttl=15m sens=phi
 a      lactate_trend = rising  ~hi
        sepsis_score  = 3 of 6  ~mid
 why    @ext:ehr:obs-88231 three consecutive samples rising
 unk    [fluid intake last 6h, prior antibiotics]
 assume weight_kg = 70 standard adult estimate, not measured ~lo
"""

TRIAGE_N = """\
Progress update on bed 7 — note this contains PHI, and these observations were \
taken at 14:02 UTC on 2026-08-26; treat them as stale after about 15 minutes. \
The lactate trend is rising and I'm confident about that; the sepsis score is 3 \
out of 6, which I'd call a moderate-confidence read. The evidence is EHR \
observation obs-88231, where three consecutive samples are rising. Two things I \
don't know: fluid intake over the last six hours, and whether the patient has \
had antibiotics already. I should also flag an assumption I made: I used 70kg as \
the weight, which is a standard adult estimate rather than a measured value, so \
treat anything downstream of it as low confidence."""

# --------------------------------------------------------------------------

BID_R = """
a1.20 do a1>@role:worker #reindex thd=shard1
 q     rebuild the index over @tbl:sha256:7d19ac44b2
 by    30m | $5
 sub   s1 = pull snapshot   @role:storage
       s2 = build inverted  on=s1
       s3 = canary cutover  on=s2
 want  {bid_cost, bid_eta, capable}

a5.3 propose a5>a1 re=a1.20
 a     bid_cost = $3.2 ~hi
       bid_eta  = 18m  ~mid
       capable  = yes  ~hi
 unk   [whether the dataset has nested fields]
"""

BID_N = """\
This goes out to anyone acting as a worker — it's shard 1 of the reindex job. I \
need the index rebuilt over table sha256:7d19ac44b2, within 30 minutes and under \
$5. The work breaks into three steps: pull the snapshot (that's for whoever holds \
the storage role), build the inverted index once the snapshot is done, and then \
do a canary cutover once the build is done. When you reply, please tell me your \
cost estimate, your ETA, and whether you're capable of doing it at all.

I can take it. My cost estimate is $3.2 and I'm confident in that figure. ETA is \
18 minutes, though I'd only call that moderate confidence. Yes, I'm capable — \
confident. One thing I don't know is whether the dataset contains nested fields."""

# --------------------------------------------------------------------------

REVIEW_R = """
a3.4 propose a3>a2,@role:editor re=a2.8 #ch1.term
 q      Chinese name for "Shorewatch"
 opt    [守岸人, 岸哨, 望海人, transliterate "肖沃奇"]
 a      rec = 守岸人 ~hi
 why    already in GLOSS v3; matches the book's other maritime coinages ~hi
 mark   @a2.8.tgt#L1|q"灯塔看守人" = must use the GLOSS name here ~hi
        @a2.8.tgt#L3|q"最不该去问的就是他" > "谁都不会去问他。" ~mid
 unk    [whether the publisher requires cross-volume consistency]
 want   accept|reject
"""

REVIEW_N = """\
About the Chinese name for "Shorewatch", replying to your draft message. Four \
options are on the table: 守岸人, 岸哨, 望海人, or transliterating it as 肖沃奇. \
I recommend 守岸人 and I'm confident about it: it's already in GLOSS v3 and it \
matches the construction of the book's other maritime coinages, which I'm also \
confident about.

Two specific changes to your draft. First, on line 1, where you currently have \
"灯塔看守人" — that needs to use the GLOSS name instead; I'm confident about \
that. Second, on line 3, the phrase "最不该去问的就是他" should become \
"谁都不会去问他。", though I'd call that a moderate-confidence suggestion rather \
than a firm one. Please note both are proposals — you own the text, so apply \
them yourself if you agree.

One thing I don't know: whether the publisher requires consistency across \
volumes. Let me know whether you accept or reject."""

PAIRS = [
    ("incident triage (ask + answer)", INCIDENT_R, INCIDENT_N),
    ("clinical progress (1 msg)", TRIAGE_R, TRIAGE_N),
    ("contract-net bid (2 msgs)", BID_R, BID_N),
    ("content review w/ inline edits", REVIEW_R, REVIEW_N),
]


def counter():
    """Return (fn, label). Real BPE if tiktoken is installed, else an estimate."""
    try:
        import tiktoken
        for name in ("o200k_base", "cl100k_base"):
            try:
                enc = tiktoken.get_encoding(name)
                return (lambda t: len(enc.encode(t))), f"tiktoken/{name}"
            except Exception:
                continue
    except ImportError:
        pass

    def est(t):
        cjk = sum(1 for c in t if "一" <= c <= "鿿")
        return cjk + max(0, len(t) - cjk) // 4
    return est, "heuristic (pip install tiktoken for real counts)"


def main() -> int:
    count, label = counter()
    print(f"\nAgentRosetta — channel token comparison\ntokenizer: {label}\n")
    print(f"  {'case':<34}{'natural':>9}{'rosetta':>9}{'saved':>8}")
    print("  " + "-" * 60)
    tot_n = tot_r = 0
    for name, wire, nl in PAIRS:
        r = count(canonical(wire))
        n = count(nl)
        tot_n += n
        tot_r += r
        print(f"  {name:<34}{n:>9}{r:>9}{100 * (n - r) // n:>7}%")
    print("  " + "-" * 60)
    print(f"  {'total':<34}{tot_n:>9}{tot_r:>9}{100 * (tot_n - tot_r) // tot_n:>7}%\n")
    print("  Read the docstring before quoting any of this. Four hand-written pairs")
    print("  measure a format, not a system; the number that matters is task success")
    print("  at a fixed budget, which is not measured here (spec/SPEC.md §25).")
    print("  Note the last row: content-heavy messages compress least, because the")
    print("  content is the same bytes either way. That is the honest shape of it.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
