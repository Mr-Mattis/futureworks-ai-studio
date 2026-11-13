# Future Works AI Studio — Master Project Completion Checklist

VERSION 1.0 • CONTINUED • NOVEMBER 9, 2026

Source: complete checklist supplied by the owner in this chat. This operational transcription preserves the checkpoint requirements, locked stack, sequence and exit gates. Decorative images and their links are omitted. Checkpoint suffixes identify each bullet in its original order; they add no requirements. Verified progress is tracked separately in PROGRESS.md rather than changing the supplied baseline.

Single source of truth: follow phases sequentially, validate each milestone, document changes, and introduce no unrelated work. Objective: an automated content-production studio delivering editable YouTube episodes for final creative approval.

## Supplied baseline

12 / 101; 12%. Checkpoint-based, not estimated time remaining. Later tests may reopen prior items.

| Phase | Established / total |
| --- | --- |
| P00 Infrastructure | 6/7 |
| P01 Contracts and data | 0/7 |
| P02 Ten local agents | 1/10 |
| P03 Orchestration | 0/8 |
| P04 Local images | 0/6 |
| P05 AI video | 0/7 |
| P06 Avatar and voice | 0/8 |
| P07 Audio and captions | 0/6 |
| P08 Assembly and Resolve | 3/9 |
| P09 QC and approval | 1/8 |
| P10 Publishing and analytics | 0/8 |
| P11 Operations | 1/7 |
| P12 Final acceptance | 0/10 |

## P00 — Existing infrastructure baseline

- P00.01 WSL/Ubuntu development environment configured.
- P00.02 n8n and Python production worker deployed through Docker.
- P00.03 Ollama model reachable from the n8n Docker container.
- P00.04 Creative Director demonstrated local model inference and structured script generation.
- P00.05 Python worker successfully completed a dry-run production job.
- P00.06 DaVinci Resolve successfully imported an editable generated timeline.
- P00.07 Capture a fresh backup of the live n8n configuration, workflow JSON files, data tables and Python worker before further development.

Exit gate: Backup verified and existing production workflow preserved. No modifications to the working production webhook.

## P01 — Production contracts and data architecture

- P01.01 Define canonical production_manifest.json: project metadata, content classification, episode title, narration, scene IDs, image/video prompts, output format and durations.
- P01.02 Define agent_result.json: agent role, input manifest version, output payload, validation status and error details.
- P01.03 Establish job state transitions: draft → research → scripted → planned → approved → generating → assembling → qa → ready_for_edit → published.
- P01.04 Create persistent n8n data tables for production jobs, scene assets, provider jobs, costs, approvals and error records.
- P01.05 Implement schema validation and immutable revision IDs so later agents cannot silently overwrite an approved script.
- P01.06 Define idempotency rules, retry limits, timeouts and recovery procedures for interrupted AI-generation jobs.
- P01.07 Test a dummy production manifest through every data-validation gate without calling paid APIs.

Exit gate: One test manifest can pass through the system, retain its identifiers, survive an interrupted operation, and resume without duplicate jobs or expenses.

## P02 — Complete the ten local production agents

Each agent uses an n8n workflow with Ollama Chat Model, role instructions, structured-output validation and handoff rules. Existing standalone FWAI-DEV drafts remain specification/reference until local counterparts pass functional tests.

- P02.01 Executive Producer: delegates production stages and evaluates blockers.
- P02.02 Creative Director: writes scripts and scene manifests; existing Ollama version working.
- P02.03 Research Agent: checks claims and identifies technical limitations.
- P02.04 Visual Director: creates shot plans and continuity-controlled prompts.
- P02.05 Avatar Director: plans approved likeness, wardrobe and presenter segments.
- P02.06 Budget Controller: forecasts costs; hard caps enforced outside the agent.
- P02.07 Editing Supervisor: reviews timeline structure and suggests targeted changes.
- P02.08 Quality Control: audits completeness, accuracy and defects.
- P02.09 Growth Strategist: analyzes actual publishing performance.
- P02.10 SOP & Knowledge: drafts documentation changes for approval.

Exit gate: All ten roles have saved workflows and pass controlled role-specific tests using Ollama. No agent can invoke external paid tools or publish without an explicit gate.

## P03 — Master production orchestration

- P03.01 Create FWAI-LOCAL — Master Production Orchestrator.
- P03.02 Implement creative-brief intake through an n8n form/webhook.
- P03.03 Route tasks from Executive Producer to Research, Creative, Visual, Avatar and Budget agents.
- P03.04 Enforce output schemas and dependencies between agents.
- P03.05 Add parallel execution for independent tasks and sequential execution where prerequisites exist.
- P03.06 Add approval checkpoints before rendering, additional spending and publishing.
- P03.07 Implement asynchronous provider-job polling, retries, failure queues and recovery.
- P03.08 Generate a dashboard/report showing stage status, costs, asset readiness and outstanding issues.

