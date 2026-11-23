"""Read-only authenticated Runway account health probe. No uploads or paid requests."""
import json, pathlib, urllib.request, urllib.error, os
key_path=pathlib.Path.home()/".config"/"futureworks-ai-studio"/"secrets"/"runway_api_key"
if not key_path.is_file(): raise SystemExit("RUNWAY_KEY_MISSING")
key=key_path.read_text().strip()
request=urllib.request.Request("https://api.dev.runwayml.com/v1/organization",
    method="GET", headers={"Authorization":"Bearer "+key,"X-Runway-Version":"2024-11-06"})
try:
    with urllib.request.urlopen(request,timeout=20) as response: data=json.load(response)
    print(json.dumps({"status":"AUTHENTICATED","creditBalance":data.get("creditBalance"),"tier_models":list(data.get("tier",{}).get("models",{}))[:15],"paid_calls":0},indent=2))
except urllib.error.HTTPError as e:
    print(json.dumps({"status":"AUTH_FAILURE_OR_API_ERROR","http_status":e.code,"paid_calls":0}))
except Exception as e:
    print(json.dumps({"status":"NETWORK_OR_CONFIGURATION_ERROR","type":type(e).__name__,"paid_calls":0}))
