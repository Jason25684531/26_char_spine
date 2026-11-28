"""Spine Editor 薄橋接：偵測安裝、匯入成新版本專案、開啟專案、單一部件圖片熱更新。

.spine 專案檔只由 Spine 本身產生；這裡只呼叫它、檢查結果、留下紀錄。
"""
import os
import re
import shutil
import struct
import subprocess
from datetime import datetime
from pathlib import Path

from . import C2SError, NeedsInput, load_json, save_json

NO_SPINE = "找不到 Spine。安裝並啟用完整版後，設定環境變數 SPINE_EXE 指向 Spine.com，或加上 --spine-exe <Spine.com 路徑>"
UNINSTALL_KEYS = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
EXE_NAMES = "Spine.com", "SpineTrial.com", "Spine.exe", "SpineTrial.exe"  # .com 會等 Spine 結束並把輸出接回主控台


def _read_uninstall():
    """讀 HKLM／HKCU 的 Uninstall 機碼，回傳每個程式的 {DisplayName, DisplayVersion, InstallLocation}。"""
    try:
        import winreg
    except ImportError:
        return []
    found = []
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for path in UNINSTALL_KEYS:
            try:
                root = winreg.OpenKey(hive, path)
            except OSError:
                continue
            for i in range(winreg.QueryInfoKey(root)[0]):
                try:
                    with winreg.OpenKey(root, winreg.EnumKey(root, i)) as k:
                        entry = {}
                        for name in ("DisplayName", "DisplayVersion", "InstallLocation"):
                            try:
                                entry[name] = str(winreg.QueryValueEx(k, name)[0])
                            except OSError:
                                pass
                        found.append(entry)
                except OSError:
                    continue
    return found


def _is_trial(exe):
    return "trial" in Path(exe).name.lower()


def _vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v))


def detect(registry=_read_uninstall, env=None, home=None):
    """回傳 {exe, launcher_version, editor_version, trial, source}。同時有完整版與試用版時用完整版。"""
    env = os.environ if env is None else env
    home = Path.home() if home is None else Path(home)
    found = []  # (exe, launcher_version, source)
    if env.get("SPINE_EXE"):
        found.append((env["SPINE_EXE"], None, "env"))
    for name in EXE_NAMES:
        hit = shutil.which(name, path=env.get("PATH", ""))
        if hit:
            found.append((hit, None, "path"))
    for e in registry():
        if "spine" in e.get("DisplayName", "").lower() and e.get("InstallLocation"):
            loc = Path(e["InstallLocation"].strip().strip('"'))  # 安裝程式寫入的路徑帶引號
            found += [(str(loc / n), e.get("DisplayVersion"), "registry") for n in EXE_NAMES]
    for pf in filter(None, (env.get("ProgramFiles"), env.get("ProgramFiles(x86)"))):
        found += [(str(Path(pf) / d / n), None, "common") for d in ("Spine", "Spine Trial") for n in EXE_NAMES]
    found = [f for f in found if Path(f[0]).is_file()]
    if not found:
        return {"exe": None, "launcher_version": None, "editor_version": None, "trial": False, "source": None}
    exe, launcher, source = next((f for f in found if not _is_trial(f[0])), found[0])
    trial = _is_trial(exe)
    updates = home / ("SpineTrial" if trial else "Spine") / "updates"  # Launcher 下載的 Editor 以版本號為檔名放在這裡
    versions = sorted((p.name for p in updates.glob("*") if _vkey(p.name)), key=_vkey)
    return {"exe": exe, "launcher_version": launcher, "editor_version": versions[-1] if versions else None,
            "trial": trial, "source": source}


def _resolve(exe):
    """回傳 (執行檔, BLOCKED 原因或 None)。"""
    from .spine_exporter import TRIAL_NOTE
    if exe is None:
        exe = detect()["exe"]
    if exe is None:
        return None, NO_SPINE
    return exe, TRIAL_NOTE if _is_trial(exe) else None


def _projects(wd):
    d = Path(wd) / "spine" / "projects"
    return sorted((p for p in d.glob("character_v*.spine") if p.stem[11:].isdigit()), key=lambda p: int(p.stem[11:]))


