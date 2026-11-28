"""組出 Spine JSON，並在有完整版 Spine CLI 時匯入成可編輯的 .spine 專案。

JSON 結構依官方 spine-runtimes 4.2／4.3 的 spineboy 匯出檔比對：只使用兩版相同的子集
（bones、slots、region attachment、rotate/translate/scale timeline、絕對座標 bezier）。
"""
import shutil
import subprocess
from pathlib import Path

from . import NeedsInput, load_json, save_json, spine_bridge
from .spine_bridge import _is_trial

DEFAULT_SPINE_VERSION = "4.3.26"  # 試用版 Launcher 實際下載的 Editor 版本（~/SpineTrial/updates）；用 --spine-version 配合實際匯入的 Editor
TRIAL_NOTE = ("偵測到的是 Spine 試用版：2026-11-23 實測 SpineTrial.com（Launcher 4.3.08，Editor 4.3.26）的 CLI 沒有 -i/-o/-r/-e 參數，"
              "官方也說明試用版不能儲存專案與匯出資料，無法產生 .spine")


def build_skeleton(workdir, spine_version=DEFAULT_SPINE_VERSION):
    wd = Path(workdir)
    for needed, cmd in (("rig.json", "c2s rig"), ("animations.json", "c2s animate")):
        if not (wd / needed).exists():
            raise NeedsInput(f"{wd} 缺少 {needed}，請先執行 {cmd}")
    rig, anims = load_json(wd / "rig.json"), load_json(wd / "animations.json")
    bx, by, bw, bh = rig["bbox"]
    ox, oy = rig["origin"]
    bones = [{k: v for k, v in b.items() if k != "world" and (k in ("name", "parent") or v)} for b in rig["bones"]]
    return {
        "skeleton": {"spine": spine_version, "x": round(bx - ox, 2), "y": round(oy - (by + bh), 2),
                     "width": bw, "height": bh, "images": "./images/", "audio": ""},
        "bones": bones,
        "slots": rig["slots"],
        "skins": [{"name": "default", "attachments": {
            s["name"]: {s["attachment"]: {k: v for k, v in rig["attachments"][s["attachment"]].items()
                                          if v or k in ("width", "height")}} for s in rig["slots"]}}],
        "animations": anims,
    }


def find_spine():
    """回傳 (執行檔路徑或 None, 是否為試用版)。偵測順序見 spine_bridge.detect。"""
    d = spine_bridge.detect()
    return d["exe"], d["trial"]


def _run(cmd, log, timeout=300):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, errors="replace")
    except subprocess.TimeoutExpired:
        log.write_text(f"$ {subprocess.list2cmdline(cmd)}\nTIMEOUT after {timeout}s", encoding="utf-8")
        return None, f"逾時（{timeout} 秒）"
    except OSError as e:
        log.write_text(f"$ {subprocess.list2cmdline(cmd)}\n無法執行：{e}", encoding="utf-8")
        return None, f"無法執行 {cmd[0]}：{e}"
    log.write_text(f"$ {subprocess.list2cmdline(cmd)}\nexit={r.returncode}\n--- stdout ---\n{r.stdout}\n--- stderr ---\n{r.stderr}", encoding="utf-8")
    return r.returncode, (r.stdout + r.stderr).strip()[-600:]


def import_to_spine(json_path, spine_path, exe=None):
    """用 Spine CLI 匯入 JSON → .spine，再匯出回 JSON 比對。回傳 {status, detail, ...}。"""
    json_path, spine_path = Path(json_path), Path(spine_path)
    if exe is None:
        exe, _ = find_spine()
    if exe is None:
        return {"status": "BLOCKED", "detail": "找不到 Spine CLI。安裝並啟用完整版後，設定環境變數 SPINE_EXE 指向 Spine.com，或執行 c2s export --spine-exe <Spine.com 路徑>"}
    if _is_trial(exe):
        return {"status": "BLOCKED", "detail": TRIAL_NOTE, "exe": exe}
    out = spine_path.parent
    spine_path.unlink(missing_ok=True)
    cmd = [exe, "-i", str(json_path), "-o", str(spine_path), "-r", spine_path.stem]
    code, tail = _run(cmd, out / "spine_import.log")
    result = {"exe": exe, "command": subprocess.list2cmdline(cmd), "log": str(out / "spine_import.log")}
    if code != 0 or not spine_path.exists() or spine_path.stat().st_size == 0:
        return {**result, "status": "FAIL", "detail": f"Spine CLI 匯入失敗（exit={code}）：{tail}"}
    result.update(status="PASS", detail=f"已建立 {spine_path}（{spine_path.stat().st_size} bytes）")

    # 往返驗證：把 .spine 再匯出成 JSON，確認骨頭、插槽、動畫都還在
    rt = out / "roundtrip"
    shutil.rmtree(rt, ignore_errors=True)
    code, tail = _run([exe, "-i", str(spine_path), "-o", str(rt), "-e", "json"], out / "spine_roundtrip.log")
    exported = sorted(rt.glob("*.json")) if rt.exists() else []
    if code != 0 or not exported:
        result["roundtrip"] = {"status": "FAIL", "detail": f"重新匯出失敗（exit={code}）：{tail}"}
        return result
    a, b = load_json(json_path), load_json(exported[0])
    names = lambda d, k: sorted(x["name"] for x in d.get(k, []))
    diffs = [k for k in ("bones", "slots") if names(a, k) != names(b, k)]
    if sorted(a["animations"]) != sorted(b.get("animations", {})):
        diffs.append("animations")
    result["roundtrip"] = {"status": "FAIL" if diffs else "PASS",
                           "detail": ("不一致：" + ", ".join(diffs)) if diffs else "骨頭、插槽、動畫名稱與原始 JSON 一致"}
    return result


def export(workdir, spine_version=DEFAULT_SPINE_VERSION, spine_exe=None):
    wd = Path(workdir)
    data = build_skeleton(wd, spine_version)
    (wd / "quality" / "quality_report.json").unlink(missing_ok=True)  # 重新匯出後需要重跑 c2s refine 才有有效的品質報告
    out = wd / "spine"
    images = out / "images"
    shutil.rmtree(images, ignore_errors=True)
    images.mkdir(parents=True)
    for slot in data["slots"]:
        shutil.copyfile(wd / "layers" / f"{slot['attachment']}.png", images / f"{slot['attachment']}.png")
    json_path = save_json(out / "character.json", data)
    report = {"json": str(json_path), "spine_version": spine_version,
              "spine_import": import_to_spine(json_path, out / "character.spine", spine_exe)}
    save_json(wd / "export_report.json", report)
    return {"status": "ok", **report}
