"""P04.06 — mechanics-first design specification, zero image generation.

Uses only owner-approved FWAI-T001 geometry. All distances are diagrammatic
metres in a single top-view plane; no stresses/torques, orbital dynamics,
thermal loads or real-world manufacturing claims are calculated.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from .geometry import check as check_geometry
from .mechanical import inspect as check_mechanical

APPROVED_SHA = "7bc0379c02632018e78dfbea6eab467071ec0ffe9f97b3c9522c1634bf51b77e"
SCHEMA = "FWAI_MECHANICAL_DETAIL_1"
ARM_COMPONENTS = (
    "TRUSS_ANCHOR", "SHOULDER_JOINT", "PROXIMAL_LINK",
    "ELBOW_JOINT", "DISTAL_LINK", "FABRICATION_TOOL",
)
REQUIRED_SYSTEMS = ("structure", "actuation", "power", "telemetry", "thermal", "service")
PROHIBITED = ("weapon", "turret", "camouflage", "military")


class DetailRejected(ValueError):
    pass


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def create_spec(geometry_path, approval_path):
    gp, ap = Path(geometry_path), Path(approval_path)
    geometry_bytes = gp.read_bytes()
    geometry_hash = sha256(geometry_bytes)
    approval = json.loads(ap.read_text(encoding="utf-8"))
    if geometry_hash != APPROVED_SHA or approval.get("spec_sha256") != APPROVED_SHA:
        raise DetailRejected("Geometry differs from approved immutable owner source")
    decision = approval.get("owner_decisions", {})
    if decision.get("P04.06-GEOMETRY") != "APPROVE":
        raise DetailRejected("Explicit owner geometry approval absent")
    for field in ("MATERIAL_RENDER", "ENVIRONMENT_RENDER", "PUBLISH"):
        if decision.get(field) != "NOT_AUTHORIZED":
            raise DetailRejected("Source owner scope has changed")
    if approval.get("automatic_promotion_allowed") is not False:
        raise DetailRejected("Unexpected automatic promotion authorization")

    geometry = json.loads(geometry_bytes)
    check_geometry(geometry)
    check_mechanical(geometry)
    arms = []
    for i, arm in enumerate(geometry["fabrication_arms"], 1):
        anchor, elbow, tip = arm["joints"]
        first_length = round(_dist(anchor, elbow), 3)
        second_length = round(_dist(elbow, tip), 3)
        arms.append({
            "id": f"ARM-{i:02d}",
            "truss_anchor_id": f"R{i}",
            "joint_coordinates_m": [anchor, elbow, tip],
            "components": list(ARM_COMPONENTS),
            "proximal_link_length_m": first_length,
            "distal_link_length_m": second_length,
            "actuation_concept": {
                "shoulder": "revolute_junction_with_protected_rotary_drive",
                "elbow": "revolute_junction_with_replaceable_bearing_module",
                "tool": "interchangeable_precision_fabrication_end_effector",
            },
            "load_path_description": "tool -> distal link -> elbow -> proximal link -> shoulder -> truss anchor",
            "cable_path_description": "power_bus -> anchor_connector -> shielded_service_loop -> elbow_connector -> tool",
            "service": {
                "method": "isolated_joint_cartridge_exchange",
                "access_from": "truss_mounted_maintenance_carriage",
                "safing": "power_isolated_and_arm_locked_before_service",
            },
            "status": "diagrammatic_proposal_only",
        })
    out = {
        "schema": SCHEMA, "design_id": "FWAI-T001",
        "design_title": "Civilian Orbital Lattice Weaver",
        "geometry_sha256": geometry_hash,
        "owner_acceptance_sha256": sha256(ap.read_bytes()),
        "source_approval_scope": "geometry_approved_only",
        "coordinate_system": "orthographic_top_view_xy_metres",
        "truss_ring_diameter_m": geometry["truss_ring_diameter_m"],
        "arms": arms,
        "service_hatch": {
            "location": "central_hub", "width_m": 2.0,
            "access_description": "human_scale_service_airlock_and_internal_maintenance_corridor",
        },
        "subsystem_interfaces": {
            "structure": "hexagonal_truss_anchor_nodes_R1_to_R6",
            "actuation": "six_independent_two_link_precision_manipulators",
            "power": "conceptual_isolatable_distribution_bus_and_shielded_branch_harnesses",
            "telemetry": "redundant_local_sensing_and_civilian_cooperative_automation",
            "thermal": "six_anchor_radiator_ports_for_future_thermal_design",
            "service": "replaceable_joint_modules_and_crew_access_at_central_hub",
        },
        "design_boundaries": {
            "nonmilitary": True, "weapons_present": False,
            "material_rendering_authorized": False,
            "environment_rendering_authorized": False,
            "api_spend_authorized": False,
            "external_upload_authorized": False,
            "publishing_authorized": False,
            "physics_certified": False, "fea_performed": False,
            "thermal_balance_computed": False, "kinematic_collision_simulated": False,
        },
        "review_state": "PENDING_OWNER_MECHANICAL_DETAIL_REVIEW",
    }
    verify_detail(out, geometry, approval)
    return out


def verify_detail(detail, geometry, approval):
    if detail.get("schema") != SCHEMA or detail.get("design_id") != "FWAI-T001":
        raise DetailRejected("Unsupported mechanical detail identity")
    if detail.get("geometry_sha256") != APPROVED_SHA:
        raise DetailRejected("Approved geometry not cryptographically bound")
    if approval["owner_decisions"]["P04.06-GEOMETRY"] != "APPROVE":
        raise DetailRejected("Approved geometry consent required")
    if detail.get("truss_ring_diameter_m") != geometry["truss_ring_diameter_m"]:
        raise DetailRejected("Truss scale drift")
    arms = detail.get("arms", [])
    if len(arms) != 6 or len({a.get("id") for a in arms}) != 6:
        raise DetailRejected("Six unique functional arms required")
    for n, (arm, reference) in enumerate(zip(arms, geometry["fabrication_arms"]), 1):
        if arm["id"] != f"ARM-{n:02d}" or arm["truss_anchor_id"] != f"R{n}":
            raise DetailRejected("Wrong truss attachment")
        if arm.get("joint_coordinates_m") != reference["joints"]:
            raise DetailRejected("Approved joint geometry changed")
        if tuple(arm.get("components", [])) != ARM_COMPONENTS:
            raise DetailRejected("Missing assembly component")
        calculated = [_dist(reference["joints"][i], reference["joints"][i+1]) for i in range(2)]
        if not math.isclose(arm.get("proximal_link_length_m"), calculated[0], abs_tol=.00051):
            raise DetailRejected("Proximal linkage does not match geometry")
        if not math.isclose(arm.get("distal_link_length_m"), calculated[1], abs_tol=.00051):
            raise DetailRejected("Distal linkage does not match geometry")
        if set(arm.get("actuation_concept", {})) != {"shoulder", "elbow", "tool"}:
            raise DetailRejected("Actuation conceptual interfaces incomplete")
        if "truss anchor" not in arm.get("load_path_description", ""):
            raise DetailRejected("Load transfer path undefined")
        if "shielded_service_loop" not in arm.get("cable_path_description", ""):
            raise DetailRejected("Protected cables missing")
        service = arm.get("service", {})
        if service.get("safing") != "power_isolated_and_arm_locked_before_service":
            raise DetailRejected("Service power lockout missing")
        if service.get("method") != "isolated_joint_cartridge_exchange":
            raise DetailRejected("Joint module replaceability missing")
    if set(detail.get("subsystem_interfaces", {})) != set(REQUIRED_SYSTEMS):
        raise DetailRejected("Missing subsystem interface declaration")
    hatch = detail.get("service_hatch", {})
    if hatch.get("width_m") != geometry["crew_access"]["width_m"] or hatch.get("location") != "central_hub":
        raise DetailRejected("Human-scale maintenance reference changed")
    boundary = detail.get("design_boundaries", {})
    if boundary.get("nonmilitary") is not True or boundary.get("weapons_present") is not False:
        raise DetailRejected("Civilian mission is mandatory")
    protected = ("material_rendering_authorized", "environment_rendering_authorized",
                 "api_spend_authorized", "external_upload_authorized", "publishing_authorized",
                 "physics_certified", "fea_performed", "thermal_balance_computed",
                 "kinematic_collision_simulated")
    if any(boundary.get(k) is not False for k in protected):
        raise DetailRejected("Unapproved rendering/engineering capability asserted")
    if detail.get("review_state") != "PENDING_OWNER_MECHANICAL_DETAIL_REVIEW":
        raise DetailRejected("Human mechanical approval must remain pending")
    # Provenance-bound semantic tests, not real structural analysis.
    return {"status": "MECHANICAL_DETAIL_CONTRACT_PASS", "arms": 6,
            "linked_sections": 12, "subsystems": len(REQUIRED_SYSTEMS),
            "geometry_unchanged": True, "owner_mechanical_signoff": False,
            "physical_feasibility": "NOT_ASSESSED", "rendering_authorized": False}


def write_details(geometry_path, approval_path, output_dir):
    detail = create_spec(geometry_path, approval_path)
    dest = Path(output_dir); dest.mkdir(parents=True, exist_ok=True)
    data = canonical(detail)
    detail_path = dest / "FWAI-T001_mechanical_detail.json"
    detail_path.write_bytes(data)
    receipt = {
        "schema": "FWAI_MECHANICAL_DETAIL_RECEIPT_1",
        "design_id": "FWAI-T001", "approved_geometry_sha256": APPROVED_SHA,
        "detail_sha256": sha256(data),
        "detail_file": detail_path.name, "owner_mechanical_approval": "PENDING",
        "material_rendering": "BLOCKED", "environment_rendering": "BLOCKED",
        "publishing": "BLOCKED", "paid_provider_calls": 0,
    }
    (dest / "FWAI-T001_mechanical_detail_receipt.json").write_text(
        json.dumps(receipt, indent=2), encoding="utf-8"
    )
    return receipt


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("geometry");p.add_argument("approval");p.add_argument("output")
    a=p.parse_args()
    print(json.dumps(write_details(a.geometry, a.approval, a.output),indent=2))
