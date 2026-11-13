# P01.07 completion evidence

Requirement: Test a dummy production manifest through every data-validation gate without paid APIs.

One existing immutable test manifest, project FWAI-P0105-LIVE-TEST revision 1, passed the P01.01 manifest validator, P01.02 ten-agent result envelopes, P01.03 nine lifecycle gates with synthetic in-memory receipts, P01.04 all six live n8n tables, P01.05 revision/row guard and P01.06 restart/reconciliation policy. Exact project ID, job ID, revision and SHA-256 stayed bound throughout.

Result: 28 positive checks passed; 25 deliberate invalid inputs rejected. Live records were read back exactly; prior rows were unchanged. The process crash exited with code 17 and recovered an existing mock provider job. Across recovery and a repeat restart there was one synthetic submission, one zero-amount billing event and zero real expense. No real provider or model was called; no approval was granted and no content was published.

Live changes: five clearly marked test child rows in provider_jobs, scene_assets, costs, approvals and errors. Existing production_jobs test row reused. No production workflow or existing archive row changed. The live job remains draft, approval pending and provider unsubmitted. Four workflows and seven tables were reachable at final verification, closing the P01.06 tunnel inventory gap.

Evidence: gate-report.json, live-readback.json, five candidate-row JSON files, test-context.json, production-preservation.json, test-results.txt, installation-verification.json, SHA256SUMS. README.md explains the controlled test limits.

Status: P01.07 complete once installation verification passes. P01 is 7/7 at the data-architecture exit gate: the dummy manifest retained identifiers and survived a simulated interrupted operation without a duplicate mock job or charge. Production orchestration, real provider semantics and live agent integration remain later phases. Stop before P02 and ask the owner whether to continue.
