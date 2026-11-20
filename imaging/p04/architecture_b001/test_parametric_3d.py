"""FWAI-B001 geometry contract tests. Geometry-only, offline and fail-closed."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import pathlib
import tempfile
import unittest
from imaging.p04.architecture_b001.parametric_3d import DesignHold, validate, scene, build, FT

ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=ROOT/"FWAI-B001_geometry_v1.json"
SPEC=json.loads(SOURCE.read_text())

class ParameterTests(unittest.TestCase):
    def setUp(self):self.s=copy.deepcopy(SPEC)
    def rejected(self,alter):
        alter(self.s)
        with self.assertRaises(DesignHold):validate(self.s)
    def test_all_owner_decisions_preserved(self):
        r=validate(self.s)
        self.assertEqual(self.s["balcony"]["length_ft"],10)
        self.assertEqual(self.s["balcony"]["depth_ft"],6)
        self.assertEqual(self.s["balcony"]["floor_elevation_ft"],15)
        self.assertEqual(r["total_tread_solids"],48)
        self.assertEqual(self.s["staircase"]["central_axis"],"open_void_no_vertical_column")
        self.assertEqual(self.s["staircase"]["strand_construction"].split()[0],"hybrid")
        self.assertFalse(self.s["render_permissions"]["image_generation"])
    def test_staircase_is_counterclockwise(self):
        self.rejected(lambda s:s["staircase"].__setitem__("movement_descending_top_view","clockwise"))
    def test_two_independent_helix_strands(self):
        self.rejected(lambda s:s["staircase"].__setitem__("helix_count",1))
    def test_unacceptable_narrow_footpath(self):
        self.rejected(lambda s:s["staircase"].__setitem__("outer_walking_radius_ft",4.0))
    def test_outer_structural_envelope_fail(self):
        self.rejected(lambda s:s["staircase"].__setitem__("outer_support_radius_ft",6.2))
    def test_no_collapsing_support_ribbon_into_walkway(self):
        self.rejected(lambda s:s["staircase"].__setitem__("outer_support_radius_ft",5.7))
    def test_wrong_phase_difference_rejected(self):
        self.rejected(lambda s:s["staircase"].__setitem__("entry_phase_radians_B",2))
    def test_wrong_riser_total_rejected(self):
        self.rejected(lambda s:s["staircase"].__setitem__("riser_height_ft",.5))
    def test_more_revolutions_require_new_headroom_study(self):
        self.rejected(lambda s:s["staircase"].__setitem__("revolutions",1.5))
    def test_low_headroom_fails_design_gate(self):
        self.rejected(lambda s:s["staircase"].__setitem__("tread_thickness_ft",.7))
    def test_second_entry_must_stay_on_hold(self):
        self.rejected(lambda s:s["upper_transfer"].__setitem__("status","READY"))
    def test_environment_and_paid_permissions_stay_blocked(self):
        for scope in ("environment_rendering","material_rendering","paid_api","image_generation","publish","external_upload"):
            self.rejected(lambda s,sco=scope:s["render_permissions"].__setitem__(sco,True))
    def test_dimension_contract_is_exact(self):
        self.rejected(lambda s:s["balcony"].__setitem__("length_ft",11))
    def test_double_helix_pitch_and_tread_wedge_depth(self):
        r=validate(self.s)
        self.assertAlmostEqual(r["rise_in"],7.5)
        self.assertAlmostEqual(r["wedge_arc_depth_at_inner_edge_in"],7.540,places=2)
        self.assertAlmostEqual(r["wedge_arc_depth_12in_from_inner_edge_in"],10.681,places=2)
        self.assertAlmostEqual(r["approx_tread_only_headroom_ft"],7.25)
        self.assertEqual(r["upper_second_entry"],"NOT_CONNECTED_NEEDS_DESIGN")
    def test_json_never_claims_structural_certification(self):
        self.assertFalse(self.s["agency_boundary"]["code_compliant"])
        self.assertFalse(self.s["agency_boundary"]["structural_engineering_certified"])
        self.assertFalse(self.s["agency_boundary"]["physics_validated"])
    def test_3d_mesh_geometry_is_real_and_consistent(self):
        m,checks=scene(self.s)
        self.assertGreater(len(m.points),9000)
        self.assertGreater(len(m.faces),17000)
        self.assertEqual(len(m.groups),len(m.faces))
        self.assertEqual(len({g for g in m.groups if g.startswith("STAIR_A_TREAD_")}),24)
        self.assertEqual(len({g for g in m.groups if g.startswith("STAIR_B_TREAD_")}),24)
        self.assertEqual(len([g for g in set(m.groups) if "STRUCTURAL_RIBBON" in g]),4)
        self.assertGreater(len([g for g in set(m.groups) if "OVERHEAD_TENSION_MEMBER" in g]),0)
        self.assertTrue(all(all(math.isfinite(x) for x in p) for p in m.points))
        self.assertTrue(all(all(0<=i<len(m.points) for i in f) for f in m.faces))
    def test_obj_export_is_meters_and_deterministic(self):
        m,_=scene(self.s)
        raw=m.obj();self.assertEqual(raw,m.obj())
        self.assertIn(b"Units: meters",raw)
        self.assertIn(b"g STAIR_A_TREAD_01",raw)
        self.assertIn(b"g STAIR_B_TREAD_24",raw)
        vertices=[x for x in raw.decode().splitlines() if x.startswith("v ")]
        self.assertEqual(len(vertices),len(m.points))
        # 15ft nominal floor height is 4.572 meters; highest anchor 27.5ft.
        self.assertGreater(max(float(line.split()[3]) for line in vertices),8.0)
    def test_immutable_receipts_no_image_no_environment(self):
        with tempfile.TemporaryDirectory() as td:
            receipt=build(SOURCE,td)
            obj=pathlib.Path(td)/receipt["obj_file"]
            self.assertEqual(hashlib.sha256(obj.read_bytes()).hexdigest(),receipt["obj_sha256"])
            self.assertEqual(receipt["source_sha256"],hashlib.sha256(SOURCE.read_bytes()).hexdigest())
            self.assertFalse(receipt["human_design_approval"])
            self.assertFalse(receipt["material_render_created"])
            self.assertFalse(receipt["environment_created"])
            self.assertEqual(receipt["paid_calls"],0)
            self.assertIn("Upper B-entry",receipt["hold"])
    def test_delegated_architecture_language_locked(self):
        self.rejected(lambda s:s.__setitem__("design_character","ornate_victorian"))
        self.rejected(lambda s:s.__setitem__("library_style","conventional"))
    def test_open_air_and_balcony_hybrid_support_locked(self):
        self.rejected(lambda s:s["staircase"].__setitem__("open_air",False))
        self.rejected(lambda s:s["balcony"].__setitem__("support","four_pillars"))
    def test_balcony_has_separate_structural_glass_and_guard_solids(self):
        m,_=scene(self.s)
        names=set(m.groups)
        self.assertIn("BALCONY_GLASS_OBSERVATION_PANEL",names)
        self.assertIn("BALCONY_GLAZED_GUARD_INFILL",names)
        self.assertIn("BALCONY_OPAQUE_COMPOSITE_SLAB",names)
    def test_original_fwai_t001_not_modified(self):
        self.assertEqual(SPEC["design_id"],"FWAI-B001")
        self.assertNotIn("FWAI-T001",SOURCE.read_text())
if __name__=="__main__":unittest.main()
