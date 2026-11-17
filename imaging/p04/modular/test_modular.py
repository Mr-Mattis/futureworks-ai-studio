"""P04.06 isolated geometry and function gates; no inference or network."""
import copy,json,pathlib,tempfile,unittest
from xml.etree import ElementTree as ET
from imaging.p04.modular.geometry import check,diagram,produce,GeometryRejected
from imaging.p04.modular.mechanical import inspect,MechanicalRejected

HERE=pathlib.Path(__file__).resolve().parent
BASE=json.loads((HERE/"FWAI-T001_geometry_spec.json").read_text())

class GeometryTests(unittest.TestCase):
    def setUp(self):self.s=copy.deepcopy(BASE)
    def test_valid_complete_orbital_platform(self):
        out=check(self.s)
        self.assertEqual(out["fabrication_arms"],6)
        self.assertEqual(out["crew_access_width_m"],2)
        self.assertFalse(out["manufacturing_certified"])
        self.assertTrue(out["environment_excluded"])
    def test_environment_is_forbidden_at_subject_gate(self):
        self.s["environment"]={"sky":"stellar"}
        with self.assertRaises(GeometryRejected):check(self.s)
    def test_military_features_forbidden(self):
        self.s["weapons"]=["turret"]
        with self.assertRaises(GeometryRejected):check(self.s)
    def test_scale_must_be_human_readable(self):
        self.s["crew_access"]["width_m"]=20
        with self.assertRaises(GeometryRejected):check(self.s)
    def test_nonattached_arm_fails(self):
        self.s["fabrication_arms"][2]["joints"][0][0]+=3
        with self.assertRaises(GeometryRejected):check(self.s)
    def test_missing_structural_anchor_fails(self):
        self.s["ring"].pop()
        with self.assertRaises(GeometryRejected):check(self.s)
    def test_clipped_or_invalid_linkage_fails(self):
        self.s["fabrication_arms"][0]["joints"][1]=[900,900]
        with self.assertRaises(GeometryRejected):check(self.s)
    def test_mask_and_blueprint_are_deterministic(self):
        first=diagram(self.s);self.assertEqual(first,diagram(self.s))
        mask=diagram(self.s,mask=True)
        self.assertNotEqual(first,mask)
        self.assertIn(b"FWAI-T001",first)
        self.assertNotIn(b"FWAI-T001",mask)
        self.assertIsNotNone(ET.fromstring(first))
    def test_receipt_is_hash_bound_and_no_environment_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec=produce(HERE/"FWAI-T001_geometry_spec.json",tmp)
            self.assertFalse(rec["environment_generation_allowed"])
            self.assertFalse(rec["material_rendering_allowed"])
            self.assertTrue(rec["owner_approval_required"])
            for artifact in rec["artifacts"].values():
                file=pathlib.Path(tmp)/artifact["path"]
                self.assertEqual(__import__("hashlib").sha256(file.read_bytes()).hexdigest(),artifact["sha256"])

class MechanicalTests(unittest.TestCase):
    def setUp(self):self.s=copy.deepcopy(BASE)
    def test_mechanical_linkage_heuristic_passes_without_claiming_feasibility(self):
        out=inspect(self.s)
        self.assertEqual(out["result"],"HEURISTIC_MECHANICAL_QA_PASS")
        self.assertEqual(out["subsystem_connection_checks"],6)
        self.assertFalse(out["physical_feasibility_certified"])
        self.assertFalse(out["simulation_or_fea_performed"])
    def test_invalid_actuation_chain_fails(self):
        self.s["fabrication_arms"][1]["mechanical_chain"]="arbitrary_paint"
        with self.assertRaises(MechanicalRejected):inspect(self.s)
    def test_missing_power_routing_fails(self):
        self.s["fabrication_arms"][1]["power"]=""
        with self.assertRaises(MechanicalRejected):inspect(self.s)
    def test_missing_service_access_fails(self):
        self.s["fabrication_arms"][3]["maintenance"]=""
        with self.assertRaises(MechanicalRejected):inspect(self.s)
    def test_cannot_mislabel_as_certified_engineering(self):
        self.s["engineering_status"]="physics_proven"
        with self.assertRaises(MechanicalRejected):inspect(self.s)

if __name__=="__main__":unittest.main()
