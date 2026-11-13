# FutureWorks AI Studio — First Working Pipeline

**Goal:** one prompt on Windows -> n8n -> local Python job worker -> optional AI APIs -> FFmpeg MP4 and OpenTimelineIO `.otioz` edit package in a Windows folder -> manual edit in DaVinci Resolve.

**Status:** Dry-run production code and its actual FFmpeg outputs were tested in the author's build environment. We could not run Docker/n8n or DaVinci Resolve in that environment; **n8n imported workflow and Resolve `.otioz` compatibility must still be validated on your machine**. Paid API calls cannot be tested without your credentials.

## What works in the starter

- `dry_run` (default): generates a placeholder avatar, scene clips, **silent audio tracks**, a script/shot plan, a rough-cut MP4 and a `.otioz` with separate video/audio tracks. It DOES NOT create your likeness or synthetic narration.
- `live`: calls an LLM for shot scripts, HeyGen v3 for the talking intro, Runway Gen-4.5 for scene videos, ElevenLabs for voiceovers, then makes a rough cut and timeline. The live path has been implemented based on the providers' documented API shapes, **but remains untested until you connect paid accounts and trial it**.
- n8n handles submission and status lookup, while the separate Python worker performs long-running jobs. The worker runs one production at a time, persists job state, and refuses to auto-resubmit an interrupted paid task on restart.
- Status endpoint returns `queued`, `running`, `completed`, `failed`, or `needs_review`.

**Limits:** This is a starter production pipeline, not a finished 8-minute automatic film studio. It makes 1–4 scenes (5 or 10 seconds each), plus an avatar intro. Longer videos, parallel shots, retries, automated quality scoring, captions, reusable intro, and true remote dashboard are Phase 2. Current cap controls only Runway *scene* generation; other providers have independent charges. Copyright and AI disclosure require a human check.

## 1. Create your accounts (no API keys in chat!)

1. https://heygen.com — create a **Digital Twin** from your own face, follow their current consent recording process, and create or assign a clone of your own voice. Test a talking 5–10-second video in the web interface.
2. https://developers.heygen.com/generate-avatar-video — view API v3 docs. In your HeyGen API workspace create a key, then obtain a private look `id` from `GET https://api.heygen.com/v3/avatars/looks?avatar_type=digital_twin&ownership=private`. The `id` goes in `HEYGEN_AVATAR_ID`. Get a usable voice ID from `GET https://api.heygen.com/v3/voices` and put it in `HEYGEN_VOICE_ID`. Make sure your API plan supports the selected avatar and video engine.
3. https://elevenlabs.io — create an **Instant Voice Clone** using a clean sample of your voice (the service recommends 1–2 minutes), test the result and copy its voice ID. Create a scoped API key and confirm TTS usage/credit entitlement. You may later unify the HeyGen and narration voices for closer consistency.
4. https://dev.runway.com and https://docs.dev.runwayml.com/ — create an **API developer account**, API key and controlled credit balance. Studio subscription credits do not automatically equal API credits.
5. Your preferred LLM API account — this starter uses OpenAI's Chat Completions-compatible endpoint. Use an OpenAI API key with a spending limit and ensure your configured model has access. This is separate billing from ChatGPT subscriptions.
6. Install DaVinci Resolve 21 (or a version supporting OTIO import) from https://www.blackmagicdesign.com/products/davinciresolve . Use a new project for the test.

## 2. Record your avatar and voice (Phase 1)

- Avatar footage: face clearly visible, steady camera, clear lighting, neutral background, clothing matching your channel identity, natural speech and natural gestures. Follow HeyGen's up-to-date recording instructions rather than assuming one specific footage length.
- Consent: read and submit the consent statement given by HeyGen. Never substitute an image or another person's consent.
- Voice: record around 1–2 minutes with a quiet microphone at consistent distance; no music, compression artifacts or other speakers. Save the raw reference offline.
- Test three short scripts containing technical words like *Venetian plaster*, *GPU heatsink*, *servo motor*. Fix pronunciation and consistency before paying for batches.
- Keep reference recordings and API keys private. Only clone yourself or someone who explicitly consented.

## 3. Windows + WSL + Docker Desktop setup

**Assumption:** Windows 11, WSL Ubuntu installed, and Docker Desktop using the WSL 2 backend.

A. Download and unzip the project ZIP on Windows into `C:\Users\YOUR_WINDOWS_USERNAME\Downloads\futureworks-ai-studio`.

