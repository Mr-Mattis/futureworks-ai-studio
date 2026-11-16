"""Minimal offline canonical encoding shared by the signed P04 review gate."""
import json
class Rejected(ValueError):
    pass
def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=True,
                      allow_nan=False).encode()
