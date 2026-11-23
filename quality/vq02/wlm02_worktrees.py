"""WLM-02 read-only Git worktree discovery and review flags.
Never removes branches, worktrees, files, or n8n workflows.
"""
import pathlib,subprocess,json,datetime
OUT=pathlib.Path.home()/"Documents"/"futureworks-maintenance"/"WLM02_worktrees_readonly.json"
def call(args,timeout=25):
    p=subprocess.run(["wsl.exe","-d","Ubuntu","--",*args],capture_output=True,text=True,timeout=timeout)
    if p.returncode not in (0,1):raise RuntimeError("git read-only command failed: "+p.stderr[:200])
    return p
def main():
    home=call(["printenv","HOME"]).stdout.strip()
    repo=home+"/futureworks-studio/futureworks-ai-studio"
    records=[]
    raw=call(["git","-C",repo,"worktree","list","--porcelain"]).stdout
    for block in raw.strip().split("\n\n"):
        row={}
        for ln in block.splitlines():
            key,_,val=ln.partition(" ")
            row[key]=val
        if not row.get("worktree"):continue
        loc=row["worktree"]
        p=call(["git","-C",loc,"status","--porcelain"])
        dirty=bool(p.stdout.strip())
        merged=call(["git","-C",repo,"merge-base","--is-ancestor",row["HEAD"],"main"])
        records.append({"path":loc,"head":row.get("HEAD"),"branch":row.get("branch"),"detached":("detached" in row),
            "dirty":dirty,"commit_reachable_from_main":merged.returncode==0,
            "disposition":"PROTECT_ACTIVE_OR_UNVERIFIED" if dirty or merged.returncode!=0 else "REVIEW_MERGED_NOT_SAFE_TO_DELETE"})
    report={"schema":"FWAI_WLM02_GIT_READONLY_V1","timestamp_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "dry_run":True,"delete_enabled":False,"worktree_count":len(records),
      "dirty_count":sum(x["dirty"] for x in records),"worktrees":records}
    OUT.write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!="worktrees"},indent=2))
    print("REPORT",OUT)
if __name__=="__main__":main()