B. Install **Docker Desktop for Windows**, then open Settings -> Resources -> WSL Integration -> enable Ubuntu. Start Docker Desktop.

C. Open Ubuntu/WSL and enter these commands, **one command per line**. Replace `YOUR_WINDOWS_USERNAME` with your real Windows home-folder name (not necessarily your display name):

```bash
mkdir -p ~/futureworks-studio
cp -a /mnt/c/Users/YOUR_WINDOWS_USERNAME/Downloads/futureworks-ai-studio/. ~/futureworks-studio/
cd ~/futureworks-studio
cp .env.example .env
mkdir -p /mnt/c/Users/YOUR_WINDOWS_USERNAME/Videos/FutureWorks
openssl rand -hex 32
```

D. Edit your `.env` in VS Code **from WSL** (execute `code .` in the WSL terminal), or use `nano .env`. Set:

- `OUTPUT_DIR=/mnt/c/Users/YOUR_WINDOWS_USERNAME/Videos/FutureWorks` (replace placeholder, use no quotes).
- `N8N_ENCRYPTION_KEY=` followed by the 64-character random hex string printed by `openssl rand -hex 32`.
- Leave `ENABLE_PAID_GENERATION=false` and all API keys blank until the dry-run test passes.

E. Start the production system:

```bash
cd ~/futureworks-studio
docker compose up -d --build
docker compose ps
docker compose logs --tail=30 worker
```

Visit **http://localhost:5678** on the Windows PC, create your n8n owner account and secure the account. n8n and the worker run in Docker containers; only n8n is reachable from the Windows host and it is bound to **127.0.0.1**. Do **not** port-forward this service to the public internet.

## 4. Import the n8n workflow

1. In n8n, choose **Add Workflow** -> menu `...` -> **Import from File**.
2. Select `workflows/futureworks-n8n-workflow.json` from the downloaded Windows project folder.
3. Confirm the two flows show:
   - `Submit production brief` -> `Queue production job`.
   - `Check job status` -> `Fetch job status`.
4. In the **Queue production job** HTTP Request node verify:
   - Method: `POST`.
   - URL: `http://worker:8000/jobs`.
   - Send Body: enabled, JSON body in **Expression** mode: `{{ JSON.stringify($json.body) }}`.
5. In **Fetch job status**, verify URL Expression: `{{ 'http://worker:8000/jobs/' + $json.params.job_id }}`.
6. Save and **publish/activate** the workflow. Production endpoints do not run until published. New n8n versions may label this control differently.

Because the workflow is local-only, both webhook URLs begin with `http://localhost:5678/webhook/...`.

## 5. Submit your first production job

Open **Windows PowerShell**, navigate to the extracted project (not the WSL copy):

```powershell
cd "$env:USERPROFILE\Downloads\futureworks-ai-studio"
.\submit.ps1
```

Paste this prompt when it asks:

> A cinematic AI concept video showing a custom desktop computer transforming into a futuristic mechanical robot inside an industrial design lab.

Choose **D** for Dry Run, **2** scenes, budget **3**. The script will print a job ID.

Check it later:

```powershell
.\status.ps1 -JobId PASTE_YOUR_JOB_ID_HERE
```

**Only replace** `PASTE_YOUR_JOB_ID_HERE` with the actual 12-character job ID; do not paste the words themselves.

