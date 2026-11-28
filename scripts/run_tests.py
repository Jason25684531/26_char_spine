"""分批執行自動化測試：一個測試檔一批，每批寫檢查點，可續跑；可用記憶體低於下限時先存進度再停。

python scripts/run_tests.py --name v1.2.1            從頭跑
python scripts/run_tests.py --name v1.2.1 --resume   只跑還沒通過的批次
結束碼：0 全部通過、1 有失敗、75 因記憶體不足停止（進度已存，之後用 --resume 接續）。
檢查點：output/test_runs/<名稱>.json（每批的通過數、失敗清單、秒數、pytest 程序的記憶體峰值）。
"""
import argparse
import ctypes
import json
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path


def free_mb():
    """可用實體記憶體（MB）。非 Windows 讀不到時回傳很大的數，不擋執行。"""
    if sys.platform != "win32":
        return 1 << 30
    class Mem(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
            (n, ctypes.c_ulonglong) for n in ("ullTotalPhys", "ullAvailPhys", "ullTotalPageFile", "ullAvailPageFile",
                                              "ullTotalVirtual", "ullAvailVirtual", "ullAvailExtendedVirtual")]
    m = Mem()
    m.dwLength = ctypes.sizeof(m)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys // (1 << 20)


def peak_mb(proc):
    """已結束的子程序的工作集峰值（只含 pytest 本身，不含它再啟動的子程序）。"""
    if sys.platform != "win32":
        return None
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
                                           "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    c = Counters()
    c.cb = ctypes.sizeof(c)
    get = ctypes.windll.psapi.GetProcessMemoryInfo
    get.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
    return c.PeakWorkingSetSize // (1 << 20) if get(int(proc._handle), ctypes.byref(c), c.cb) else None


def run_batch(root, rel):
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "r.xml"
        t0 = time.time()
        proc = subprocess.Popen([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", rel, f"--junitxml={xml}"],
                                cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        tail = proc.communicate()[0][-1500:]
        rec = {"seconds": round(time.time() - t0, 1), "peak_mb": peak_mb(proc), "exit_code": proc.returncode}
        if not xml.exists():  # pytest 沒跑完（收集錯誤、被終止）
            return rec | {"status": "failed", "passed": 0, "failed": [f"{rel}（pytest 沒有產生結果）"], "tail": tail}
        cases = list(ET.parse(xml).getroot().iter("testcase"))
        bad = [f"{rel}::{c.get('name')}" for c in cases if c.find("failure") is not None or c.find("error") is not None]
        skipped = sum(1 for c in cases if c.find("skipped") is not None)
        rec.update(status="failed" if bad or proc.returncode else "passed", passed=len(cases) - len(bad) - skipped,
                   skipped=skipped, failed=bad)
        if bad:
            rec["tail"] = tail
        return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--min-free-mb", type=int, default=400, help="開始下一批前的可用記憶體下限")
    a = ap.parse_args()
    root = Path(a.root)
    path = root / "output" / "test_runs" / f"{a.name}.json"
    state = json.loads(path.read_text(encoding="utf-8")) if a.resume and path.exists() else {"batches": {}}
    state.pop("stopped", None)

    def save():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    for f in sorted((root / "tests").glob("test_*.py")):
        rel = f"tests/{f.name}"
        if state["batches"].get(rel, {}).get("status") == "passed":
            continue
        if free_mb() < a.min_free_mb:
            state["stopped"] = "low_memory"
            save()
            print(f"可用記憶體 {free_mb()} MB 低於下限 {a.min_free_mb} MB，已存進度並停止。"
                  f"之後接續：python scripts/run_tests.py --name {a.name} --resume")
            return 75
        state["batches"][rel] = {"status": "running"}  # 這一批執行中被終止時，續跑會重跑它
        save()
        state["batches"][rel] = run_batch(root, rel)
        save()
        b = state["batches"][rel]
        print(f"{rel}: {b['status']} {b['passed']} passed, {len(b['failed'])} failed, {b['seconds']}s, peak {b['peak_mb']} MB", flush=True)
    passed = sum(b.get("passed", 0) for b in state["batches"].values())
    failed = [t for b in state["batches"].values() for t in b.get("failed", [])]
    state["summary"] = {"passed": passed, "failed": len(failed), "skipped": sum(b.get("skipped", 0) for b in state["batches"].values())}
    save()
    print(f"合計：{passed} passed, {len(failed)} failed" + "".join(f"\n  FAILED {t}" for t in failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
