"""P05 isolated replaceable cinematic video engine.

NO paid provider execution capability is enabled in this module. The Runway
adapter only constructs validated request envelopes and parses test data.
Actual HTTP submission must be implemented under separate owner-approved
billing gates, never inferred from a merged PR.
"""
from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
P04 = REPO / "imaging/p04"
MANIFEST = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
MODEL = "gen4.5"
VERSION = "2024-11-06"
STAGES = ("S01", "S02", "S03")
BILLING_FIELDS = ("production_approved", "spend_authorized", "publish_authorized")
TEMPLATES = {
    "AI_CONCEPT": "Original fictional graphite-titanium computer transforms into a futuristic robot. Cyan accents and recognizable silhouette, slow cinematic camera motion; do not imply this is footage of real working hardware.",
    "REAL_BUILD": "Accurate documentary-style camera movement over a real photographed physical object; no invented construction steps or false demonstration of performance.",
    "HYBRID": "Photoreal cinematic transition clearly distinguishing real hardware imagery from fictional CGI concept visualization; preserve reference identity."
}
MAX_BYTES = 64 * 1024 * 1024
DEFAULT_BUDGET_CENTS = 0


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class Rejected(ValueError):
    pass


def validate_approval(approval):
    """Never trust caller-authored approval booleans or a claimed signature result.

    Only a separate cryptographic P04 owner approval verifier may authorize
    future workflows. This P05 development adapter intentionally has no
    authority to perform such a promotion.
    """
    raise Rejected("P05 caller approval flags cannot authorize production or paid use; independently signed P04 gate required")

def load_reference_bundle(path):
    p = Path(path).resolve()
    data = json.loads(p.read_text())
    if data.get("status") != "ready_for_visual_director" or data.get("assets_count") != 10:
        raise Rejected("P04 ten-image canonical reference index required")
    if data.get("authorization") != dict.fromkeys(BILLING_FIELDS, False):
        raise Rejected("P04 index must not claim spending or publishing authority")
    if data.get("dispatch_performed") or data.get("paid_provider_calls") != 0:
        raise Rejected("Untrusted P04 index")
    asset_ids = set()
    images = {}
    for a in data["assets"]:
        if not {"asset_id", "scene_id", "local_path", "sha256", "prompt", "seed", "model_sha256", "license", "approval_state"} <= set(a):
            raise Rejected("Missing image provenance")
        if not isinstance(a["asset_id"],str) or not re.fullmatch(r"P04_[A-Za-z0-9_]+",a["asset_id"]):
            raise Rejected("Untrusted asset identifier")
        file = (p.parent/(a["asset_id"]+".png")).resolve()
        if not file.is_file() or file.suffix.lower() != ".png" or not file.is_relative_to(p.parent):
            raise Rejected("Image must be a local PNG adjacent to trusted index")
        raw = file.read_bytes()
        if sha(raw) != a["sha256"]:
            raise Rejected("Image sha mismatch")
        if a["approval_state"] != "requires_visual_director_review":
            raise Rejected("Do not fabricate image approval from role metadata")
        if a["asset_id"] in asset_ids:
            raise Rejected("Duplicate image asset")
        asset_ids.add(a["asset_id"])
        images.setdefault(a["scene_id"], []).append(a)
    if len(asset_ids) != 10 or not set(STAGES).issubset(images):
        raise Rejected("Incomplete three-scene reference set")
    return data, images


def make_scene_requests(bundle, *, approval=None):
    """Unapproved real images can be used ONLY for dry-run request construction."""
    data, imgs = load_reference_bundle(bundle)
    manifest_raw = MANIFEST.read_bytes()
    manifest = json.loads(manifest_raw)
    manifest_sha = sha(manifest_raw)
    requests = []
    for scene in STAGES:
        a = imgs[scene][0]
        prompt = TEMPLATES[manifest["content_type"]] + " " + a["prompt"]
        if len(prompt) > 10000:
            raise Rejected("Runway prompt exceeds conservative budget")
        requests.append({
            "scene_id": scene, "mode": "image_to_video",
            "model": MODEL, "ratio": "1280:720", "duration": 5,
            "promptText": prompt,
            # Local image bytes cannot be sent to Runway directly; upload is
            # separately gated and is *not* fabricated from an image path.
            "reference_asset_id": a["asset_id"],
            "reference_sha256": a["sha256"],
            "reference_local_path": a["local_path"],
            "promptImage": None,
            "manifest_sha256": manifest_sha,
            "project_id": data["project_id"],
            "requires_human_review": True,
        })
    if approval is not None:
        validate_approval(approval)  # Untrusted user/model fields cannot grant permission.
    return requests


