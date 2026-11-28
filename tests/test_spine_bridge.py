"""spec: spine-bridge（以假的 Spine 執行檔測試包裝邏輯；不是真實 Spine 匯入驗證）"""
import hashlib
import json
import sys
import time
from pathlib import Path

import pytest
from PIL import Image

from character_to_spine import C2SError, cli, load_json, spine_bridge, spine_exporter

FAKE = r'''import json, sys
from pathlib import Path
a = sys.argv[1:]
Path(sys.argv[0]).with_name("calls.jsonl").open("a", encoding="utf-8").write(json.dumps(a) + "\n")
if "-o" in a:
    out = Path(a[a.index("-o") + 1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("fake project from " + a[a.index("-i") + 1], encoding="utf-8")
print("fake spine done")
'''


def fake_spine(dirpath, name="Spine"):
    """假的 Spine.com：Python 腳本包成 .cmd，記下收到的參數，-o 時寫出輸出檔。"""
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "fake_spine.py").write_text(FAKE, encoding="utf-8")
    cmd = dirpath / f"{name}.cmd"
    cmd.write_text(f'@"{sys.executable}" "{dirpath / "fake_spine.py"}" %*\r\n', encoding="utf-8")
    return cmd


def calls(cmd):
    log = cmd.with_name("calls.jsonl")
    return [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []


def png(path, size, color):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", size, color).save(path)


@pytest.fixture
def wd(tmp_path):
    w = tmp_path / "work"
    (w / "spine").mkdir(parents=True)
    (w / "spine" / "character.json").write_text('{"skeleton": {}}', encoding="utf-8")
    for part, size in (("head", (40, 30)), ("arm_r", (20, 50))):
        png(w / "spine" / "images" / f"{part}.png", size, (255, 0, 0, 255))
        png(w / "layers" / f"{part}.png", size, (255, 0, 0, 255))
    return w


def tree(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


# ---- detect ----

def test_detect_from_registry_with_quoted_location(tmp_path):
    loc = tmp_path / "Soft" / "Spine Trial"
    loc.mkdir(parents=True)
    (loc / "SpineTrial.com").write_bytes(b"")
    updates = tmp_path / "home" / "SpineTrial" / "updates"
    updates.mkdir(parents=True)
    for v in ("4.3.9", "4.3.26"):
        (updates / v).write_bytes(b"")  # 實機上每個 Editor 版本是一個檔案
    reg = [{"DisplayName": "Other App", "InstallLocation": str(tmp_path)},
           {"DisplayName": "Spine Trial", "DisplayVersion": "4.3.08", "InstallLocation": f'"{loc}"'}]
    d = spine_bridge.detect(registry=lambda: reg, env={}, home=tmp_path / "home")
    assert d == {"exe": str(loc / "SpineTrial.com"), "launcher_version": "4.3.08", "editor_version": "4.3.26",
                 "trial": True, "source": "registry"}


def test_detect_prefers_env_then_full_over_trial(tmp_path):
    trial, full = tmp_path / "Spine Trial", tmp_path / "Spine"
    for d, exe in ((trial, "SpineTrial.com"), (full, "Spine.com")):
        d.mkdir()
        (d / exe).write_bytes(b"")
    reg = [{"DisplayName": "Spine Trial", "InstallLocation": str(trial)}, {"DisplayName": "Spine", "InstallLocation": str(full)}]
    d = spine_bridge.detect(registry=lambda: reg, env={}, home=tmp_path)
    assert d["exe"] == str(full / "Spine.com") and d["trial"] is False
    mine = tmp_path / "custom" / "Spine.com"
    mine.parent.mkdir()
    mine.write_bytes(b"")
    d = spine_bridge.detect(registry=lambda: reg, env={"SPINE_EXE": str(mine)}, home=tmp_path)
    assert d["exe"] == str(mine) and d["source"] == "env"


def test_detect_nothing(tmp_path):
    d = spine_bridge.detect(registry=lambda: [], env={}, home=tmp_path)
    assert d["exe"] is None and d["source"] is None


def test_find_spine_keeps_shape(monkeypatch):
    monkeypatch.setattr(spine_bridge, "detect", lambda: {"exe": "X/SpineTrial.com", "trial": True})
    assert spine_exporter.find_spine() == ("X/SpineTrial.com", True)


# ---- import ----

def test_import_args_versions_and_no_overwrite(wd, tmp_path):
    exe = fake_spine(tmp_path / "bin")
    r1 = spine_bridge.import_project(wd, exe=str(exe))
    v1 = wd / "spine" / "projects" / "character_v001.spine"
    assert r1["status"] == "PASS" and Path(r1["project"]) == v1 and v1.exists()
    assert calls(exe) == [["-i", str(wd / "spine" / "character.json"), "-o", str(v1), "-r"]]
    assert "fake spine done" in Path(r1["log"]).read_text(encoding="utf-8")
    first = v1.read_bytes()
    v1.write_bytes(first + b" hand edited")  # 使用者在 Spine 裡改過、存檔
    r2 = spine_bridge.import_project(wd, exe=str(exe))
    assert r2["status"] == "PASS" and Path(r2["project"]).name == "character_v002.spine"
    assert v1.read_bytes() == first + b" hand edited"
    hist = load_json(wd / "spine" / "projects" / "history.json")
    assert [h["project"] for h in hist] == ["character_v001.spine", "character_v002.spine"]


def test_import_continues_after_highest_version(wd, tmp_path):
    projects = wd / "spine" / "projects"
    projects.mkdir()
    (projects / "character_v007.spine").write_bytes(b"old")  # 測試用的舊專案（只當作已存在的檔案）
    r = spine_bridge.import_project(wd, exe=str(fake_spine(tmp_path / "bin")))
    assert Path(r["project"]).name == "character_v008.spine" and (projects / "character_v007.spine").read_bytes() == b"old"


def test_import_trial_blocked_creates_nothing(wd, tmp_path):
    exe = fake_spine(tmp_path / "bin", "SpineTrial")
    r = spine_bridge.import_project(wd, exe=str(exe))
    assert r["status"] == "BLOCKED" and "試用版" in r["detail"]
    assert calls(exe) == [] and not list(wd.rglob("*.spine"))


def test_import_without_spine_blocked(wd, monkeypatch):
    monkeypatch.setattr(spine_bridge, "detect", lambda: {"exe": None, "trial": False})
    r = spine_bridge.import_project(wd)
    assert r["status"] == "BLOCKED" and "SPINE_EXE" in r["detail"] and not list(wd.rglob("*.spine"))


def test_import_failure_is_fail_with_log(wd, tmp_path):
    bad = tmp_path / "Spine.cmd"
    bad.write_text("@echo boom\r\n@exit /b 3\r\n")
    r = spine_bridge.import_project(wd, exe=str(bad))
    assert r["status"] == "FAIL" and "exit=3" in r["detail"]
    assert "boom" in Path(r["log"]).read_text(encoding="utf-8")
    assert load_json(wd / "spine" / "projects" / "history.json")[-1]["status"] == "FAIL"


# ---- open ----

def test_open_without_project_blocked(wd, tmp_path):
    exe = fake_spine(tmp_path / "bin")
    r = spine_bridge.open_project(wd, exe=str(exe))
    assert r["status"] == "BLOCKED" and "c2s spine import" in r["detail"] and calls(exe) == []


def test_open_launches_newest_project(wd, tmp_path):
    exe = fake_spine(tmp_path / "bin")
    spine_bridge.import_project(wd, exe=str(exe))
    spine_bridge.import_project(wd, exe=str(exe))
    r = spine_bridge.open_project(wd, exe=str(exe))
    assert r["status"] == "ok"
    for _ in range(100):
        if len(calls(exe)) == 3:
            break
        time.sleep(0.1)
    assert calls(exe)[-1] == [str(wd / "spine" / "projects" / "character_v002.spine")]


# ---- sync ----

def test_sync_replaces_only_that_part_and_restores(wd):
    before = tree(wd / "spine")
    old = (wd / "spine" / "images" / "arm_r.png").read_bytes()
    png(wd / "layers" / "arm_r.png", (20, 50), (0, 0, 255, 255))
    r = spine_bridge.sync_image(wd, "arm_r")
    assert r["status"] == "ok"
    after = tree(wd / "spine")
    changed = {k for k in before if before[k] != after.get(k)}
    assert changed == {str(Path("images/arm_r.png"))}
    assert (wd / "spine" / "images" / "arm_r.png").read_bytes() == (wd / "layers" / "arm_r.png").read_bytes()
    assert [p.name for p in (wd / "spine" / "images").iterdir()] == ["arm_r.png", "head.png"], "不留暫存檔"
    saved = list((wd / "spine" / "history").rglob("arm_r.png"))
    assert len(saved) == 1 and saved[0].read_bytes() == old
    assert spine_bridge.sync_image(wd, "arm_r")["status"] == "unchanged"
    assert len(list((wd / "spine" / "history").rglob("arm_r.png"))) == 1, "重複同步不多存一份"

    r = spine_bridge.sync_image(wd, "arm_r", restore=True)
    assert r["status"] == "ok" and (wd / "spine" / "images" / "arm_r.png").read_bytes() == old
    assert tree(wd / "spine" / "images") == {k[len("images") + 1:]: v for k, v in before.items() if k.startswith("images")}
    assert spine_bridge.sync_image(wd, "arm_r", restore=True)["status"] == "BLOCKED", "沒有更早的版本"


def test_sync_refuses_size_change(wd):
    before = tree(wd / "spine")
    png(wd / "layers" / "arm_r.png", (24, 50), (0, 0, 255, 255))
    r = spine_bridge.sync_image(wd, "arm_r")
    assert r["status"] == "BLOCKED" and "重新匯入" in r["detail"]
    assert tree(wd / "spine") == before


def test_sync_rejects_path_like_part(wd):
    with pytest.raises(C2SError):
        spine_bridge.sync_image(wd, "../layers/arm_r")


# ---- CLI ----

def test_cli_spine_exit_codes(wd, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    exe = fake_spine(tmp_path / "bin")
    assert cli.main(["spine", "import", "-w", str(wd), "--spine-exe", str(exe)]) == 0
    trial = fake_spine(tmp_path / "trialbin", "SpineTrial")
    assert cli.main(["spine", "import", "-w", str(wd), "--spine-exe", str(trial)]) == 2
    png(wd / "layers" / "head.png", (40, 30), (0, 255, 0, 255))
    assert cli.main(["spine", "sync", "-w", str(wd), "--part", "head"]) == 0
    assert cli.main(["spine", "sync", "-w", str(wd), "--part", "head", "--restore"]) == 0
    assert cli.main(["spine", "sync", "-w", str(wd)]) == 1, "sync 要指定 --part"
    capsys.readouterr()