Exit gate: One concept passes through all planning agents, creates a validated production plan, and stops at the correct approval gate without manual node execution.

Locked design: Production Brief → Master Orchestrator → Executive Producer (coordinates Research, Creative Director, Visual Director, Avatar Director, Budget Controller and QC) → Human Approval + Budget Gate → Media Generation Services → Python / FFmpeg / OpenTimelineIO → Editing Supervisor + QC → DaVinci Resolve, ready for human edit.

## P04 — Local AI image generation

Objective: Reference images, thumbnails, engineering concepts, environments and consistent characters without paid image APIs. Primary engine: ComfyUI. Benchmark Radeon RX 9070 XT; backend/model compatibility tested before locking the model.

- P04.01 Install ComfyUI with compatible AMD GPU backend; verify GPU acceleration.
- P04.02 Select and license-check models for photorealism, machinery and technical concept art.
- P04.03 Establish reusable thumbnail, establishing-shot, mechanical close-up and material-texture templates.
- P04.04 Create an n8n ComfyUI API adapter and asynchronous job monitoring.
- P04.05 Save images with prompts, seeds, model versions, project IDs and reference relationships.
- P04.06 Verify ten images generated, downloaded, indexed and passed to Visual Director without manual transfers.

Exit gate: An approved manifest automatically produces consistent reference images available to video-generation workflows.

## P05 — Cinematic AI video generation

Objective: Coherent clips from scene plans and approved reference images. Primary engine: Runway Dev API behind a replaceable provider adapter, not embedded throughout the studio.

- P05.01 Establish developer account, API credentials and spending limits.
- P05.02 Implement text-to-video and image-to-video using supported models and current API schema.
- P05.03 Create reusable scene-generation templates for channel categories.
- P05.04 Build polling, timeouts, throttling and bounded retries.
- P05.05 Download clips to permanent project storage before temporary URLs expire.
- P05.06 Add visual continuity review, reference-frame matching and correction requests.
- P05.07 Complete a three-scene cinematic test within an explicitly approved budget.

Exit gate: One approved manifest generates three usable clips with recorded costs, source prompts and preserved assets.

## P06 — Digital avatar and cloned voice

Objective: Reusable real likeness and voice with consistent presenter identity. HeyGen: presenter video and synchronized speech. ElevenLabs: narration and controlled consistent voice generation.

- P06.01 Finalize approved facial-reference photo set and presenter styling.
- P06.02 Create and verify HeyGen digital avatar using required consent process.
- P06.03 Record, create and approve cloned voice using consented recordings.
- P06.04 Establish versioned identity profile with approved identifiers, wardrobe and presentation rules.
- P06.05 Connect HeyGen to n8n for presenter generation and status retrieval.
- P06.06 Connect ElevenLabs to n8n for narration, downloads and timing metadata.
- P06.07 Implement speech, appearance, pronunciation and lip-sync consistency checks.
- P06.08 Render and approve one 20–30-second presenter segment with owner likeness and cloned voice.

Exit gate: A script automatically produces a short identity-consistent presenter segment and separate narration file, approved by the owner.

Never combine separate narration with an avatar clip containing spoken audio without deliberately muting or replacing one source; prevent double narration and sync problems.

## P07 — Sound design, music and captions

Objective: Complete legally usable audio package.

- P07.01 Connect selected sound-effects generation service and job retrieval.
- P07.02 Establish licensed music library and commercial rights for each track.
- P07.03 Create profiles for futuristic technology, RC, plasterwork, painting and vinyl tutorials.
- P07.04 Generate word/sentence timestamps with local transcription/alignment.
- P07.05 Implement FFmpeg loudness normalization, dialogue ducking, fades and peak limiting.
- P07.06 Generate and validate synchronized SRT captions.

Exit gate: Test video receives synchronized narration, approved music, sound effects and captions without clipping, duplicate dialogue or missing licenses.

## P08 — Automated assembly and DaVinci Resolve handoff

Build on existing Python worker and editing pipeline.

- P08.01 Python/FFmpeg rough-cut assembly implemented.
- P08.02 OpenTimelineIO source and packaged export generated.
- P08.03 Initial generated timeline successfully imported into Resolve.
- P08.04 Extend worker to canonical multi-scene manifest rather than simplified dry-run request.
- P08.05 Assemble AI footage, stills, avatar, narration, music, captions and brand intro into separate tracks.
- P08.06 Preserve organized original media, shot IDs and source metadata.
- P08.07 Implement timeline timing, transitions, scene-order corrections and missing-asset handling.
- P08.08 Export and verify complete 1080p package with editable tracks and rough-cut MP4.
- P08.09 Validate actual multi-provider episode in Resolve, including relinking, trimming, playback and export.

Exit gate: Multi-service episode opens in Resolve as an editable project without manual assembly or missing media.

