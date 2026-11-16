"""P05 n8n disabled-provider graph acceptance: exact source, Node VM."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import re
import subprocess
import unittest

HERE=Path(__file__).resolve().parent
SOURCE=(HERE/"workflow.inactive.sdk.js").read_text()
SCRIPTS=[json.loads(x) for x in re.findall(r'jsCode:("(?:\\.|[^"\\])*")',SOURCE)]
if len(SCRIPTS)!=3:
    raise AssertionError("Expected exactly three policy Code nodes")
FREEZE,POLICY,FINAL=SCRIPTS


def invoke(js,items):
    proc=subprocess.run(["/usr/bin/node",str(HERE.parents[1]/"imaging/p04/check_n8n_wrapper.cjs")],
                        input=json.dumps({"code":js,"items":items}),
                        capture_output=True,text=True,check=True,timeout=10)
    return json.loads(proc.stdout)


class N8nVideoTests(unittest.TestCase):
    def test_runway_disabled_disconnected_unauthenticated(self):
        self.assertIn("disabled:true",SOURCE)
        self.assertIn("DISABLED Runway image to video provider adapter",SOURCE)
        self.assertIn("/v1/image_to_video",SOURCE)
        self.assertNotIn("Authorization",SOURCE)
        self.assertNotIn("RUNWAYML_API_SECRET",SOURCE)
        self.assertNotIn("youtubeUpload",SOURCE)
    def test_frozen_test_intake(self):
        out=invoke(FREEZE,[{}])
        self.assertTrue(out["ok"])
        self.assertFalse(invoke(FREEZE,[{"run_id":"UNAPPROVED"}])["ok"])
        self.assertEqual(out["result"][0]["json"]["paid_budget_cents"],0)
    def test_three_scenes_stay_unsubmitted_and_blocked(self):
        fixture=invoke(FREEZE,[{}])["result"][0]["json"]
        plan=invoke(POLICY,[fixture])
        self.assertTrue(plan["ok"],plan)
        raw=plan["result"][0]["json"]
        self.assertEqual([s["scene_id"] for s in raw["scenes"]],
                         ["S01","S02","S03"])
        self.assertFalse(any(s["provider_request_sent"] for s in raw["scenes"]))
        final=invoke(FINAL,[raw])
        self.assertTrue(final["ok"],final)
        self.assertEqual(final["result"][0]["json"]["locked_P05_exit"],"OPEN")
        self.assertFalse(any(final["result"][0]["json"]["authorization"].values()))
    def test_unsafe_budget_and_model_state_fail_closed(self):
        frozen=invoke(FREEZE,[{}])["result"][0]["json"]
        for mutation in (
            {"approved_provider_spend":True},
            {"paid_budget_cents":180},
            {"approved_manifest":True},
            {"model":"unknown_model"},
            {"scenes":["S01","S02","S03","S04"]},
        ):
            with self.subTest(mutation=mutation):
                self.assertFalse(invoke(POLICY,[frozen|mutation])["ok"])
    def test_forged_paid_result_fails_final_gate(self):
        frozen=invoke(FREEZE,[{}])["result"][0]["json"]
        planned=invoke(POLICY,[frozen])["result"][0]["json"]
        for mutation in (
            {"actual_paid_calls":1},
            {"actual_generated_clips":3},
            {"authorization":{"spend_authorized":True}},
        ):
            with self.subTest(mutation=mutation):
                self.assertFalse(invoke(FINAL,[planned|mutation])["ok"])

if __name__=="__main__":
    unittest.main(verbosity=2)
