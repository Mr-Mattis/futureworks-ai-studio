"""Read-only P03 local development dashboard CLI (no secrets/media)."""
from __future__ import annotations

import argparse
import json

from engine import Studio


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--database", required=True)
    p.add_argument("--project", default="FWAI-EP-0001")
    p.add_argument("--run-id", required=True)
    args = p.parse_args()
    print(json.dumps(Studio(args.database).dashboard(args.project, args.run_id),
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
