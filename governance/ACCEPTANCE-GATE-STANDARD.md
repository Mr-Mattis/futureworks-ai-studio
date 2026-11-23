# Future Works AI Studio — reusable phase acceptance standard (v1)

Purpose: make the owner's decision small and auditable while keeping technical evidence, spending, rights and deployment approvals separate. This document does not amend MASTER-CHECKLIST-v1.0 and grants no authority.

## Universal protocol for P04, P05 and every later phase

1. Engineer generates an **evidence packet**: locked requirement, exact run/manifest/asset SHA IDs, branch/commit, automated tests, real-vs-mock disclosure, money spent, outstanding blockers, security scan, rollback and evidence links. Each claim must be marked PASS, FAIL, NOT_RUN or NOT_APPLICABLE; never silently infer PASS.
2. Engineer supplies a short **decision card** with independently reviewable selections. The owner can answer in one message using exact gate IDs, e.g. `P04-VISUAL=APPROVE; P04-RIGHTS=HOLD`. `APPROVE` applies only to its explicitly named subject and reviewed asset versions, never to future generations.
3. **No self-attestation:** human visual/continuity/rights approvals require actual owner viewing and a recorded decision; technical receipt validation does not replace them. The local signer's key must be outside Git and logs. A signed authorization must bind reviewed manifest hash, asset hashes, scope, reviewer, timestamp and expiry; the independent verifier must validate it.
4. **Budget authority is separate:** every paid test requires a clearly defined provider, model, specific operations, maximum aggregate USD spend inclusive of contingency, expiry and zero-automatic-retry policy. Default budget is $0. No stored API credential means a gate stays blocked. No blanket 'approve P05' may cause charges.
5. **Production authority is separate:** approving development/visuals/budget never activates workflows, deploys services, publishes video or approves likeness. Require new explicit gates for each.
6. Automated gate runner evaluates prerequisites deterministically; any missing evidence, failed test, mismatched SHA, stale approval, expired limit, unexpected provider request or unclear rights result is HOLD, not PASS. Stage completion requires every locked exit condition, not a majority vote.
7. Store an append-only acceptance decision record (not private secrets) referencing artifact SHA, branch/commit, reviewer, scope, evidence and decision. For each future phase, copy the same card template, fill phase-specific locked requirements and only ask the owner to rule on genuinely human decisions.
8. After owner review, run a fresh isolated regression and scoped real-world acceptance test, upload redacted receipts and cost ledger, and open a reviewable PR. Source control merge is a separate explicitly authorized step. Do not mark CLOSED until the exit matrix is all PASS.

## Future gate template

| Gate | Owner decision | Objective evidence | Status |
| --- | --- | --- | --- |
| PX-TECH | None when automated | Tests, immutable manifest, provenance, receipts, fail-closed checks | NOT_RUN |
| PX-VISUAL | Approve/reject exact assets | Contact sheet, full-resolution samples, continuity notes | HOLD |
| PX-RIGHTS | Confirm documented rights/consents | Model/source licenses, likeness permissions, use scope | HOLD |
| PX-BUDGET | Explicit cap/provider/expiry | Estimate, credentials held securely, kill switch, cost tracking | HOLD |
| PX-LIVE | Separate approval for scoped external test | Redacted real-provider request/response and archive receipt | HOLD |
| PX-PROD | Separate deployment/publication approval | Rollback plan, release checklist, signed publishing rights | HOLD |

Owner replies: `GATE_ID=APPROVE`, `GATE_ID=REJECT`, or `GATE_ID=HOLD`, with required scope fields. An engineer must not interpret silence, a PR merge, approval of source code, or positive feedback as a production/spending/rights grant.

An acceptance decision is **not** a cryptographic signature. The existing P04 HMAC verifier must still be fed independently generated, correctly scoped signed evidence by the approved local reviewer flow; never commit HMAC secrets or mark pending_review as approved to satisfy tests.
