"""Fail-closed P04.06 mechanical detailing tests, no image/API calls."""
import copy
import hashlib
import json
import pathlib
import tempfile
import unittest

from imaging.p04.modular.mechanical_detail import (
    APPROVED_SHA, DetailRejected, create_spec, verify_detail, write_details
)

BASE = pathlib.Path(__file__).resolve().parent
GEO = BASE / "FWAI-T001_geometry_spec.json"
APP = BASE / "FWAI-T001_owner_acceptance.json"


class MechanicalDetailTests(unittest.TestCase):
    def setUp(self):
        self.detail = create_spec(GEO, APP)
        self.geometry = json.loads(GEO.read_text())
        self.approval = json.loads(APP.read_text())

    def reject(self, change):
        candidate = copy.deepcopy(self.detail)
        change(candidate)
        with self.assertRaises(DetailRejected):
            verify_detail(candidate, self.geometry, self.approval)

    def test_actual_signed_off_geometry_hash(self):
        self.assertEqual(hashlib.sha256(GEO.read_bytes()).hexdigest(), APPROVED_SHA)
        self.assertEqual(self.detail["geometry_sha256"], APPROVED_SHA)
        self.assertEqual(self.approval["owner_decisions"]["P04.06-GEOMETRY"], "APPROVE")

    def test_six_connected_arms_and_subsystems(self):
        verdict = verify_detail(self.detail, self.geometry, self.approval)
        self.assertEqual(verdict["arms"], 6)
        self.assertEqual(verdict["linked_sections"], 12)
        self.assertEqual(verdict["subsystems"], 6)
        self.assertFalse(verdict["rendering_authorized"])
        self.assertFalse(verdict["physical_feasibility"] == "CERTIFIED")

    def test_detached_joint_rejected(self):
        self.reject(lambda x: x["arms"][2]["joint_coordinates_m"][0].__setitem__(0, 999))

    def test_fabricated_link_length_rejected(self):
        self.reject(lambda x: x["arms"][0].__setitem__("distal_link_length_m", 99))

    def test_missing_actuation_interface_rejected(self):
        self.reject(lambda x: x["arms"][1]["actuation_concept"].pop("elbow"))

    def test_missing_cable_protection_rejected(self):
        self.reject(lambda x: x["arms"][4].__setitem__("cable_path_description", "bare cable"))

    def test_missing_power_isolation_rejected(self):
        self.reject(lambda x: x["arms"][0]["service"].__setitem__("safing", "not protected"))

    def test_missing_serviceability_rejected(self):
        self.reject(lambda x: x["arms"][2]["service"].__setitem__("method", "no maintenance"))

    def test_reject_unauthorized_material_render(self):
        self.reject(lambda x: x["design_boundaries"].__setitem__("material_rendering_authorized", True))

    def test_reject_environment_render_and_publish(self):
        self.reject(lambda x: x["design_boundaries"].__setitem__("environment_rendering_authorized", True))
        self.reject(lambda x: x["design_boundaries"].__setitem__("publishing_authorized", True))

    def test_reject_false_engineering_certification(self):
        self.reject(lambda x: x["design_boundaries"].__setitem__("physics_certified", True))
        self.reject(lambda x: x["design_boundaries"].__setitem__("fea_performed", True))

    def test_reject_wrong_hatch_scale_and_missing_interface(self):
        self.reject(lambda x: x["service_hatch"].__setitem__("width_m", 20))
        self.reject(lambda x: x["subsystem_interfaces"].pop("thermal"))

    def test_no_unapproved_promotion_or_external_upload(self):
        self.assertEqual(self.detail["review_state"], "PENDING_OWNER_MECHANICAL_DETAIL_REVIEW")
        self.assertFalse(self.detail["design_boundaries"]["external_upload_authorized"])
        self.assertFalse(self.detail["design_boundaries"]["api_spend_authorized"])

    def test_reject_tampered_approval_hash_or_decision(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = pathlib.Path(folder) / "owner.json"
            altered = copy.deepcopy(self.approval)
            altered["owner_decisions"]["P04.06-GEOMETRY"] = "HOLD"
            fake.write_text(json.dumps(altered))
            with self.assertRaises(DetailRejected):
                create_spec(GEO, fake)
            altered["owner_decisions"]["P04.06-GEOMETRY"] = "APPROVE"
            altered["spec_sha256"] = "0" * 64
            fake.write_text(json.dumps(altered))
            with self.assertRaises(DetailRejected):
                create_spec(GEO, fake)

    def test_receipt_hash_and_determinism(self):
        with tempfile.TemporaryDirectory() as folder:
            first = write_details(GEO, APP, folder)
            second = write_details(GEO, APP, folder)
            self.assertEqual(first, second)
            payload=(pathlib.Path(folder) / first["detail_file"]).read_bytes()
            self.assertEqual(first["detail_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(first["owner_mechanical_approval"], "PENDING")
            self.assertEqual(first["paid_provider_calls"], 0)


if __name__ == "__main__":
    unittest.main()
