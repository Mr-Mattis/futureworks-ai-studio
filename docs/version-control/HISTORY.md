# Evidence-based development history

Recorded during version-control setup on November 13, 2026 (America/New_York).
This is a retrospective index, not historical Git commits. Dates below come from
record contents or the backup identifier, not filesystem modification times.
UTC is retained where the evidence supplies a timestamp; early November 10 UTC
falls on November 9 in New York. Historical test results were not rerun here.

| Evidence date | Milestone and scope | Evidence |
| --- | --- | --- |
| November 9, 2026 (document date) | Owner baseline: infrastructure 6/7, local Creative Director work, rough-cut/OTIO/Resolve foundation, script review and initial SOP work. These are recorded baseline claims, not newly verified production behavior. | `governance/MASTER-CHECKLIST-v1.0.md` |
| 2026-11-10 04:15:43 UTC (backup identifier) | P00.07 backup: source snapshot, four workflow exports, saved n8n database and private configuration. Backup stays outside Git. | sibling `backups/P00.07-20261110T041543Z`; P01.02 checkpoint |
| Before P01.02 verification; exact completion time unavailable | P01.01 canonical production manifest, schema and validation. | `contracts/production-manifest/v1.0.0/`; P01.02 prerequisite record |
| 2026-11-10 04:38:12 UTC | P01.02 agent-result contract; ten roles and ten test methods reported passing. Production agent adoption not established. | `contracts/agent-result/v1.0.0/installation-verification.json` and checkpoint |
| 2026-11-10 04:49:49 UTC | P01.03 job-state contract; 12 test methods and all 100 state pairs reported checked. | `contracts/job-state/v1.0.0/installation-verification.json` and checkpoint |
| 2026-11-10 04:55:16 UTC | P01.04 six persistent tables, synthetic roundtrips and seven offline evidence tests reported passing. | `contracts/data-tables/v1.0.0/installation-verification.json` and checkpoint |
| 2026-11-10 05:05:21 UTC | P01.05 guarded immutable revisions, row validation and 15 tests. Direct administrative writes and production agent adoption remain outside this guarantee. | `contracts/revision-guard/v1.0.0/installation-verification.json` and checkpoint |
| 2026-11-10 05:23:47 UTC | P01.06 recovery policy/reference code, 17 tests and synthetic interruption/reconciliation. No real provider idempotency guarantee. | `contracts/recovery-policy/v1.0.0/installation-verification.json` and checkpoint |
| 2026-11-10 05:55:00 UTC | Initial P01.07 evidence: 28 positive checks, 25 rejections and synthetic recovery. Initial exit-gate conclusion was subsequently corrected as too broad. | `contracts/full-data-gate/v1.0.0/installation-verification.json`; `governance/P01-GATE-CORRECTION.md` |
| November 10, 2026 (addendum date; exact final time not established) | Follow-up executions 19–23 documented connected synthetic readback/restart, canonical guard rejection, persisted draft-to-research transition, and removal of the temporary bridge. Controlled P01 exit gate complete; production orchestration remains unproved. | `governance/P01-CONNECTED-TEST/CHECKPOINT-ADDENDUM.md`, `connected-run-evidence.json`, correction and progress records |
| November 13, 2026 | Establish current source baseline and retrospective index; no production checkpoint advanced. | This document and the first Git commit |

## Historical snapshot decision

The November 10 source archive was readable and its checksum matched. All 12
non-environment regular-file members matched the corresponding current files
before this setup. It contains the starter pipeline, not intermediate P01
snapshots. The environment-template member was excluded from versioning.
The archive remains intact outside Git. No commits or commit dates were backdated;
no intermediate development sequence was invented. Discovery was scoped to the
project, its sibling backup directory, and the referenced conversation.

## Remaining backlog and evidence limits

- `governance/PROGRESS.md` names P02.01 Executive Producer as the next sequential checkpoint. It remains pending; this Git setup grants no phase advancement.
- Preserve the locked P00–P12 sequence and acceptance gates in the master checklist. Later phases cover production agent adoption, orchestration, media generation, assembly, QC, publishing and operations.
- Permanent guard access, authenticated approvals, concurrent-writer enforcement and real provider recovery semantics remain to be integrated/tested.
- The preserved checklist headline says 101 while phase denominators total 111. Progress records identify 20 established/verified checkpoints. No denominator or locked requirement was changed here.
- The addendum references `adapter-before.json`, which is absent from the inspected connected-test directory. Preserve this evidence gap; do not invent the missing artifact.
- The referenced November 13 audit conversation reports a status-helper/webhook mismatch and incomplete live prerequisite checks. Those reports were not resolved or retested by version-control setup.
- Some source/test files and historical installation evidence contain absolute WSL paths. They were preserved byte-for-byte; portability is not established. Runtime data itself is excluded.
