<!-- Prose baseline for the same review. Each reviewer quotes the code it is
     commenting on, because a line number alone is ambiguous to a reader who is
     not looking at the same rendering, and because reviewers are spawned fresh
     and cannot assume the other two loaded the diff. Same findings, same
     confidences, same unknowns. -->

**cmd -> everyone.** Terms: PR is pull request 812, the payment client retry and
timeout change. DIFF is the reviewed diff at pr/812.diff, 62 lines. GATE means it
must pass correctness, config safety and test coverage before merge.

**cmd -> whoever holds the reviewer role.** Please review PR 812 against GATE.
Three subtasks: correctness of the retry loop for backend, config and rollout
safety for SRE, test coverage for QA. Two hours. When you reply I need a verdict —
block, comment or approve — and a list of findings.

**backend -> cmd.** Taking it.

**backend -> cmd.** My verdict is block, and I am confident. Two findings, both
held with high confidence: the retry-on-5xx is not idempotent, and PaymentError's
arity changed.

On the first: the diff introduces

> `for attempt in range(self.retries + 1):`

which retries a POST that already carries an idem_key, but the upstream is only
idempotent within its own window, so a 500 arriving after the charge has committed
will double-charge. High confidence.

On the second, the diff changes the raise to

> `raise PaymentError(resp.status, order_id)`

The arity changed, so every caller that constructs PaymentError breaks. High
confidence.

My reasoning is that the idem_key is threaded into the payload variable but never
actually sent upstream. One unknown: whether the payment provider dedupes on
idem_key server-side. And a high-confidence risk worth stating plainly — a
double-charge on retry is a money bug, not a latency bug.

**sre -> cmd.** Taking it.

**sre -> cmd.** Verdict block, high confidence. One finding at moderate
confidence: dropping the timeout from 30s to 3s while adding retries=2 raises the
worst-case latency.

The code now reads

> `self.timeout = cfg.get('http.timeout', 3)`

and 3s is below the observed upstream p99 of 4.1s, per the grafana pay-p99
dashboard. High confidence on that.

Separately, prod.yaml now has

> `timeout: 3`

so the config file and the code default must not be allowed to drift; pin one of
them. Moderate confidence.

Reasoning: 3s times 3 attempts is 9 seconds worst case, against a 5 second gateway
budget. Two unknowns: the current gateway budget, and whether retries are counted
per-request. Moderate-confidence risk: the retry loop converts a timeout into a
gateway 504.

**qa -> cmd.** Taking it.

**qa -> cmd.** Verdict comment, high confidence. One finding, high confidence:
there is no test for the 409 refund path.

The diff adds

> `return {'status': 'already_refunded'}`

which is a new branch with no test covering it. High confidence.

Also, the new test asserts

> `assert len(calls) == 2`

which checks the call count but not that the second call carried the same
idem_key. Moderate confidence that this matters.

Reasoning: the coverage report at ci cov-8831 shows the 409 branch unhit. No
outstanding unknowns.

**cmd -> whoever is the human reviewer.** Verdict is block, high confidence. The
blocking items are backend's two findings — the non-idempotent retry and the
PaymentError arity change — and SRE's timeout finding. High confidence. Reasoning:
two independent blocks; QA's verdict is non-blocking. One unknown: whether the
provider dedupes on idem_key, which decides backend's finding. High-confidence
risk: merging on the QA verdict alone would ship a double-charge path.