class RunwayWire:
    """Pure current-schema request builder. NO network client is instantiated."""
    BASE = "https://api.dev.runwayml.com"
    def __init__(self, *, enable_paid_calls=False):
        if enable_paid_calls:
            raise Rejected("Paid Runway integration requires separate owner authorization")
    @staticmethod
    def prepare(request, image_uri=None):
        if request["model"] != MODEL or request["duration"] != 5 or request["ratio"] != "1280:720":
            raise Rejected("Unexpected model/duration/ratio")
        if request["mode"] not in ("image_to_video", "text_to_video"):
            raise Rejected("Unsupported provider mode")
        fields = {"model": MODEL, "duration": 5, "ratio": "1280:720",
                  "promptText": request["promptText"]}
        route = "/v1/text_to_video"
        if request["mode"] == "image_to_video":
            if image_uri is None or not isinstance(image_uri, str) or not (
                image_uri.startswith("runway://") or image_uri.startswith("https://")):
                raise Rejected("Actual uploaded image URI required")
            fields["promptImage"] = image_uri
            route = "/v1/image_to_video"
        return {"endpoint": route, "version": VERSION, "body": fields}
    @staticmethod
    def parse_created(result):
        try:
            task = str(uuid.UUID(result["id"]))
        except (TypeError, ValueError, KeyError) as exc:
            raise Rejected("Missing validated provider task receipt") from exc
        return task
    @staticmethod
    def parse_status(result, task_id):
        if str(result.get("id")) != task_id:
            raise Rejected("Provider task identity mismatch")
        status = result.get("status")
        if status not in ("PENDING", "THROTTLED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"):
            raise Rejected("Unknown provider state")
        if status == "SUCCEEDED":
            output = result.get("output")
            if not isinstance(output, list) or len(output) != 1:
                raise Rejected("Expected exactly one video URI")
            url = output[0]
            if not isinstance(url, str) or not url.startswith("https://"):
                raise Rejected("Invalid expiring HTTPS output")
            return status, url
        return status, None


def mp4_probe(data):
    """Conservative MP4 container check; full decode and ffprobe are separate gates."""
    if len(data) < 32 or len(data) > MAX_BYTES or data[4:8] != b"ftyp":
        raise Rejected("Not a bounded ISO-BMFF MP4 container")
    size = struct.unpack(">I", data[:4])[0]
    if not 8 <= size <= len(data) or b"moov" not in data or b"mdat" not in data:
        raise Rejected("Incomplete MP4 container; ffprobe review still required")
    return True