Production package layout:

```
FWAI-EPISODE-ID/
├── 01_Brief/
├── 02_Research_and_Scripts/
├── 03_Images/
├── 04_Generated_Video/
├── 05_Avatar/
├── 06_Voice_and_Audio/
├── 07_Timeline/
│   ├── FutureWorks_Edit.otio
│   └── FutureWorks_Edit.otioz
├── 08_Rough_Cut/
├── 09_Thumbnails_and_Metadata/
├── 10_QC_and_Approvals/
└── production_manifest.json
```

## P09 — Quality control and human approval

Objective: Prevent incomplete, misleading, technically defective or over-budget videos reaching publication.

- P09.01 Script validation and human review established in Creative Director workflow.
- P09.02 Extend approval records across production lifecycle.
- P09.03 Validate asset completeness, formats, frame rates, resolutions and durations.
- P09.04 Review visual consistency, missing frames, artifacts and continuity.
- P09.05 Check narration alignment, captions, audio levels and missing sound.
- P09.06 Audit technical claims, fiction labels, asset rights and applicable YouTube disclosures.
- P09.07 Add targeted regeneration with bounded retries and spending authorization.
- P09.08 Produce final QC report and require owner approval before release.

Exit gate: Deliberate defects detected or flagged for human review; no unapproved/failed project advances to publication.

## P10 — YouTube publishing and analytics

- P10.01 Finalize metadata, standard descriptions, content categories and upload defaults.
- P10.02 Create and approve reusable animated intro, outro and branding assets.
- P10.03 Build metadata and thumbnail templates.
- P10.04 Configure least-required YouTube API permissions.
- P10.05 Implement private/unlisted staging uploads for controlled tests.
- P10.06 Add final owner-controlled publishing approval gate.
- P10.07 Connect YouTube Analytics and approved reports to Growth Strategist.
- P10.08 Validate one authorized upload, reporting cycle and generated performance summary.

Exit gate: Successful permitted-visibility staging upload, correct metadata and retrievable performance metrics. Public release remains owner's decision.

## P11 — SOP library, backups and operating procedures

- P11.01 Initial PDF production SOP library and publishing roadmap created.
- P11.02 Document installation/configuration of every service.
- P11.03 Create version-controlled architecture index of workflows, agent IDs, schemas and integrations.
- P11.04 Document production SOP including manual intervention and approval procedures.
- P11.05 Establish automatic backups of n8n configuration, database, workflows, scripts and media manifests.
- P11.06 Test restoration of critical components.
- P11.07 Create startup/shutdown procedures starting WSL, Docker, Ollama and MCP tunnel only when studio intentionally launched.

Exit gate: Studio can stop, restart and recover without losing configuration/history. Automatic tunnel at Windows login intentionally deferred and not a production blocker.

## P12 — Final end-to-end production acceptance test

Use one original episode, not synthetic placeholder scenes.

- P12.01 Submit concept only through dashboard/intake form.
- P12.02 Run required production agents and verify handoffs.
- P12.03 Produce original, fully researched structured script.
- P12.04 Generate approved images, clips, avatar, cloned narration and sound effects.
- P12.05 Verify spending controls, logs and successful failure recovery.
- P12.06 Automatically assemble complete rough cut with branding, captions and metadata.
- P12.07 Pass technical, creative and disclosure QC.
- P12.08 Deliver and open editable package in Resolve.
- P12.09 Complete human-approved staging upload and verify metadata.
- P12.10 Save complete production record, SOP revision and performance baseline.

Final acceptance: One brief leads through automated production without routine manual intervention to a coherent editable fully sourced video package for creative review. Paid generation, identity use and publishing obey configured approvals.

## Locked build execution order

1. Back up/protect V1 infrastructure (P00).
2. Contracts and persistent records (P01).
3. Ten individually tested Ollama agents (P02).
4. Master orchestrator and approval gates (P03).
5. Local images, then video, avatar, voice, sound (P04–P07).
6. Expanded assembly and Resolve (P08).
7. Full QA, publishing, analytics and operations (P09–P11).
8. Final production acceptance (P12).

## Governance

1. No skipped phases; satisfy exit criteria. Record narrowly scoped dependency fixes, not new initiatives.
2. No silent substitutions. Locked stack, architecture, schema or objective changes require a versioned checklist amendment and owner approval.
3. Preserve infrastructure. Develop in FWAI-DEV/FWAI-LOCAL; update production only after regression tests and verified backup.
4. Control costs. Ollama for local reasoning; ComfyUI first image target; paid services have budgets, retry limits and gates. Credentials alone do not prove operation.
5. Evidence for completion. Nodes, prompts and saved credentials alone do not establish integration.

Original baseline closing instruction: Begin P00.07 — Production backup. This remains historical baseline text; current verified status is maintained separately.