def import_project(workdir, exe=None):
    """Spine -i character.json -o projects/character_vNNN.spine -r。NNN 取現有最大值加一，不覆蓋任何專案。"""
    from .spine_exporter import _run
    wd = Path(workdir)
    src = wd / "spine" / "character.json"
    if not src.exists():
        raise NeedsInput(f"{wd} 缺少 spine/character.json，請先執行 c2s export")
    exe, blocked = _resolve(exe)
    if blocked:
        return {"status": "BLOCKED", "detail": blocked, "exe": exe}
    existing = _projects(wd)
    n = int(existing[-1].stem[11:]) + 1 if existing else 1
    out = wd / "spine" / "projects" / f"character_v{n:03d}.spine"
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [exe, "-i", str(src), "-o", str(out), "-r"]
    log = out.with_suffix(".import.log")
    code, tail = _run(cmd, log)
    ok = code == 0 and out.is_file() and out.stat().st_size > 0
    result = {"status": "PASS" if ok else "FAIL", "project": str(out), "command": subprocess.list2cmdline(cmd), "log": str(log),
              "detail": f"已建立 {out.name}，之前的版本沒有變動" if ok else f"Spine 匯入失敗（exit={code}）：{tail}"}
    hist_path = out.parent / "history.json"
    hist = load_json(hist_path) if hist_path.exists() else []
    hist.append({"time": datetime.now().isoformat(timespec="seconds"), "project": out.name, "status": result["status"],
                 "exit": code, "command": result["command"], "log": log.name})
    save_json(hist_path, hist)
    return result


def open_project(workdir, project=None, exe=None):
    """用 Spine 開啟指定或最新的專案，不等待 Spine 結束。"""
    projects = [Path(project)] if project else _projects(workdir)
    if not projects or not projects[-1].is_file():
        return {"status": "BLOCKED", "detail": "還沒有 Spine 專案檔：先執行 c2s spine import（需要完整版 Spine）"}
    exe = exe or detect()["exe"]
    if exe is None:
        return {"status": "BLOCKED", "detail": NO_SPINE}
    gui = Path(exe).with_suffix(".exe")
    exe = str(gui) if gui.is_file() else exe  # 開視窗用 .exe，不佔住目前的主控台
    p = subprocess.Popen([exe, str(projects[-1])], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, close_fds=True)
    return {"status": "ok", "project": str(projects[-1]), "exe": exe, "pid": p.pid}


def _png_size(path):
    head = Path(path).read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise C2SError(f"{path} 不是 PNG")
    return struct.unpack(">II", head[16:24])


def _atomic_copy(src, dst):
    tmp = dst.with_name(f".{dst.name}.c2s-tmp")  # 副檔名不是 .png：Spine 監看圖片資料夾時不會把暫存檔當成新圖片
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def sync_image(workdir, part, restore=False):
    """把 layers/<部件>.png 換進 spine/images/，上一版存到 spine/history/<時間>/；只動這一個檔。restore 取回最近一版。"""
    if not re.fullmatch(r"[\w-]+", part):
        raise C2SError(f"部件名稱只能有英數字、底線與連字號，收到 {part!r}")
    wd = Path(workdir)
    dst = wd / "spine" / "images" / f"{part}.png"
    if not dst.exists():
        raise NeedsInput(f"{dst} 不存在：新部件需要先 c2s export 再 c2s spine import")
    history = wd / "spine" / "history"
    if restore:
        saved = sorted(history.glob(f"*/{part}.png"))
        if not saved:
            return {"status": "BLOCKED", "detail": f"{part} 沒有可還原的上一版"}
        _atomic_copy(saved[-1], dst)
        os.replace(saved[-1], saved[-1].with_name(f"{part}.restored.png"))  # 保留檔案、不再當成可還原的版本，下次還原取更早一版
        return {"status": "ok", "part": part, "image": str(dst), "restored_from": str(saved[-1].parent.name)}
    src = wd / "layers" / f"{part}.png"
    if not src.exists():
        raise NeedsInput(f"{src} 不存在")
    if src.read_bytes() == dst.read_bytes():
        return {"status": "unchanged", "part": part, "image": str(dst)}
    if _png_size(src) != _png_size(dst):
        return {"status": "BLOCKED", "detail": f"{part} 尺寸從 {_png_size(dst)} 變成 {_png_size(src)}：附件大小也要改，"
                                               "需要重新匯入（c2s export 後 c2s spine import 產生新版本專案）"}
    keep = history / datetime.now().strftime("%Y%m%d-%H%M%S-%f") / f"{part}.png"
    keep.parent.mkdir(parents=True)
    shutil.copy2(dst, keep)
    _atomic_copy(src, dst)
    return {"status": "ok", "part": part, "image": str(dst), "previous": str(keep)}
