"""P04 offline concurrency, metadata, download integrity and Visual handoff tests."""
from __future__ import annotations
import concurrent.futures
import copy
import hashlib
from pathlib import Path
import sqlite3
import struct
import tempfile
import unittest
import uuid
import zlib

import engine
from engine import Comfy, ImagePipeline, MANIFEST, MODEL, Rejected, TEMPLATES, png_dimensions, workflow

RUN = "P04_TEST_BATCH_001"


def chunk(t, payload):
    raw = t + payload
    return struct.pack(">I", len(payload)) + raw + struct.pack(">I", zlib.crc32(raw) & 0xffffffff)


def png(w=512, h=512):
    # Original generated fixture pixels only. NEVER count as ComfyUI output.
    raw_rows = b"".join(b"\x00" + b"\x44\x66\x88" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw_rows, 6)) + chunk(b"IEND", b""))


class FakeComfy:
    def __init__(self):
        self.submissions = []
        self.fail = False
        self.pending = False
        self.bad_png = False
        self.jobs = {}

    def submit(self, job):
        if self.fail:
            raise Rejected("Simulated lost acknowledgement (outcome unknown)")
        prompt_id = str(uuid.uuid4())
        self.submissions.append(job["image_id"])
        self.jobs[prompt_id] = (job["kind"], job["image_id"])
        return prompt_id

    def result(self, prompt_id):
        if self.pending:
            return None
        kind, image_id = self.jobs[prompt_id]
        spec = TEMPLATES[kind]
        if self.bad_png:
            return b"not an image"
        return png(spec["width"], spec["height"])

    def health(self):
        return {"devices":[{"name":"AMD Radeon RX 9070 XT"}]}


class ImagePipelineTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.mock = FakeComfy()
        self.engine = ImagePipeline(self.folder / "jobs.db", self.folder / "images", self.mock)

    def prepare(self):
        return self.engine.prepare(MANIFEST, run_id=RUN, model_sha=MODEL["sha256"])

    def test_ten_real_work_intents_and_four_templates(self):
        ids = self.prepare()
        self.assertEqual(len(ids), 10)
        self.assertEqual(len(set(ids)), 10)
        report = self.engine.dashboard(RUN)
        self.assertEqual(report["completed"], 0)
        self.assertEqual(report["status"], "in_progress")
        self.assertEqual(set(r["kind"] for r in report["images"]), set(TEMPLATES))
        self.assertTrue(all(r["state"] == "queued" for r in report["images"]))
        self.assertEqual({r["scene_id"] for r in report["images"]},
                         {"S01","S02","S03","S04","S05"})
        self.assertFalse(any(report["authorization"].values()))

    def test_prepare_replay_stays_exact_and_never_duplicates(self):
        first = self.prepare()
        second = self.prepare()
        self.assertEqual(first, second)
        with sqlite3.connect(self.engine.db) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM image_jobs").fetchone()[0],10)

    def test_unknown_manifest_and_unverified_model_fail_closed(self):
        with self.assertRaises(Rejected):
            self.engine.prepare(self.folder / "fake.json", run_id=RUN, model_sha=MODEL["sha256"])
        with self.assertRaises(Rejected):
            self.engine.prepare(MANIFEST, run_id=RUN, model_sha="0"*64)

    def test_invalid_comfy_url_never_allowed(self):
        for u in ("https://api.runwayml.com:443", "http://google.com:8188",
                  "http://127.0.0.1:80", "http://127.0.0.1:8188/foo",
                  "http://user:pass@localhost:8188"):
            with self.subTest(url=u), self.assertRaises(Rejected):
                Comfy(u)

    def test_api_workflow_only_builtins_and_exact_seed(self):
        self.prepare()
        job = self.engine.dashboard(RUN)["images"][0]
        graph = workflow(job)
        self.assertEqual(set(n["class_type"] for n in graph.values()),
                         {"CheckpointLoaderSimple","CLIPTextEncode","EmptyLatentImage",
                          "KSampler","VAEDecode","SaveImage"})
        self.assertEqual(graph["5"]["inputs"]["seed"],job["seed"])
        self.assertEqual(graph["1"]["inputs"]["ckpt_name"], MODEL["filename"])
        self.assertTrue(graph["7"]["inputs"]["filename_prefix"].startswith("FWAI_P04_DEV_"))

    def test_single_known_comfy_prompt_receipt(self):
        first = self.prepare()[0]
        uuid.UUID(self.engine.submit_one(first))
        self.assertEqual(self.engine.submit_one(first), "submitted")
        self.assertEqual(len(self.mock.submissions),1)

    def test_simulated_lost_acknowledgement_requires_reconciliation(self):
        first = self.prepare()[0]
        self.mock.fail = True
        with self.assertRaises(Rejected):
            self.engine.submit_one(first)
        self.assertEqual(self.engine.dashboard(RUN)["images"][0]["state"], "needs_review")
        self.assertEqual(self.engine.submit_one(first), "needs_review")
        self.assertEqual(len(self.mock.submissions), 0)

    def test_pending_history_never_redrives_generation(self):
        first = self.prepare()[0]
        self.engine.submit_one(first)
        self.mock.pending = True
        self.assertEqual(self.engine.poll_one(first), "submitted")
        self.mock.pending = False
        self.assertEqual(self.engine.poll_one(first), "complete")
        self.assertEqual(len(self.mock.submissions), 1)

    def test_invalid_png_never_indexed(self):
        first = self.prepare()[0]
        self.engine.submit_one(first)
        self.mock.bad_png = True
        with self.assertRaises(Rejected):
            self.engine.poll_one(first)
        self.assertEqual(self.engine.dashboard(RUN)["completed"],0)
        self.assertEqual(self.engine.dashboard(RUN)["images"][0]["state"],"needs_review")
        self.assertEqual(self.engine.submit_one(first),"needs_review")
        self.assertEqual(len(self.mock.submissions),1)

    def test_ten_downloads_are_indexed_without_manual_transfer(self):
        ids = self.prepare()
        for image_id in ids:
            self.engine.submit_one(image_id)
            self.assertEqual(self.engine.poll_one(image_id), "complete")
        report = self.engine.dashboard(RUN)
        self.assertEqual(report["completed"],10)
        self.assertEqual(report["status"],"ready_for_visual_review")
        handoff = self.engine.visual_handoff(RUN)
        self.assertEqual(handoff["assets_count"], 10)
        self.assertEqual({r["approval_state"] for r in handoff["assets"]},
                         {"requires_visual_director_review"})
        self.assertEqual({r["role"] for r in handoff["assets"]}, {"visual_director"})
        self.assertEqual(len({r["seed"] for r in handoff["assets"]}),10)
        self.assertEqual(len({r["comfy_prompt_id"] for r in handoff["assets"]}),10)
        self.assertTrue((self.engine.out /
            ("VISUAL_DIRECTOR_HANDOFF_" + RUN + ".json")).is_file())
        self.assertFalse(any(handoff["authorization"].values()))
        self.assertEqual(handoff["paid_provider_calls"],0)

    def test_tampered_png_blocks_visual_handoff(self):
        ids = self.prepare()
        for image_id in ids:
            self.engine.submit_one(image_id)
            self.engine.poll_one(image_id)
        (self.engine.out / (ids[0] + ".png")).write_bytes(b"tampered")
        with self.assertRaisesRegex(Rejected, "changed"):
            self.engine.visual_handoff(RUN)

    def test_incomplete_generation_blocks_visual_handoff(self):
        self.prepare()
        with self.assertRaises(Rejected):
            self.engine.visual_handoff(RUN)

    def test_png_headers_reject_forged_data(self):
        with self.assertRaises(Rejected):
            png_dimensions(b"GIF89a")
        self.assertEqual(png_dimensions(png(512,512)),(512,512))

    def test_known_model_hash_is_required(self):
        original = engine.MODEL
        try:
            tiny = self.folder / MODEL["filename"]
            tiny.write_bytes(b"local model test fixture")
            engine.MODEL = {**original, "sha256":hashlib.sha256(tiny.read_bytes()).hexdigest()}
            self.assertEqual(engine.verify_model(tiny),engine.MODEL["sha256"])
            tiny.write_bytes(b"changed")
            with self.assertRaises(Rejected):
                engine.verify_model(tiny)
        finally:
            engine.MODEL = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