If Windows blocks PowerShell execution, don't change global execution policy. Instead start from PowerShell with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\submit.ps1
```

Or call the n8n local webhook using `curl` in your WSL shell:

```bash
curl -sS http://localhost:5678/webhook/futureworks/produce \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"A futuristic computer transforms into a robot in a workshop","mode":"dry_run","scene_count":2,"scene_duration":5,"runway_budget_usd":3}'
```

## 6. Open your generated edit in DaVinci Resolve

1. On Windows, go to `C:\Users\YOUR_WINDOWS_USERNAME\Videos\FutureWorks`.
2. Open the new 12-character job ID folder.
3. Preview `06_Rough_Cut\rough_cut.mp4` (in dry mode, you'll see titles and hear silence by design).
4. Open DaVinci Resolve. Create a new project. In the Media or Edit workspace, use **File -> Import -> Timeline**, then select `05_Editing\FutureWorks_Edit.otioz`.
5. Resolve should unpack the `.otioz` and reconstruct a **Video 1** track and **Audio 1** track. In Resolve's OTIO import options, review frame rate (24 fps) and media linking. If the imported timeline shows media offline, check the extracted `media` directory and relink manually.
6. Make your changes, save the native DaVinci Resolve project, and use Deliver for your final upload render.

If your installed Resolve build cannot import the package, keep the MP4 and individual media files as a fallback. This package has been structurally verified but not opened in Resolve in our build environment.

## 7. Activate **paid** live generation (only after dry-run)

In `~/futureworks-studio/.env`, set:

```ini
ENABLE_PAID_GENERATION=true
OPENAI_API_KEY=YOUR_ACTUAL_API_KEY
RUNWAYML_API_SECRET=YOUR_ACTUAL_RUNWAY_API_KEY
HEYGEN_API_KEY=YOUR_ACTUAL_HEYGEN_KEY
HEYGEN_AVATAR_ID=YOUR_OWN_DIGITAL_TWIN_LOOK_ID
HEYGEN_VOICE_ID=YOUR_OWN_HEYGEN_VOICE_ID
ELEVENLABS_API_KEY=YOUR_ACTUAL_ELEVENLABS_API_KEY
ELEVENLABS_VOICE_ID=YOUR_OWN_ELEVENLABS_VOICE_ID
```

Do **not** include the strings `YOUR_...` literally; replace with values from the corresponding account. **Never share the `.env` file, or commit it to GitHub.**

Restart the two services to load updated environment variables:

```bash
cd ~/futureworks-studio
docker compose up -d --force-recreate
docker compose logs --tail=30 worker
```

Submit a **single** live scene first, not a complete episode. A scene is billed by the providers even if the user dislikes the result. The `runway_budget_usd` field caps **estimated Runway clip charges only**, not your entire bill. Do not leave a live job running if you cannot afford any provider charges outside that cap. The program intentionally does not auto-retry an interrupted paid task.

## 8. Operation, troubleshooting, and security

```bash
# Show status
docker compose ps
# Worker logs
docker compose logs --tail=100 worker
# n8n logs
docker compose logs --tail=100 n8n
# Restart after Docker Desktop/Windows reboot
docker compose up -d
# Stop services
docker compose down
```

- Your **Windows computer must remain powered on and connected** for this local version to finish jobs while you're away. Do not let it sleep during generation. Cloud hosting + file synchronization is a later upgrade.
- Keep the n8n app available only on `localhost`. If you later need phone/remote access, use an authenticated private VPN or access proxy, NOT an open public webhook.
- This is a single-worker queue. If a container crashes mid-paid generation, job status becomes `needs_review` rather than automatically re-running and potentially charging twice.
- Provider output links expire. The worker downloads outputs immediately after completion and stores originals locally.
- `job.json` records the current stage and output locations. Folder contents are your recovery path.
- For production, pin your n8n Docker image to a tested specific version, back up the volume and project output, and use a proper database/job-queue as volume scales. `latest` is only suitable for this local starter.
- Keep realistic AI scenes disclosed as needed under YouTube's altered/synthetic content rules. Final uploading is manual in V1.

### Known V1 limitations and planned V2 upgrades

**Not yet implemented:** remote job submission, authenticated remote webhooks, provider-specific error normalization, real cost accounting across all providers, checking actual footage content for anomalies, in-scene avatar composites, subtitles, soundtrack licenses, scene continuity, output quality scoring, native Resolve `.drp` project creation, full YouTube-length narratives, prompt asset library, and direct YouTube upload. We should add these in that order, after the end-to-end handoff works.

### Verified sources

- HeyGen v3 Digital Twin: https://developers.heygen.com/generate-avatar-video
- HeyGen consent: https://help.heygen.com/en/articles/12092609-recording-your-consent-video
- ElevenLabs cloning: https://elevenlabs.io/docs/eleven-creative/voices/voice-cloning/instant-voice-cloning
- ElevenLabs TTS API: https://elevenlabs.io/docs/api-reference/text-to-speech/stream
- Runway API: https://docs.dev.runwayml.com/api/
- Runway credits: https://docs.dev.runwayml.com/guides/pricing/
- OTIOZ format: https://opentimelineio.readthedocs.io/en/latest/tutorials/otio-filebundles.html
- DaVinci Resolve OTIO import (Blackmagic): https://documents.blackmagicdesign.com/in/SupportNotes/DaVinci_Resolve_18.5_New_Features_Guide.pdf
- n8n Docker Compose: https://docs.n8n.io/hosting/installation/server-setups/docker-compose/
- YouTube AI disclosures: https://support.google.com/youtube/answer/14328491
