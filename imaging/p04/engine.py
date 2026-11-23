"""P04 local-only ComfyUI image generation, durable metadata and Visual handoff.

No paid services, credentials, publishing, prod mounts or model downloads.
Model bytes must be SHA-256 verified before every new generation batch.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zlib

REPO = Path(__file__).resolve().parents[2]
CATALOG = json.loads((Path(__file__).with_name("model-catalog.json")).read_text())
MANIFEST = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
MODEL = CATALOG["primary"]
TEMPLATES = {
    "thumbnail": {
        "width": 768, "height": 512, "steps": 16, "cfg": 6.5,
        "hint": "high contrast heroic composition, dramatic cyan rim lighting, visually striking original technology concept, clear central silhouette, no lettering"
    },
    "establishing": {
        "width": 768, "height": 512, "steps": 16, "cfg": 6.5,
        "hint": "wide cinematic establishing view, credible industrial space, consistent graphite titanium and cyan design language, 35mm lens"
    },
    "mechanical": {
        "width": 512, "height": 512, "steps": 16, "cfg": 6.5,
        "hint": "macro close-up of fictional robot mechanism, metal linkages, precision machining texture, concept illustration not engineering specification"
    },
    "texture": {
        "width": 512, "height": 512, "steps": 16, "cfg": 6.5,
        "hint": "material swatch study of brushed graphite titanium and cyan accents, detailed PBR-like surface texture, no logos"
    },
}
NEGATIVE = "watermark, text, logo, trademark, screenshot, real laboratory proof, duplicated limbs, deformed geometry, blurry, low quality, incorrect brand insignia"


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class Rejected(ValueError):
    pass


def validate_backend(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname not in
            ("127.0.0.1", "localhost", "host.docker.internal") or
            parsed.username or parsed.password or
            parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise Rejected("Only the local ComfyUI HTTP backend is permitted")
    if parsed.port is None or not 1024 <= parsed.port <= 65535:
        raise Rejected("Explicit unprivileged local ComfyUI port required")
    return url.rstrip("/")


def png_dimensions(raw):
    """Validate PNG chunk bounds/checksums, not merely its image signature."""
    if len(raw) < 57 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise Rejected("ComfyUI did not return a complete PNG")
    cursor, dimensions, seen_image, seen_end = 8, None, False, False
    while cursor + 12 <= len(raw):
        length = struct.unpack(">I", raw[cursor:cursor+4])[0]
        if length > 20 * 1024 * 1024 or cursor + length + 12 > len(raw):
            raise Rejected("Invalid PNG chunk boundary")
        kind = raw[cursor+4:cursor+8]
        payload = raw[cursor+8:cursor+8+length]
        expected_crc = struct.unpack(">I", raw[cursor+8+length:cursor+12+length])[0]
        if zlib.crc32(kind + payload) & 0xffffffff != expected_crc:
            raise Rejected("PNG chunk checksum mismatch")
        if dimensions is None:
            if kind != b"IHDR" or length != 13:
                raise Rejected("PNG must start with IHDR")
            width, height = struct.unpack(">II", payload[:8])
            if not (64 <= width <= 8192 and 64 <= height <= 8192):
                raise Rejected("Invalid generated image dimensions")
            dimensions = (width, height)
        if kind == b"IDAT":
            seen_image = True
        cursor += 12 + length
        if kind == b"IEND":
            if length or cursor != len(raw):
                raise Rejected("Invalid PNG terminator")
            seen_end = True
            break
    if dimensions is None or not seen_image or not seen_end:
        raise Rejected("PNG has no complete image body")
    return dimensions

def verify_model(path):
    path = Path(path).resolve()
    if not path.is_file() or path.name != MODEL["filename"]:
        raise Rejected("Missing pinned local model")
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            h.update(block)
    if h.hexdigest() != MODEL["sha256"]:
        raise Rejected("Model SHA-256 differs from published checkpoint")
    return h.hexdigest()


def workflow(job):
    """Unmodified built-in ComfyUI text-to-image API nodes, not custom code."""
    spec = TEMPLATES[job["kind"]]
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {
            "ckpt_name": MODEL["filename"]}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {
            "text": job["prompt"], "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {
            "text": NEGATIVE, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {
            "width": spec["width"], "height": spec["height"], "batch_size": 1}},
        "5": {"class_type": "KSampler", "inputs": {
            "seed": job["seed"], "steps": spec["steps"], "cfg": spec["cfg"],
            "sampler_name": "euler", "scheduler": "normal",
            "denoise": 1.0, "model": ["1", 0], "positive": ["2", 0],
            "negative": ["3", 0], "latent_image": ["4", 0]}},
        "6": {"class_type": "VAEDecode", "inputs": {
            "samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {
            "filename_prefix": "FWAI_P04_DEV_" + job["image_id"],
            "images": ["6", 0]}},
    }


class Comfy:
    def __init__(self, url="http://127.0.0.1:8188"):
        self.url = validate_backend(url)

    def request(self, path, payload=None, *, binary=False):
        if not path.startswith("/") or "//" in path or ".." in path:
            raise Rejected("Invalid Comfy API path")
        data = compact(payload).encode() if payload is not None else None
        req = urllib.request.Request(
            self.url + path, data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if data is not None else "GET")
        try:
            with urllib.request.urlopen(req, timeout=180) as res:
                raw = res.read(18 * 1024 * 1024 + 1 if binary else 4 * 1024 * 1024)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise Rejected("Comfy API unavailable or ambiguous response") from exc
        if len(raw) > (18 * 1024 * 1024 if binary else 4 * 1024 * 1024 - 1):
            raise Rejected("Comfy API response exceeds size limit")
        return raw if binary else json.loads(raw)

    def health(self):
        data = self.request("/system_stats")
        if not isinstance(data, dict) or not data.get("devices"):
            raise Rejected("Comfy health missing device data")
        return data

    def submit(self, job):
        data = self.request("/prompt", {"prompt": workflow(job),
                                        "client_id": "FWAI_P04_DEV"})
        prompt_id = data.get("prompt_id")
        try:
            uuid.UUID(prompt_id)
        except (TypeError, ValueError) as exc:
            raise Rejected("Comfy prompt acknowledgement missing stable UUID") from exc
        return prompt_id

    def result(self, prompt_id):
        result = self.request("/history/" + str(uuid.UUID(prompt_id)))
        run = result.get(prompt_id)
        if not run:
            return None
        status = run.get("status", {})
        if status.get("status_str") == "error" or status.get("completed") is False:
            raise Rejected("Comfy generation failed or incomplete")
        outputs = run.get("outputs", {}).get("7", {}).get("images", [])
        if len(outputs) != 1:
            raise Rejected("Comfy history does not contain exactly one saved image")
        item = outputs[0]
        if (item.get("type") != "output" or
                any(type(item.get(k)) is not str for k in ("filename", "subfolder"))):
            raise Rejected("Invalid Comfy image provenance")
        params = urllib.parse.urlencode({
            "filename": item["filename"], "subfolder": item["subfolder"], "type": "output"
        })
        return self.request("/view?" + params, binary=True)


class ImagePipeline:
    def __init__(self, database, output_root, comfy=None):
        self.db = Path(database).resolve()
        self.out = Path(output_root).resolve()
        if self.out.is_relative_to(REPO) or self.db.is_relative_to(REPO):
            raise Rejected("Generated bytes/index cannot enter git source checkout")
        if self.out.is_relative_to(Path("/data")) or self.db.is_relative_to(Path("/data")):
            raise Rejected("Production storage is forbidden")
        self.out.mkdir(parents=True, exist_ok=True)
        self.db.parent.mkdir(parents=True, exist_ok=True)
        self.comfy = comfy or Comfy()
        with self.tx() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS image_jobs(
              image_id TEXT PRIMARY KEY, project_id TEXT NOT NULL,
              run_id TEXT NOT NULL, manifest_sha TEXT NOT NULL,
              scene_id TEXT NOT NULL, kind TEXT NOT NULL, prompt TEXT NOT NULL,
              seed INTEGER NOT NULL, model_id TEXT NOT NULL,
              model_sha TEXT NOT NULL, license TEXT NOT NULL,
              reference_id TEXT NOT NULL, state TEXT NOT NULL,
              prompt_id TEXT UNIQUE, path TEXT, image_sha TEXT, error TEXT,
              created_at TEXT NOT NULL
            );
            """)

    @contextmanager
    def tx(self):
        db = sqlite3.connect(self.db, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def prepare(self, manifest, *, run_id, model_sha):
        # Exact content and SHA reference before any generation-side mutation.
        if manifest.resolve() != MANIFEST.resolve():
            raise Rejected("Only approved synthetic P01 manifest supported at development gate")
        raw = manifest.read_bytes()
        if sha(raw) != "cf2bbd17b2170755fef18de1be5ea4c08694ee894c8167c70ed322aa9906fe87":
            raise Rejected("Frozen P01 manifest bytes changed")
        data = json.loads(raw)
        if data.get("approval_state", {}).get("status") not in ("pending_review", "approved"):
            raise Rejected("Invalid manifest approval state")
        if not isinstance(run_id, str) or not (5 <= len(run_id) <= 80) or not all(
            x.isalnum() or x in "-_" for x in run_id):
            raise Rejected("Invalid image batch identity")
        if model_sha != MODEL["sha256"]:
            raise Rejected("Model bytes unverified")
        specs = [
            ("S01", "thumbnail"), ("S01", "establishing"),
            ("S02", "mechanical"), ("S02", "texture"),
            ("S03", "establishing"), ("S03", "mechanical"),
            ("S04", "thumbnail"), ("S04", "texture"),
            ("S05", "establishing"), ("S05", "mechanical"),
        ]
        scenes = {s["scene_id"]: s for s in data["scenes"]}
        if len(scenes) != 5:
            raise Rejected("Five exact reference scenes required")
        image_ids = []
        with self.tx() as db:
            for idx, (scene_id, kind) in enumerate(specs):
                scene = scenes[scene_id]
                image_id = "P04_" + run_id + "_" + str(idx + 1).zfill(2)
                seed = 10042026 + idx * 719
                prompt = (
                    "Original fictional AI_CONCEPT scene. NEVER portray verified real "
                    "engineering, a product photo or tested functionality. "
                    + scene["visual_prompt"] + ". " + TEMPLATES[kind]["hint"] +
                    ". Keep consistent graphite titanium computer transforming "
                    "into a robot with electric cyan highlights; fictional concept art."
                )
                ref = data["project_id"] + ":" + scene_id + ":concept_graphite_cyan_v1"
                row = db.execute("SELECT * FROM image_jobs WHERE image_id=?",
                                 (image_id,)).fetchone()
                values = (image_id, data["project_id"], run_id, sha(raw),
                          scene_id, kind, prompt, seed, MODEL["id"],
                          model_sha, MODEL["license"], ref)
                if row:
                    if tuple(row[k] for k in (
                        "image_id", "project_id", "run_id", "manifest_sha",
                        "scene_id", "kind", "prompt", "seed", "model_id",
                        "model_sha", "license", "reference_id")) != values:
                        raise Rejected("Image job idempotency conflict")
                else:
                    db.execute("INSERT INTO image_jobs(image_id,project_id,run_id,"
                               "manifest_sha,scene_id,kind,prompt,seed,model_id,model_sha,"
                               "license,reference_id,state,created_at) "
                               "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'queued',?)",
                               values + (now(),))
                image_ids.append(image_id)
        return image_ids

    def submit_one(self, image_id):
        with self.tx() as db:
            row = db.execute("SELECT * FROM image_jobs WHERE image_id=?",
                             (image_id,)).fetchone()
            if not row:
                raise Rejected("Unknown image")
            if row["state"] != "queued":
                return row["state"]
            db.execute("UPDATE image_jobs SET state='submitting' WHERE image_id=?",
                       (image_id,))
            job = dict(row)
        # IMPORTANT: if submission is accepted but reply is lost, never requeue
        # automatically. The durable 'submitting' state requires reconciliation.
        try:
            prompt_id = self.comfy.submit(job)
        except Exception as exc:
            with self.tx() as db:
                db.execute("UPDATE image_jobs SET state='needs_review',error=? "
                           "WHERE image_id=?", (str(exc)[:160], image_id))
            raise
        with self.tx() as db:
            db.execute("UPDATE image_jobs SET state='submitted',prompt_id=? "
                       "WHERE image_id=? AND state='submitting'", (prompt_id, image_id))
        return prompt_id

    def poll_one(self, image_id):
        with self.tx() as db:
            row = db.execute("SELECT * FROM image_jobs WHERE image_id=?",
                             (image_id,)).fetchone()
            if not row or row["state"] not in ("submitted", "complete"):
                raise Rejected("Image has no known prompt receipt")
            if row["state"] == "complete":
                return "complete"
            job = dict(row)
        try:
            raw = self.comfy.result(job["prompt_id"])
        except Exception as exc:
            with self.tx() as db:
                db.execute("UPDATE image_jobs SET state='needs_review',error=? "
                           "WHERE image_id=?", (str(exc)[:160], image_id))
            raise
        if raw is None:
            return "submitted"
        try:
            if png_dimensions(raw) != (TEMPLATES[job["kind"]]["width"],
                                        TEMPLATES[job["kind"]]["height"]):
                raise Rejected("Output image dimensions do not match planned template")
        except Rejected as exc:
            with self.tx() as db:
                db.execute("UPDATE image_jobs SET state='needs_review',error=? "
                           "WHERE image_id=? AND state='submitted'",
                           (str(exc)[:160], image_id))
            raise
        path = self.out / (image_id + ".png")
        if path.exists():
            if sha(path.read_bytes()) != sha(raw):
                raise Rejected("Refusing to replace nonmatching immutable image")
        else:
            temp = self.out / (image_id + "." + uuid.uuid4().hex + ".part")
            try:
                temp.write_bytes(raw)
                temp.replace(path)
            finally:
                temp.unlink(missing_ok=True)
        image_sha = sha(raw)
        with self.tx() as db:
            db.execute("UPDATE image_jobs SET state='complete',path=?,image_sha=?,"
                       "error=NULL WHERE image_id=? AND state='submitted'",
                       (str(path), image_sha, image_id))
        return "complete"

    def dashboard(self, run_id):
        with self.tx() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM image_jobs "
                "WHERE run_id=? ORDER BY image_id", (run_id,))]
        return {
            "run_id": run_id, "total": len(rows),
            "completed": sum(r["state"] == "complete" for r in rows),
            "needs_review": sum(r["state"] in ("needs_review", "submitting") for r in rows),
            "status": "ready_for_visual_review" if len(rows) == 10 and
                      all(r["state"] == "complete" for r in rows) else "in_progress",
            "images": rows,
            "authorization": {"production_approved": False,
                              "spend_authorized": False,
                              "publish_authorized": False},
            "paid_provider_calls": 0,
        }

    def visual_handoff(self, run_id, *, save=True):
        report = self.dashboard(run_id)
        if report["status"] != "ready_for_visual_review":
            raise Rejected("Ten actual downloaded PNGs required before Visual handoff")
        images = []
        for row in report["images"]:
            path = Path(row["path"])
            if not path.is_relative_to(self.out) or not path.is_file():
                raise Rejected("Indexed image missing from controlled output directory")
            raw = path.read_bytes()
            if sha(raw) != row["image_sha"]:
                raise Rejected("Local image changed since indexing")
            images.append({
                "asset_id": row["image_id"], "project_id": row["project_id"],
                "scene_id": row["scene_id"], "role": "visual_director",
                "media_type": "image/png", "local_path": str(path),
                "sha256": row["image_sha"], "prompt": row["prompt"],
                "seed": row["seed"], "template": row["kind"],
                "model_id": row["model_id"], "model_sha256": row["model_sha"],
                "license": row["license"], "reference_id": row["reference_id"],
                "approval_state": "requires_visual_director_review",
                "comfy_prompt_id": row["prompt_id"],
            })
        handoff = {
            "schema_version": "P04_DEV_1",
            "project_id": images[0]["project_id"], "run_id": run_id,
            "status": "ready_for_visual_director",
            "assets": images, "assets_count": 10,
            "authorization": report["authorization"],
            "dispatch_performed": False, "paid_provider_calls": 0,
        }
        if save:
            dest = self.out / ("VISUAL_DIRECTOR_HANDOFF_" + run_id + ".json")
            temp = self.out / (uuid.uuid4().hex + ".tmp")
            try:
                temp.write_text(json.dumps(handoff, indent=2))
                temp.replace(dest)
            finally:
                temp.unlink(missing_ok=True)
        return handoff
