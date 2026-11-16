"""P02.02–P02.10 offline role validation boundary. No dispatch or model clients.

Contracts are pinned to the existing P01 registry and the inspected n8n
development inventory. This intentionally DOES NOT publish/approve anything.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[2]
INVENTORY = Path(__file__).with_name("baseline-workflow-inventory.json")
REGISTRY = REPO / "contracts/agent-result/v1.0.0/agent-registry.json"


class Rejected(ValueError):
    pass


def records():
    entries = json.loads(INVENTORY.read_text())["roles"]
    return {r["role"]: r for r in entries}


def registry():
    return {r["key"]: r for r in json.loads(REGISTRY.read_text())}


def schema(role):
    """The source n8n parser schema, locked down at the role-output root."""
    if role == "creative_director":
        # The active production workflow emits a *manifest formatter* object,
        # not the required P01.02 Creative Director role-native planning payload.
        # Never mutate that live workflow to resolve this distinction.
        required = ("project_id", "working_title", "opening_hook", "logline",
                    "closing_cta", "disclosure_note", "sections", "scenes",
                    "shorts_ideas", "open_questions", "metadata_draft",
                    "content_type", "target_duration_seconds")
        properties = {
            k: {"type": "array"} if k in ("sections", "scenes", "shorts_ideas", "open_questions")
            else {"type": "object"} if k == "metadata_draft"
            else {"type": "integer", "minimum": 1} if k == "target_duration_seconds"
            else {"type": "string", "minLength": 1}
            for k in required
        }
        properties["content_type"]["enum"] = ["REAL_BUILD", "AI_CONCEPT", "HYBRID"]
        properties["scenes"]["items"] = {
            "type": "object", "additionalProperties": False,
            "required": ["scene_id", "description", "narration", "visual_intent", "duration_seconds"],
            "properties": {
                "scene_id": {"type": "string", "pattern": "^S[0-9]{2,3}$"},
                "description": {"type": "string", "minLength": 1},
                "narration": {"type": "string", "minLength": 1},
                "visual_intent": {"type": "string", "minLength": 1},
                "duration_seconds": {"type": "integer", "minimum": 1},
            },
        }
        candidate = {"type": "object", "required": list(required),
                     "properties": properties, "additionalProperties": False}
    else:
        candidate = copy.deepcopy(records()[role]["parserSchema"])
        candidate["additionalProperties"] = False
    Draft202012Validator.check_schema(candidate)
    return candidate


def checked_output(role, output, context):
    """Untrusted model output: exact role, scope, identity and fail-closed policy."""
    item = records()[role]
    if not isinstance(output, dict) or not isinstance(context, dict):
        raise Rejected("Expected one output object and one input context")
    problems = list(Draft202012Validator(schema(role)).iter_errors(output))
    if problems:
        raise Rejected("Role schema rejected: " + problems[0].message)
    if context.get("scope") not in ("episode", "studio"):
        raise Rejected("Invalid scope")
    if context["scope"] == "episode":
        if output.get("project_id") != context.get("project_id"):
            raise Rejected("Project identity changed")
        ref = context.get("input_manifest")
        if not isinstance(ref, dict) or ref.get("project_id") != context["project_id"]:
            raise Rejected("Invalid canonical manifest reference")
    else:
        if context.get("input_manifest") is not None:
            raise Rejected("Studio scope cannot carry a manifest")
    if role in ("growth_strategist", "sop_knowledge") and context["scope"] != "studio":
        raise Rejected("Studio role called with episode scope")
    if role not in ("growth_strategist", "sop_knowledge") and context["scope"] != "episode":
        raise Rejected("Episode role called with studio scope")
    inp = context.get("role_input")
    if not isinstance(inp, dict):
        raise Rejected("Missing typed role_input")
    if role == "research_agent":
        if not inp.get("sources") and output.get("verified_claims"):
            raise Rejected("Verified claims invented without evidence")
        if not output.get("unverified_claims"):
            raise Rejected("Unverified claims must be preserved")
    if role == "growth_strategist":
        if not inp.get("video_metrics") and output.get("observed_patterns"):
            raise Rejected("Metrics were invented without analytics")
        if not output.get("data_gaps"):
            raise Rejected("Missing analytics disclosure")
    if role == "sop_knowledge":
        if output.get("owner_approval_required") is not True:
            raise Rejected("SOP modifications require owner approval")
    if role == "avatar_director":
        if not inp.get("approved_asset_ids") and not output.get("missing_assets"):
            raise Rejected("Unapproved identity assets must block")
        if not inp.get("avatar_profile") and not output.get("required_consents"):
            raise Rejected("Missing presenter consent information")
    if role == "budget_controller":
        if output.get("currency") != "USD" or output.get("approval_required") is not True:
            raise Rejected("Budget estimates never authorize spending")
        if not inp.get("provider_rates") and not output.get("missing_rates"):
            raise Rejected("Unknown rates must be disclosed")
    if role == "quality_control":
        if not inp.get("ffprobe_report") and output.get("overall_verdict") == "pass":
            raise Rejected("QC pass asserted without inspection")
    if role == "editing_supervisor":
        if not inp.get("media_inspection") and output.get("manual_review_required") is not True:
            raise Rejected("Unobserved edits require manual review")
    if role == "visual_director":
        scene_ids = set(inp.get("scene_ids", []))
        shots = output.get("shots", [])
        if not shots:
            raise Rejected("Visual plan requires shots")
        if scene_ids and any(s.get("scene_id") not in scene_ids for s in shots if isinstance(s, dict)):
            raise Rejected("Unknown shot scene_id")
    if role == "creative_director":
        scenes = output.get("scenes", [])
        ids = [s.get("scene_id") for s in scenes]
        if len(scenes) != 5 or ids != ["S01", "S02", "S03", "S04", "S05"]:
            raise Rejected("Creative scene identity/order changed")
        if sum(s.get("duration_seconds", 0) for s in scenes) != output.get("target_duration_seconds"):
            raise Rejected("Narrative scene durations do not sum to target")
        if output.get("content_type") != inp.get("content_type"):
            raise Rejected("Content classification changed")
    return copy.deepcopy(output)


def envelope(role, candidate, context, *, manifest_path=None):
    """Produce blocked canonical P01 handoff; never an operational success."""
    if role not in records() or role not in registry():
        raise Rejected("Unknown role")
    output = checked_output(role, candidate, context)
    started = datetime.now(timezone.utc).isoformat()
    if context["scope"] == "episode":
        from importlib.util import spec_from_file_location, module_from_spec
        path = Path(manifest_path) if manifest_path is not None else None
        if path is None or not path.is_file() or not path.resolve().is_relative_to(REPO):
            raise Rejected("Missing exact checkout-local manifest file")
        ref = context["input_manifest"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
            raise Rejected("Manifest byte identity changed")
    else:
        if manifest_path is not None:
            raise Rejected("Studio cannot receive episode manifest")
    result = {
        "schema_version": "1.0.0",
        "result_id": "dev-" + uuid4().hex,
        "agent": {"role": role, "instance_id": registry()[role]["id"]},
        "scope": context["scope"],
        "input_manifest": context["input_manifest"],
        "execution": {"run_id": context["run_id"], "attempt": context["attempt"],
                      "started_at": started, "finished_at": started, "status": "blocked"},
        "output": output,
        "validation": {"status": "passed", "findings": []},
        "errors": [],
        "blockers": ["Independent approval and canonical worker handoff remain required."],
        "authorization": {"production_approved": False, "spend_authorized": False,
                          "publish_authorized": False},
    }
    import importlib.util
    validator_path = REPO / "contracts/agent-result/v1.0.0/validate_agent_result.py"
    spec = importlib.util.spec_from_file_location("p02_result_validation", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors = module.validate(result, manifest_path, REPO / "contracts/production-manifest/v1.0.0")
    if errors:
        raise Rejected("Canonical envelope rejected: " + "; ".join(errors))
    return result
