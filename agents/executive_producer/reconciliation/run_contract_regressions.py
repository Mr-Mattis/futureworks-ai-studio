"""Run all six committed P01 unittest suites in the offline development namespace."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[3]
failed = False
for name in ("production-manifest", "agent-result", "job-state",
             "data-tables", "revision-guard", "recovery-policy"):
    folder = root / "contracts" / name / "v1.0.0"
    test, = folder.glob("test_*.py")
    result = subprocess.run([sys.executable, "-B", str(test)],
                            cwd=folder, capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(name + ":")
    print("\n".join(output.splitlines()[-4:]) if result.returncode == 0 else output)
    failed |= result.returncode != 0
raise SystemExit(int(failed))
