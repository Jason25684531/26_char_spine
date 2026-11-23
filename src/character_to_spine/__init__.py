"""Character-to-Spine：2D 角色圖片 → 分層 PNG → Spine 骨架與動畫。"""
import json
from pathlib import Path

__version__ = "0.1.0"


class C2SError(Exception):
    """流程失敗。"""


class NeedsInput(C2SError):
    """流程需要 Agent 或人工補資料後才能接續（不是程式錯誤）。"""


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
