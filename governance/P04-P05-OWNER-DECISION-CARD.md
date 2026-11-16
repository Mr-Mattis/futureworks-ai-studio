# P04 + P05 owner acceptance card — v1

**Status:** Not approved. This is a decision aid, not an approval certificate. Baseline: November 15, 2026 development evidence on `dev/p04-remediation-p05-video`; revalidate live state, branch SHA, tests and current prices before closeout.

## First: the 3 decisions the owner actually needs to make

**A — P04 visual approval (P04-VISUAL)**. Open on the owner's PC:
`C:\Users\yashi\Documents\futureworks-p04-data\images\P04_GPU_001_CONTACT_SHEET.png`; inspect source images for visual quality, scene consistency and fit to this **synthetic fictional concept**. The sheet's presence/location must be checked. Choose APPROVE, REJECT or HOLD. APPROVE is for **exactly the ten PNG SHA hashes from run P04_GPU_001** after inspection, not later images.

**B — P04 rights/manifest (P04-RIGHTS)**. Independently review the CreativeML OpenRAIL M terms, model/source attribution and all prompts/sources for commercial use; confirm no unauthorized likeness, brand or copyrighted material is depicted or uploaded. Choose APPROVE, REJECT or HOLD with scope `synthetic proof-of-concept only` or a specifically documented commercial scope. The P01 manifest currently reads `pending_review`; a real separately authorized canonical approval and signed record are required. Do not forge or overwrite its status.

**C — P05 limited paid pilot (P05-BUDGET)**. Choose `HOLD` or expressly authorize **one** three-clip Runway Gen-4.5 test for scenes S01–S03, **5 seconds each**, with a user-specified hard USD cap and expiration date/time, after confirming account readiness and current provider pricing. Prior estimated baseline: 180 credits ~ $1.80 excluding taxes/fees. Estimate is NOT authorization. For the first test, propose **$5 USD maximum total**, but this proposal alone grants $0. Do not activate by merely merging the code. Developer credential must be stored in managed secrets, never Git/chat.

### Copy/paste owner reply

```text
P04-VISUAL=HOLD | APPROVE | REJECT
P04-RIGHTS=HOLD | APPROVE | REJECT
P04-RIGHTS-SCOPE=synthetic proof-of-concept only | other exact scope
P05-BUDGET=HOLD | APPROVE | REJECT
P05-PROVIDER=Runway
P05-MODEL=gen4.5
P05-CLIPS=3 x 5s (S01-S03)
P05-MAX-USD=0 (change only if explicitly approving)
P05-EXPIRES=YYYY-MM-DD HH:MM America/New_York
P05-CREDENTIAL-READY=YES | NO
```

Only put APPROVE after inspecting evidence. Never paste API keys, HMAC keys or credentials into ChatGPT. This message is an owner preference decision, not the cryptographic approval artifact. Future paid operations outside the exact plan require another authorization.

## Engineer-owned work — no owner clicking necessary until evidence review

| Gate | Acceptance criterion | Current evidence | Remaining task |
| --- | --- | --- | --- |
| P04-TECH | 10 real GPU PNGs, SHA provenance, canonical Visual Director handoff | Actual Comfy batch P04_GPU_001 and n8n 72/74 | Fresh checks for source hashes and same manifest |
| P04-MANIFEST | Separately approved immutable manifest | P01 state pending_review; signed verifier fail-closed | Run independent local reviewer/signature process once owner has approved exact scope |
| P04-API | Managed secret and authenticated n8n batch writer, actual approval-gated submit | Writer disabled; n8n 76 expected reject | Secret provisioning, isolated integration, receipts, no production activation |
| P04-HANDOFF | Approved images automatically available to video adapter | Ten real local references ingested to P05 planned intents | End-to-end repeat with approved manifest and explicit owner scope |
| P05-TECH | Durable request/poll/store/QC and isolated regressions | Mock contracts, n8n 75, local previews, 268 historic tests | Re-run regressions and audit real-only claims |
| P05-LIVE | Three real AI-generated clips with receipts and archived outputs | 0 paid Runway clips; 3 **FFmpeg previews only** | After budget authorization, managed key, real provider test, validate/archive |
| P05-CONTINUITY | Owner inspects 3 actual generated clips | Local frame sampling only | Show exact three real videos, ask APPROVE/REJECT/HOLD |
| P05-CLOSE | All locked exit requirements PASS and reviewed PR | P04/P05 locked exits open | Re-run technical audit; owner acceptance and separate merge |
| PROD/UPLOAD/PUBLISH | Explicit separate authorization | No authorization | Keep closed |

## Next decision after actual video generation

Once actual three provider clips are verified, stored and shown, request just:
`P05-CONTINUITY=APPROVE|REJECT|HOLD` plus notes. Show each generated clip with its source prompt, provider task receipt, hash and actual dollar cost. A missing clip or redacted playback stays HOLD. No AI likeness or publication authorization is implied.

## Safeguard

Use independent verifier with signature over exact manifest+10 hashes; default to fail closed. Rights and quality approvals require a human; licensed model documentation does not prove rights to every generated output. No paid API call, production change, upload or publication until separately approved.
