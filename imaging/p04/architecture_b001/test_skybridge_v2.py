"""FWAI-B001 right-hand elevated skybridge: fail-closed offline geometry tests.

These are parametric topology/visual-model checks, NOT engineering certification,
a genuine 3D swept collision test, building code approval or public egress signoff.
"""
import copy,hashlib,json,math,pathlib,tempfile,unittest
from imaging.p04.architecture_b001 import parametric_3d as v1
from imaging.p04.architecture_b001.parametric_3d_v2 import (
    V1_SHA,SkybridgeRejected,validate,bridge_model,build
)
HERE=pathlib.Path(__file__).resolve().parent
SPEC=HERE/"FWAI-B001_geometry_v2.json"
BASE=json.loads(SPEC.read_text())

class SkybridgeContractTests(unittest.TestCase):
    def setUp(self):self.s=copy.deepcopy(BASE)
    def reject(self,callback):
        callback(self.s)
        with self.assertRaises(SkybridgeRejected):validate(self.s)
    def test_original_user_loved_v1_is_unchanged(self):
        orig=HERE/"FWAI-B001_geometry_v1.json"
        self.assertEqual(v1.digest(orig),V1_SHA)
        self.assertEqual(self.s["staircase"],json.loads(orig.read_text())["staircase"])
        self.assertEqual(self.s["balcony"],json.loads(orig.read_text())["balcony"])
    def test_original_staircase_geometry_kept_12ft_and_two_strands(self):
        q=validate(self.s)
        self.assertEqual(q["stairs"],2)
        self.assertEqual(q["total_tread_solids"],48)
        self.assertEqual(q["stair_outer_diameter_unchanged_ft"],12.0)
        self.assertEqual(q["bridge_arc_turn_degrees"],180)
        self.assertFalse(q["human_design_approval"])
    def test_peripheral_clear_width_and_envelope(self):
        q=validate(self.s)
        self.assertEqual(q["bridge_clear_radial_width_ft"],3.5)
        self.assertEqual(q["outer_bridge_diameter_ft"],21.2)
        self.assertGreater(q["minimum_non_entry_horizontal_bridge_to_stair_ribbon_gap_ft"],1.0)
    def test_bridge_right_hand_side_only(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("side","left"))
    def test_reject_too_narrow_corridor(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("outer_radius_ft",9.0))
    def test_reject_corridor_too_close_to_stair(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("inner_radius_ft",6.5))
    def test_reject_large_unreviewed_span(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("outer_radius_ft",15))
    def test_reject_steep_nonlevel_skybridge(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("deck_top_z_ft",13))
    def test_reject_missing_radial_B_walk_connection(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("entry_B_radial_connector_y_ft",[22.2,22.3]))
    def test_reject_missing_near_A_threshold(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("entry_A_threshold_y_ft",[0,2]))
    def test_reject_unvalidated_handguard_aperture(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("guard_gap_outer_B_rail_segments",2))
    def test_reject_guard_post_intruding_into_walk_width(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("guard_center_offset_ft",0.01))
    def test_rail_guard_offsets_keep_nominal_walkway_clear(self):
        p=self.s["upper_transfer"]
        self.assertGreater(p["guard_center_offset_ft"],0.07)
        self.assertAlmostEqual(p["outer_radius_ft"]-p["inner_radius_ft"],3.5)
    def test_reject_auto_structural_signoff(self):
        self.reject(lambda s:s["upper_transfer"].__setitem__("engineering_status","CERTIFIED"))
    def test_reject_owner_visual_acceptance_without_review(self):
        self.reject(lambda s:s.__setitem__("review_status","APPROVED"))
    def test_reject_original_stair_helix_phase_change(self):
        self.reject(lambda s:s["staircase"].__setitem__("entry_phase_radians_B",0))
    def test_reject_original_balcony_size_change(self):
        self.reject(lambda s:s["balcony"].__setitem__("length_ft",15))
    def test_reject_environment_generation(self):
        self.reject(lambda s:s["render_permissions"].__setitem__("environment_rendering",True))
    def test_reject_material_generation_and_external_api(self):
        for setting in ("material_rendering","image_generation","external_upload","paid_api","publish"):
            self.reject(lambda s,x=setting:s["render_permissions"].__setitem__(x,True))
    def test_model_has_actual_overhead_supports_rails_and_connected_deck(self):
        mesh,q=bridge_model(self.s)
        groups=set(mesh.groups)
        for name in ("PERIPHERAL_SKYBRIDGE_CURVED_DECK",
                     "SKYBRIDGE_INNER_TORSION_EDGE_GIRDER",
                     "SKYBRIDGE_OUTER_TORSION_EDGE_GIRDER",
                     "SKYBRIDGE_INNER_GUARD_HANDRAIL",
                     "SKYBRIDGE_OUTER_GUARD_HANDRAIL",
                     "SKYBRIDGE_RADIAL_UNDERDECK_LATTICE",
                     "TRANSFER_TO_HELIX_B_RADIAL_LANDING",
                     "TRANSFER_TO_HELIX_A_ENTRY_THRESHOLD",
                     "SKYBRIDGE_OVERHEAD_SUSPENSION_TIE_PROXY",
                     "STAIR_B_OUTER_RIBBON_CUT_PORTAL_FACE",
                     "SKYBRIDGE_TO_HELIX_B_PORTAL_GUSSET_PROXY",
                     "STAIR_B_ENTRY_FLARED_GUARD_RETURN"):
            self.assertIn(name,groups)
        self.assertEqual(len({g for g in groups if g.startswith("STAIR_A_TREAD_")}),24)
        self.assertEqual(len({g for g in groups if g.startswith("STAIR_B_TREAD_")}),24)
        self.assertGreater(len(mesh.points),14000)
        self.assertGreater(len(mesh.faces),26000)
        self.assertEqual(len(mesh.faces),len(mesh.groups))
        self.assertEqual(q["bridge_deck_sweep_sections"],48)
        self.assertTrue(all(all(math.isfinite(a) for a in p) for p in mesh.points))
        self.assertTrue(all(all(0<=i<len(mesh.points) for i in face) for face in mesh.faces))
    def test_upper_B_guard_gap_is_modeled_not_just_a_flag(self):
        _,q=bridge_model(self.s)
        self.assertEqual(q["bridge_entry_guard_aperture"]["STAIR_B_OUTER_CURVED_HANDRAIL"],240)
        self.assertEqual(q["bridge_entry_guard_aperture"]["STAIR_B_OUTER_GUARD_STANCHIONS"],84)
        self.assertEqual(q["bridge_entry_guard_aperture"]["STAIR_B_OUTER_STRUCTURAL_RIBBON"],82)
        width_by_arc=10*(2*math.pi/96)*self.s["staircase"]["outer_support_radius_ft"]
        self.assertGreater(width_by_arc,3.5)
    def test_both_entries_2d_plan_continuity_only(self):
        q=validate(self.s)
        self.assertTrue(q["near_entrance_overlaps_shared_landing"])
        self.assertTrue(q["far_connector_overlaps_bridge_and_helix_B_entry"])
        self.assertEqual(q["upper_second_entry"],"CONNECTED_IN_PRELIMINARY_XY_TOPOLOGY_ONLY")
        self.assertFalse(q["full_3d_interference_validated"])
        self.assertFalse(q["load_path_certified"])
    def test_sources_deterministically_produce_3d_obj_receipt_without_images(self):
        with tempfile.TemporaryDirectory() as td:
            a=build(SPEC,td)
            b=build(SPEC,td)
            self.assertEqual(a,b)
            fn=pathlib.Path(td)/a["obj_file"]
            self.assertEqual(hashlib.sha256(fn.read_bytes()).hexdigest(),a["obj_sha256"])
            self.assertEqual(a["spec_sha256"],hashlib.sha256(SPEC.read_bytes()).hexdigest())
            self.assertEqual(a["paid_api_calls"],0)
            self.assertFalse(a["materials_rendered"])
            self.assertFalse(a["environment_rendered"])
            self.assertFalse(a["external_upload"])
            self.assertFalse(a["publishing"])
            self.assertFalse(a["owner_visual_acceptance"])
            self.assertEqual(a["full_collision_qa"],"NOT_DONE")
            self.assertEqual(a["stair_code_compliance"],"NOT_VALIDATED")
if __name__=="__main__":unittest.main()
