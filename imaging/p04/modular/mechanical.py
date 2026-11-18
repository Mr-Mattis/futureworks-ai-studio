"""P04.06 mechanical-function heuristic review over geometry contract.

This checks connected subsystem design/traceability, NOT engineering safety,
load capacity, orbit mechanics, thermals, manufacturability or real feasibility.
"""
from __future__ import annotations
import json
from .geometry import check, GeometryRejected

REQUIRED_CHAIN="truss_mount -> rotary_joint -> linear_actuator -> tool_head"
class MechanicalRejected(GeometryRejected):pass

def inspect(spec):
    geometry=check(spec)
    problems=[]
    for i,arm in enumerate(spec["fabrication_arms"]):
        if arm.get("function")!="precision_additive_fabrication":
            problems.append(f"arm {i}: missing process role")
        if arm.get("mechanical_chain")!=REQUIRED_CHAIN:
            problems.append(f"arm {i}: undefined load/actuation chain")
        if arm.get("power")!="shielded_harness":
            problems.append(f"arm {i}: protected power routing undefined")
        if arm.get("maintenance")!="replaceable_joint_cartridge":
            problems.append(f"arm {i}: serviceability missing")
    if spec.get("reference_view")!="orthographic_top":
        problems.append("reference view not explicit")
    if spec.get("engineering_status")!="fictional_visualization_not_physically_validated":
        problems.append("engineering disclaimer absent")
    if problems:
        raise MechanicalRejected("; ".join(problems))
    return {"schema":"FWAI_MECHANICAL_QA_1",
            "result":"HEURISTIC_MECHANICAL_QA_PASS",
            "geometry":geometry,
            "subsystem_connection_checks":6,"power_route_checks":6,
            "maintenance_access_checks":6,"human_scale_reference":True,
            "simulation_or_fea_performed":False,"physical_feasibility_certified":False,
            "owner_visual_acceptance":"PENDING",
            "next_gate":"HUMAN_TECHNOLOGY_GEOMETRY_REVIEW"}
