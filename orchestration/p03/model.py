"""Explicitly local-only P03 planning model adapters.

Replay is a synthetic integration fixture derived from previous *real* P02
Ollama artifacts. It is not a fresh inference or real research.
Ollama calls only the owner's installed local endpoint, no paid provider.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import urllib.request
import urllib.error

from engine import REPO, Rejected, roles

OLLAMA_URL = "http://host.docker.internal:11434/api/chat"


class ReplayModel:
    """Controlled test-only replay of recorded role-native model candidates."""
    def __call__(self, role, ctx):
        if role not in roles.records():
            raise Rejected("Unknown role")
        path = REPO / "agents/p02_roles/live-runs" / (role + ".json")
        record = json.loads(path.read_text())
        if record["role"] != role or record["handoff"]["dispatch_performed"]:
            raise Rejected("Non-test model evidence")
        if any(record["handoff"]["authorization"].values()):
            raise Rejected("Authorization injected into recorded evidence")
        result = copy.deepcopy(record["handoff"]["candidate"])
        # Explicit synthetic substitution to make older role-specific reference
        # artifacts address the SAME immutable concept for an orchestrator test.
        if "project_id" in result:
            result["project_id"] = ctx["project_id"]
        return result


class OllamaModel:
    """Fresh real local Ollama inference, with no external network endpoint choice."""
    def __init__(self, timeout_seconds=240):
        if timeout_seconds < 10 or timeout_seconds > 600:
            raise Rejected("Bounded Ollama inference timeout required")
        self.timeout = timeout_seconds

    def __call__(self, role, ctx):
        record = roles.registry()[role]
        schema = roles.schema(role)
        instructions = (record["output_instructions"] +
                        "\nP03 controlled development ONLY. No tools or permission. "
                        "Return exactly ONE JSON object adhering to the supplied "
                        "output_schema; no extra root fields. All claims without "
                        "sources remain unverified; quality cannot pass without "
                        "actual inspections; likeness requires consent; missing "
                        "provider rates require explicit disclosure and owner "
                        "approval, even with zero spend. 5 Creative Director scenes "
                        "S01–S05, 72s each and 144–192 narration words per scene. "
                        "Never invent a provider result, spending authorization, "
                        "approved SOP, real footage or analytics.")
        data = {
            "model": "qwen3.6:latest", "stream": False, "think": False,
            "format": schema,
            "options": {"temperature": 0, "num_predict": 6000, "num_ctx": 16384},
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps({
                    "context": ctx["role_input"], "output_schema": schema,
                    "canonical_project_id": ctx["project_id"],
                    "content_type": ctx["manifest"]["content_type"],
                }, ensure_ascii=True, default=str)},
            ],
        }
        request = urllib.request.Request(
            OLLAMA_URL, data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                payload = json.loads(resp.read(1024 * 1024))
        except (TimeoutError, urllib.error.URLError, ValueError) as exc:
            raise Rejected("Local Ollama unavailable or invalid response") from exc
        try:
            candidate = json.loads(payload["message"]["content"])
        except (KeyError, TypeError, ValueError) as exc:
            raise Rejected("Local Ollama output is not a JSON role object") from exc
        return roles.checked_output(role, candidate, ctx)