class VideoStore:
    """Atomic job identities and local asset index: simulated transport only."""
    def __init__(self, database, output):
        self.database = Path(database).resolve()
        self.output = Path(output).resolve()
        if self.database.is_relative_to(REPO) or self.output.is_relative_to(REPO):
            raise Rejected("Development outputs must never enter repository")
        if self.database.is_relative_to(Path("/data")) or self.output.is_relative_to(Path("/data")):
            raise Rejected("Production storage is forbidden")
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.output.mkdir(parents=True, exist_ok=True)
        with self.tx() as db:
            db.executescript("""
              CREATE TABLE IF NOT EXISTS clips (
                project_id TEXT NOT NULL, run_id TEXT NOT NULL, scene_id TEXT NOT NULL,
                request_json TEXT NOT NULL, request_sha TEXT NOT NULL,
                state TEXT NOT NULL, task_id TEXT UNIQUE, poll_count INTEGER NOT NULL DEFAULT 0,
                next_poll TEXT, clip_path TEXT, clip_sha TEXT, cost_cents INTEGER NOT NULL DEFAULT 0,
                error TEXT, PRIMARY KEY (project_id,run_id,scene_id)
              );
            """)
    @contextmanager
    def tx(self):
        db = sqlite3.connect(self.database, isolation_level=None, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()
    def plan(self, run_id, requests):
        if not re.fullmatch(r"[A-Za-z0-9_-]{5,80}",run_id) or len(requests) != 3:
            raise Rejected("Three-scene unique project run required")
        if {r["scene_id"] for r in requests} != set(STAGES):
            raise Rejected("Expected exactly three known scene IDs")
        with self.tx() as db:
            for req in requests:
                existing = db.execute("SELECT request_sha FROM clips WHERE project_id=? AND run_id=? AND scene_id=?",
                                      (req["project_id"],run_id,req["scene_id"])).fetchone()
                h = sha(stable(req).encode())
                if existing and existing["request_sha"] != h:
                    raise Rejected("Idempotency conflict")
                db.execute("INSERT OR IGNORE INTO clips(project_id,run_id,scene_id,request_json,request_sha,state) "
                           "VALUES(?,?,?,?,?,'planned')",
                           (req["project_id"],run_id,req["scene_id"],stable(req),h))
        return self.dashboard(run_id)
    def stage_mock_receipt(self, run_id, scene, task_id):
        """Simulates receipt only: never sends a paid request."""
        task_id = str(uuid.UUID(task_id))
        with self.tx() as db:
            row = db.execute("SELECT state FROM clips WHERE run_id=? AND scene_id=?",
                             (run_id,scene)).fetchone()
            if not row or row["state"] != "planned":
                raise Rejected("Cannot add or replace provider receipt")
            db.execute("UPDATE clips SET state='mock_submitted',task_id=?,next_poll=? "
                       "WHERE run_id=? AND scene_id=?",
                       (task_id, now(), run_id,scene))
        return task_id
    def poll_mock(self, run_id, scene, payload, *, at=None):
        clock = at or now()
        with self.tx() as db:
            row = db.execute("SELECT * FROM clips WHERE run_id=? AND scene_id=?",
                             (run_id,scene)).fetchone()
            if row is None or row["state"] not in ("mock_submitted","mock_running"):
                raise Rejected("Task has no outstanding mock receipt")
            if row["next_poll"] and row["next_poll"] > clock:
                return "not_due"
            status,url = RunwayWire.parse_status(payload,row["task_id"])
            tries = row["poll_count"] + 1
            if status == "SUCCEEDED":
                state = "mock_output_pending"
            elif status in ("FAILED","CANCELLED") or tries >= 10:
                state = "needs_review"
            else:
                state = "mock_running"
            due = (datetime.now(timezone.utc)+timedelta(seconds=5*min(tries,6))).isoformat()
            db.execute("UPDATE clips SET state=?,poll_count=?,next_poll=?,error=? WHERE run_id=? AND scene_id=?",
                       (state,tries,due,None if status == "SUCCEEDED" else status,run_id,scene))
            return state
    def save_mock_clip(self, run_id, scene, data):
        """Tests asset persistence. The fixture is not a Runway-generated video."""
        mp4_probe(data)
        with self.tx() as db:
            row=db.execute("SELECT * FROM clips WHERE run_id=? AND scene_id=?",
                           (run_id,scene)).fetchone()
            if row is None or row["state"] != "mock_output_pending":
                raise Rejected("Provider success receipt required before archival")
            dest=self.output/(run_id+"_"+scene+".mp4")
            digest=sha(data)
            if dest.exists() and sha(dest.read_bytes()) != digest:
                raise Rejected("Existing immutable clip differs")
            if not dest.exists():
                tmp=self.output/("."+uuid.uuid4().hex+".part")
                try:
                    tmp.write_bytes(data)
                    tmp.replace(dest)
                finally:
                    tmp.unlink(missing_ok=True)
            db.execute("UPDATE clips SET state='mock_archived',clip_path=?,clip_sha=?,cost_cents=0 "
                       "WHERE run_id=? AND scene_id=?",(str(dest),digest,run_id,scene))
        return dest
    def dashboard(self, run_id):
        with self.tx() as db:
            jobs=[dict(x) for x in db.execute("SELECT * FROM clips WHERE run_id=? ORDER BY scene_id",(run_id,))]
        return {
            "run_id":run_id, "clips": jobs, "clip_count":len(jobs),
            "mock_archived":sum(x["state"] == "mock_archived" for x in jobs),
            "actual_paid_clips":0, "actual_credits_used":0,
            "budget_authorized_cents":DEFAULT_BUDGET_CENTS,
            "authorization":dict.fromkeys(BILLING_FIELDS,False),
            "status":"synthetic_only_not_P05_exit",
        }


def continuity_review(jobs):
    if len(jobs) != 3 or {x["scene_id"] for x in jobs} != set(STAGES):
        raise Rejected("Three scenes required")
    return {"verdict":"human_review_required",
            "issues":["Compare reference silhouettes and color grading",
                      "Compare opening and closing frames for match cuts",
                      "Confirm media rights and fictional disclosure",
                      "Decode actual videos; inspect for temporal glitches"],
            "correction_requests":[],
            "approval_state":"blocked",
            "clip_count":3,
            "publish_authorized":False}
