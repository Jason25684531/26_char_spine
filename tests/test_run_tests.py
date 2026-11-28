"""分批測試執行器：檢查點、續跑、記憶體下限。"""
import json
import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).parents[1] / "scripts" / "run_tests.py"


def project(tmp_path):
    """三個測試檔；每個被執行時在 runs.log 記一行。"""
    t = tmp_path / "tests"
    t.mkdir()
    for name, body in (("a", "assert True"), ("b", "assert True"), ("c", "assert 1 == 2")):
        (t / f"test_{name}.py").write_text(
            f"from pathlib import Path\n\ndef test_{name}():\n"
            f"    with open(Path(__file__).parents[1] / 'runs.log', 'a') as f:\n        f.write('{name}\\n')\n    {body}\n",
            encoding="utf-8")
    return tmp_path


def run(root, *args):
    return subprocess.run([sys.executable, str(RUNNER), "--root", str(root), "--name", "t", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def state(root):
    return json.loads((root / "output" / "test_runs" / "t.json").read_text(encoding="utf-8"))


def test_batches_and_summary(tmp_path):
    root = project(tmp_path)
    r = run(root)
    assert r.returncode == 1, r.stdout + r.stderr  # test_c 失敗
    s = state(root)["batches"]
    assert s["tests/test_a.py"]["status"] == "passed" and s["tests/test_a.py"]["passed"] == 1
    assert s["tests/test_c.py"]["status"] == "failed" and s["tests/test_c.py"]["failed"] == ["tests/test_c.py::test_c"]
    assert "2 passed" in r.stdout and "1 failed" in r.stdout


def test_resume_only_runs_unfinished_batches(tmp_path):
    """第二批執行中被終止（狀態停在 running）：續跑不重跑第一批，仍涵蓋全部測試。"""
    root = project(tmp_path)
    (root / "tests" / "test_c.py").write_text("def test_c():\n    assert True\n", encoding="utf-8")
    out = root / "output" / "test_runs"
    out.mkdir(parents=True)
    (out / "t.json").write_text(json.dumps({"batches": {
        "tests/test_a.py": {"status": "passed", "passed": 1, "failed": [], "seconds": 0.1},
        "tests/test_b.py": {"status": "running"}}}), encoding="utf-8")
    r = run(root, "--resume")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (root / "runs.log").read_text().split() == ["b"]  # a 沒有重跑；c 被改成不寫 log
    assert {k: v["status"] for k, v in state(root)["batches"].items()} == {
        "tests/test_a.py": "passed", "tests/test_b.py": "passed", "tests/test_c.py": "passed"}
    assert "3 passed" in r.stdout


def test_stops_and_saves_when_memory_is_low(tmp_path):
    root = project(tmp_path)
    r = run(root, "--min-free-mb", "99999999")
    assert r.returncode == 75
    assert not (root / "runs.log").exists()  # 沒有啟動任何一批
    assert "--resume" in r.stdout and state(root)["stopped"] == "low_memory"
