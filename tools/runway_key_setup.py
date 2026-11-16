#!/usr/bin/env python3
"""Local WSL-only Runway API secret setup; never calls Runway or prints secrets.

This does NOT enable any paid operation or inject a credential into n8n Docker.
"""
from __future__ import annotations
import argparse
import getpass
import os
from pathlib import Path
import stat
import tempfile

STORE = Path.home() / ".config" / "futureworks-ai-studio" / "secrets"
KEY_FILE = STORE / "runway_api_key"


def status() -> int:
    if not KEY_FILE.exists():
        print("RUNWAY_CREDENTIAL=NOT_CONFIGURED; no paid calls enabled")
        return 1
    if KEY_FILE.is_symlink():
        print("RUNWAY_CREDENTIAL=REJECTED_SYMLINK")
        return 1
    meta = KEY_FILE.stat()
    if not stat.S_ISREG(meta.st_mode) or stat.S_IMODE(meta.st_mode) != 0o600:
        print("RUNWAY_CREDENTIAL=UNSAFE_PERMISSIONS; expected 0600")
        return 1
    if stat.S_IMODE(STORE.stat().st_mode) != 0o700:
        print("RUNWAY_CREDENTIAL=UNSAFE_DIRECTORY; expected 0700")
        return 1
    if not KEY_FILE.read_bytes().strip():
        print("RUNWAY_CREDENTIAL=EMPTY")
        return 1
    print("RUNWAY_CREDENTIAL=LOCALLY_STORED_AND_PERMISSION_CHECKED")
    print("Paid Runway calls and n8n integration remain DISABLED.")
    return 0


def configure(replace: bool) -> int:
    if KEY_FILE.exists() and not replace:
        print("Key already exists. Use --replace to rotate it intentionally.")
        return status()
    old_mask = os.umask(0o077)
    try:
        STORE.mkdir(parents=True, exist_ok=True)
        STORE.chmod(0o700)
        if KEY_FILE.is_symlink():
            raise RuntimeError("Refusing symlink destination")
        key = getpass.getpass("Paste Runway Developer API key (input hidden): ").strip()
        if len(key) < 16 or len(key) > 1024 or any(c.isspace() for c in key):
            raise ValueError("Credential seems malformed (required 16-1024 non-whitespace chars)")
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=STORE, prefix=".runway-", delete=False
        ) as temporary:
            temp = Path(temporary.name)
            temporary.write(key + "\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        try:
            temp.chmod(0o600)
            temp.replace(KEY_FILE)
        finally:
            temp.unlink(missing_ok=True)
    finally:
        os.umask(old_mask)
    return status()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--status", action="store_true", help="Check permissions without showing secret")
    mode.add_argument("--replace", action="store_true", help="Rotate existing secret after hidden input")
    args = parser.parse_args()
    if args.status:
        return status()
    return configure(args.replace)


if __name__ == "__main__":
    raise SystemExit(main())
