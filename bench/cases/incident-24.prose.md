<!-- DISCIPLINED prose baseline: an unusually well-behaved agent. It carries the
     same information as incident-24.rose - every confidence level, every declared
     unknown, every reference, every reply contract - and it REFERENCES prior turns
     by description rather than re-pasting them. This is prose at its best, and it
     is the harder comparison for Rosetta. -->

**a1 -> everyone.** Setting up shared terms for this incident so I do not repeat them:
CKO is the checkout service in services/checkout. A SPIKE means the 5xx rate is above
2% sustained for more than 60 seconds. Our SLO is 99.9% availability over a rolling 30
days. RB refers to the rollback runbook in runbooks/rollback.md. We are speaking
Rosetta 2.0 conventions at conformance R2c.

**a1 -> whoever holds the SRE role.** High priority. We have a SPIKE on CKO since
14:02. I need the cause, and I need the bleeding stopped. I am breaking this into four
subtasks: correlate logs and metrics, which is for observability; check recent deploys
and config, for release, and that one depends on the log correlation landing first;
check database health, for the DBA; and draft the customer statement, for comms, which
depends on the deploy check. Budget is 45 minutes. When you answer, I need the cause
identified.

**a2 -> a1.** Taking this.

**a2 -> a1.** Progress as of 14:11. The error class is an upstream timeout, not a 500
originating in CKO itself, and I am confident about that. Onset was 14:02:20, also
confident. Evidence is log 2f9c lines 440 to 512, where every failure is a 504 from the
payment upstream, and the Grafana cko-5xx dashboard for 14:00 to 14:15. Two things I do
not know: whether the upstream itself degraded, and whether the blast radius extends
beyond CKO. This is progress, not a final answer.

**a3 -> a1.** Taking the database check.

**a3 -> a1.** As of 14:14, and treat this as stale after about ten minutes: database
health is normal, no slow query above the 200ms threshold, connection pool at 34%
utilisation. I am confident in all three. Evidence is the db-overview dashboard from
13:30 to 14:15. I have no outstanding unknowns here.

**a4 -> a1.** Progress on the deploy question. Two deploys landed since 13:30: commits
9f2a and c14e. Of those, only 9f2a is a config change. Confident on both. Evidence is
CI pipeline 8817; both landed at 14:01:40. I am building on a2's log correlation. One
unknown: I do not know who approved 9f2a.

**a4 -> a1.** I have the cause, and this answers your request. Commit 9f2a lowered
http.timeout from 30s to 3s on the payment client. I am confident. Evidence: 9f2a lines
18 to 24, where the timeout is the only behavioural change, and the onset a2 reported
matches the deploy time to within 40 seconds. One moderate risk I want on record: c14e
landed at the same moment and I have not ruled it out. So the unknown is whether c14e
contributes.

**a1 -> a4.** Before we roll back, rule out c14e. I need a yes or no on whether it is
implicated. Five minutes.

**a4 -> a1.** c14e is not implicated, and I am confident. It touches only
web/static/footer.tsx, which is not on any runtime path. No remaining unknowns.

**a1 -> whoever is the human on call.** Blocking on you. Should we roll back 9f2a now?
Context is a4's cause finding, a4's c14e clearance, and the rollback runbook. Three
options: revert 9f2a, raise the timeout by config, or wait for the upstream to recover.
My recommendation, held with high confidence, is to revert 9f2a, because the config
path needs a deploy anyway and so is not actually faster. Moderate risk: reverting
reintroduces the slow query from issue 441. I do not know the current upstream p99.
Please accept or reject.

**sre1 -> a1.** Accepted. SLO burn is the larger risk right now.

**a1 -> a4.** High priority. Do this: revert 9f2a and deploy. I am committing us to it.
Fifteen minutes. Reply done or fail.

**a4 -> a1.** Taking it.

**a4 -> a1.** Progress as of 14:31: build is green, canary at 5%. Confident. Unknown:
whether 5% gives us enough signal to judge.

**a4 -> a1.** Done, as of 14:39. Reverted 9f2a, deployed aa71. Confident in both.
Evidence is CI pipeline 8823. Still unknown: the error rate after full rollout, since it
is still rolling.

**a2 -> a1.** Progress at 14:47. Error rate is 0.4% and falling, and I am confident in
that reading. Evidence is the cko-5xx dashboard from 14:35 to 14:47. Unknown: whether it
settles below the SPIKE threshold.

**a2 -> a1.** At 15:02: error rate 0.08%, and we have recovered. Confident on both.
Evidence is the cko-5xx dashboard from 14:47 to 15:02, fifteen minutes below the SLO
baseline. No outstanding unknowns.

**a1 -> everyone.** Correcting my earlier recommendation. It is not simply revert-only,
and I am confident about that correction. This conflicts with what I said before: a2's
recovery reading is confirmed, but the 3s timeout was arguably correct and the old 30s
was masking upstream latency all along. What I do not know is what the timeout should
actually be.

**a5 -> a1.** Draft customer statement, version 1:

> Between 14:02 and 14:47 UTC a subset of checkout requests failed.
> The cause was a configuration change to a payment timeout, which we
> have reverted. No orders were lost; affected customers saw an error
> at payment and could retry.

One unknown: whether legal wants us to use the word "outage".

**a1 -> a5.** Two changes to your draft. On line 3, the phrase "No orders were lost" -
we have not verified that yet, and I am confident we have not. On line 1, "a subset of"
should become "Approximately 12% of", though I hold that one at moderate confidence.
Reasoning: a2's log correlation gives us the failure share, but the order claim needs
the DBA to confirm. Unknown: the exact affected order count. Please accept or reject -
and note these are proposals, the draft is yours to change.

**a5 -> a1.** Accepted. I will hold the statement until the order count lands.

**a1 -> whoever holds the SRE role.** Incident summary, for the record. Cause was commit
9f2a; fix was commit aa71; recovered at 14:47; total duration 45 minutes. I am confident
in all four. The full chain is in this incident thread; the key messages are a4's cause
finding, a4's deploy completion, and a2's recovery confirmation. Two things remain
unknown: the correct long-term timeout value, and the exact affected order count. And
one risk I want stated with high confidence: the underlying upstream latency is still
unaddressed.
