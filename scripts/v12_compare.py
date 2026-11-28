"""v1.1 與 v1.2 輸出的前後比較（同一張圖、各自的工作目錄）。所有數字都從輸出檔重算，不讀報告裡的文字。

python scripts/v12_compare.py <標籤>=<v1.1 工作目錄>,<v1.2 工作目錄> [...] [--out 報告.md]
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from character_to_spine import load_json  # noqa: E402
from character_to_spine.animation_builder import duration  # noqa: E402
from character_to_spine.preview import world_matrices  # noqa: E402


def motion(wd, anim):
    """相對角色高度的百分比：頭部上下起伏、手（手臂骨頭末端近似為骨頭原點加附件中心）相對身體的最大位移、腳的最大下沉。"""
    skel = load_json(wd / "spine" / "character.json")
    if anim not in skel["animations"]:
        return None
    h = skel["skeleton"]["height"]
    att = skel["skins"][0]["attachments"]
    setup = world_matrices(skel)
    ts = np.arange(0, duration(skel["animations"][anim]) + 1e-9, 1 / 30)
    bones = {b["name"] for b in skel["bones"]}
    arms = [b for b in bones if b.startswith("arm_") and b != "arm_extra"]
    legs = [b for b in bones if b.startswith("leg_")]
    head_y, hand, sink = [], 0.0, 0.0
    for t in ts:
        w = world_matrices(skel, anim, t)
        head_y.append(w["head"][1, 2])
        for a in arms:  # 手相對身體（扣掉 body 骨頭的移動）；手的位置近似為附件中心的兩倍（骨頭原點在肩膀）
            c = att[a][a]
            tip = [2 * c.get("x", 0), 2 * c.get("y", 0), 1]
            rel_now = np.linalg.inv(w["body"]) @ w[a] @ tip
            rel_0 = np.linalg.inv(setup["body"]) @ setup[a] @ tip
            hand = max(hand, float(np.hypot(*(rel_now - rel_0)[:2])))
        for leg in legs:
            sink = max(sink, setup[leg][1, 2] - w[leg][1, 2])
    return {"period_s": round(float(ts[-1]), 2), "head_bob_pct": round(100 * (max(head_y) - min(head_y)) / h, 2),
            "hand_vs_body_pct": round(100 * hand / h, 2), "foot_sink_pct": round(100 * sink / h, 2)}


def summary(wd):
    wd = Path(wd)
    meta = load_json(wd / "metadata.json")
    q = load_json(wd / "quality" / "quality_report.json") if (wd / "quality" / "quality_report.json").exists() else {}
    tuning = [v for an in q.get("tuning", {}).values() for v in an.values()]
    by = lambda st: sorted(e["name"] for e in meta["parts"] if e["status"] == st)  # noqa: E731
    return {"needs_manual": by("needs_manual"), "ai_repaired": by("ai_repaired"),
            "unresolved": sorted({f"{a['kind']}:{a['subject']}" for a in q.get("unresolved", [])}),
            "min_tuning": min(tuning) if tuning else 1.0,
            "idle": motion(wd, "idle"), "happy": motion(wd, "happy")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    rows, data = [], {}
    for pair in a.pairs:
        label, dirs = pair.split("=", 1)
        old, new = (summary(d) for d in dirs.split(","))
        data[label] = {"v1.1": old, "v1.2": new}
        f = lambda s, an, k: (s[an] or {}).get(k, "—")  # noqa: E731
        rows.append(f"| {label} | {len(old['needs_manual'])} → {len(new['needs_manual'])} | {', '.join(new['ai_repaired']) or '—'} "
                    f"| {len(old['unresolved'])} → {len(new['unresolved'])} | ×{old['min_tuning']} → ×{new['min_tuning']} "
                    f"| {f(old, 'idle', 'period_s')} → {f(new, 'idle', 'period_s')} s "
                    f"| {f(old, 'idle', 'head_bob_pct')} → {f(new, 'idle', 'head_bob_pct')} "
                    f"| {f(old, 'happy', 'hand_vs_body_pct')} → {f(new, 'happy', 'hand_vs_body_pct')} "
                    f"| {f(old, 'happy', 'foot_sink_pct')} → {f(new, 'happy', 'foot_sink_pct')} |")
    table = ("| 角色 | 人工補畫部件 | AI 補圖通過 | 品質未解決 | 自動縮幅最小係數 | Idle 週期 | Idle 頭部起伏 % | Happy 手相對身體 % | Happy 腳下沉 % |\n"
             "|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows))
    print(table)
    if a.out:
        Path(a.out).write_text(table + "\n\n```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")


if __name__ == "__main__":
    main()
