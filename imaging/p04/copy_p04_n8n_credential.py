"""Copy P04 isolated n8n Custom Auth credential JSON to Windows clipboard.

Run only as: python3 script.py | clip.exe
Refuses interactive stdout to avoid accidentally printing a bearer secret.
Never stores or uploads a second copy.
"""
import json,pathlib,sys,stat
if sys.stdout.isatty():
    raise SystemExit("Refusing to show a secret in terminal. Pipe to clip.exe.")
key=pathlib.Path.home()/".config/futureworks-ai-studio/secrets/p04_n8n_gateway_token"
if not key.is_file() or stat.S_IMODE(key.stat().st_mode)!=0o600:
    raise SystemExit("Missing or unsafe local P04 credential file")
token=key.read_text().strip()
if len(token)<32:raise SystemExit("Invalid isolated token")
sys.stdout.write(json.dumps({"headers":{"Authorization":"Bearer "+token}}))
