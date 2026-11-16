"""Controlled P03 CLI. No production clients or paid-provider capability.

By default replays prior real P02 synthetic outputs; --fresh-local-ollama
is an explicit owner-authorized local inference test, not a cloud API.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine import REPO, Studio
from model import ReplayModel, OllamaModel

MANIFEST = REPO / "contracts/production-manifest/v1.0.0/example.valid.json"
PLAN = json.loads((REPO / "agents/executive_producer/reconciliation/execution-54.json"
                   ).read_text())["handoff"]["candidate"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--brief", default="The PC That Became a Robot — "
                        "a fictional computer transformation concept, not real hardware.")
    parser.add_argument("--fresh-local-ollama", action="store_true")
    args = parser.parse_args()
    studio = Studio(args.database)
    receipt = studio.submit(MANIFEST, PLAN, args.run_id, args.brief)
    model = OllamaModel() if args.fresh_local_ollama else ReplayModel()
    report = studio.drive(receipt["project_id"], args.run_id, model)
    out = dict(mode="fresh_local_ollama" if args.fresh_local_ollama else
               "synthetic_replay_from_verified_P02_outputs",
               receipt=receipt, dashboard=report)
    print(json.dumps(out, indent=2))
    return 0 if report["state"] == "awaiting_approval" else 2


if __name__ == "__main__":
    raise SystemExit(main())
