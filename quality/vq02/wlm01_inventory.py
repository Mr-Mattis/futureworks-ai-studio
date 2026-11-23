"""Future Works AI Studio WLM-01: read-only local inventory. Never deletes or moves files."""
from __future__ import annotations
import csv, hashlib, json, os, pathlib, datetime, collections
HOME = pathlib.Path.home()
ROOTS = [HOME/"Documents"/"futureworks-p04-data", HOME/"Documents"/"futureworks-p05-data"]
OUT = HOME/"Documents"/"futureworks-maintenance"
PROTECTED = {"character-library", "FWAI-M001_EP001_PREPRODUCTION", "images"}
TEMP_NAMES = {"__pycache__", ".pytest_cache", ".ruff_cache"}
HASH_LIMIT = 128 * 1024 * 1024
def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()
def analyze():
    files, errors = [], []
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    for root in ROOTS:
        if not root.is_dir():
            errors.append({"root":str(root),"error":"missing root"})
            continue
        for parent, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = [x for x in dirs if not (pathlib.Path(parent)/x).is_symlink()]
            for name in names:
                p = pathlib.Path(parent)/name
                try:
                    if p.is_symlink(): continue
                    st = p.stat()
                    rel = p.relative_to(root)
                    top = rel.parts[0] if rel.parts else ""
                    suffix = p.suffix.lower()
                    protected = top in PROTECTED or suffix in {".blend", ".blend1", ".otioz", ".mp4"} or any(s in name.lower() for s in ("approved", "master", "manifest", "receipt", "evidence", "reference"))
                    cache = any(part in TEMP_NAMES for part in rel.parts)
                    age_days = max(0, (now-st.st_mtime)/86400)
                    label = "PROTECTED" if protected else "CACHE_REVIEW" if cache else "REVIEW_ONLY"
                    files.append({"root":str(root),"relative_path":str(rel),"bytes":st.st_size,
                        "age_days":round(age_days,1),"category":label,
                        "sha256":sha256(p) if st.st_size <= HASH_LIMIT else None})
                except (OSError, PermissionError) as e:
                    errors.append({"path":str(p),"error":type(e).__name__})
    byhash=collections.defaultdict(list)
    for row in files:
        if row["sha256"]:byhash[(row["bytes"],row["sha256"])].append(row["root"]+"\\"+row["relative_path"])
    duplicates=[{"bytes_each":k[0],"sha256":k[1],"paths":v} for k,v in byhash.items() if len(v)>1]
    totals=collections.Counter()
    for x in files:totals[x["category"]]+=1
    report={"schema":"FWAI_WLM_01_READ_ONLY_V1", "generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "dry_run":True,"automatic_delete_enabled":False,"move_enabled":False,
      "roots":[str(x) for x in ROOTS],"file_count":len(files),
      "total_bytes":sum(x["bytes"] for x in files),"categories":dict(totals),
      "duplicate_groups":duplicates,"errors":errors,
      "policy":"No file is automatically eligible for deletion. Cache candidates require owner approval and dependency verification."}
    OUT.mkdir(exist_ok=True)
    with (OUT/"WLM01_report.json").open("w",encoding="utf-8") as f:json.dump(report,f,indent=2)
    with (OUT/"WLM01_inventory.csv").open("w",newline="",encoding="utf-8") as f:
        fields=["root","relative_path","bytes","age_days","category","sha256"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(files)
    print(json.dumps({k:v for k,v in report.items() if k not in ("duplicate_groups","errors")},indent=2))
    print("duplicate_groups:",len(duplicates),"errors:",len(errors))
    print("reports:",OUT/"WLM01_report.json",OUT/"WLM01_inventory.csv")
if __name__=="__main__":analyze()
