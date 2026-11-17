"""Run all API test cases and write results/api_results.json.

Usage:  python run_tests.py            (all members)
        python run_tests.py M3 M5      (only these members)
Set QA_BASE_URL to test another host (default http://localhost:8080).
"""
import glob, importlib, json, os, sys, traceback
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework import REGISTRY, Ctx, Blocked  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    members = {a.upper() for a in sys.argv[1:]}
    for f in sorted(glob.glob(os.path.join(HERE, "tests_m*.py"))):
        importlib.import_module(os.path.basename(f)[:-3])
    ctx = Ctx()
    results, counts = [], {"Pass": 0, "Fail": 0, "Blocked": 0}
    for tc in REGISTRY:
        if members and tc["member"] not in members:
            continue
        try:
            r = tc["fn"](ctx)
            status, actual = ("Pass" if r.passed else "Fail"), r.actual
        except Blocked as e:
            status, actual = "Blocked", str(e)
        except Exception as e:  # noqa: BLE001
            status, actual = "Blocked", f"Test error: {type(e).__name__}: {e}"
            traceback.print_exc()
        counts[status] += 1
        print(f"[{status:7}] {tc['id']}  {tc['title']}")
        if status != "Pass":
            print(f"           {actual}")
        row = {k: v for k, v in tc.items() if k != "fn"}
        row.update(status=status, actual=actual)
        results.append(row)
    os.makedirs(os.path.join(HERE, "..", "results"), exist_ok=True)
    out = os.path.join(HERE, "..", "results", "api_results.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"executed_at": datetime.now(timezone.utc).isoformat(), "counts": counts,
                   "results": results}, fh, indent=2)
    print(f"\n{counts}  ->  {os.path.normpath(out)}")


if __name__ == "__main__":
    main()
