"""檢查實際輸出內容，不只看程式有沒有報錯。每個檢查項目的狀態：PASS / FAIL / BLOCKED / NOT_TESTED。"""
from pathlib import Path

import numpy as np
from PIL import Image

from . import NeedsInput, load_json, save_json
from .animation_builder import CHANNELS, duration
from .image_processor import composite, masked_mae, part_mask
from .preview import render_setup_pose

# 骨架初始姿勢算圖與圖層重組在前景範圍內的平均差異上限（0~1）。
# 合成角色實測 < 0.01；任一附件偏移 15px 或旋轉方向錯誤都會遠超過此值。
SETUP_POSE_MAX_MAE = 0.02
HAPPY_MIN_SECONDS = 2.0


def validate(workdir):
    wd = Path(workdir)
    json_path = wd / "spine" / "character.json"
    if not json_path.exists():
        raise NeedsInput(f"{wd} 尚未匯出，請先執行 c2s export")
    skel, meta = load_json(json_path), load_json(wd / "metadata.json")
    checks = []
    add = lambda name, problems, ok="": checks.append(
        {"check": name, "status": "FAIL" if problems else "PASS", "detail": "; ".join(problems) if problems else ok})

    bones = [b["name"] for b in skel.get("bones", [])]
    p = [f"重複的骨頭 {n}" for n in set(bones) if bones.count(n) > 1]
    if not bones or "parent" in skel["bones"][0]:
        p.append("第一根骨頭必須是沒有 parent 的 root")
    for i, b in enumerate(skel.get("bones", [])[1:], 1):
        if b.get("parent") not in bones[:i]:
            p.append(f"{b['name']} 的 parent {b.get('parent')!r} 必須排在它前面")
    add("bones", p, f"{len(bones)} 根骨頭，階層順序正確")

    skin = skel["skins"][0]["attachments"] if skel.get("skins") else {}
    slots = skel.get("slots", [])
    p = [f"重複的插槽 {s['name']}" for s in slots if [x["name"] for x in slots].count(s["name"]) > 1]
    p += [f"插槽 {s['name']} 的骨頭 {s['bone']} 不存在" for s in slots if s["bone"] not in bones]
    p += [f"插槽 {s['name']} 的附件 {s.get('attachment')} 不在 default skin" for s in slots
          if s.get("attachment") not in skin.get(s["name"], {})]
    if not slots:
        p.append("沒有任何插槽")
    add("slots", p, f"{len(slots)} 個插槽都對應到骨頭與附件")

    p = []
    for slot_name, atts in skin.items():
        for att_name, att in atts.items():
            img_path = wd / "spine" / "images" / f"{att.get('path', att_name)}.png"
            if not img_path.exists():
                p.append(f"缺少圖片 {img_path.name}")
                continue
            img = Image.open(img_path).convert("RGBA")
            if img.size != (att["width"], att["height"]):
                p.append(f"{img_path.name} 實際尺寸 {img.size} 與附件 {att['width']}x{att['height']} 不符")
            if np.array(img)[..., 3].max() == 0:
                p.append(f"{img_path.name} 是全透明的")
    add("image_references", p, "所有附件圖片存在、尺寸相符且不是空白")

    anims = skel.get("animations", {})
    p = [] if "idle" in anims else ["缺少動畫 idle"]
    for name, anim in anims.items():
        if not anim.get("bones"):
            p.append(f"{name} 沒有任何骨頭關鍵影格")
        for bone, tls in anim.get("bones", {}).items():
            if bone not in bones:
                p.append(f"{name}: 骨頭 {bone} 不存在")
            for tl, keys in tls.items():
                times = [k.get("time", 0) for k in keys]
                if tl not in CHANNELS:
                    p.append(f"{name}/{bone}: 未知的 timeline {tl}")
                    continue
                if len(keys) < 2:
                    p.append(f"{name}/{bone}/{tl}: 關鍵影格少於 2 個")
                if times != sorted(times) or len(set(times)) != len(times):
                    p.append(f"{name}/{bone}/{tl}: 時間沒有遞增")
                for k in keys:
                    c = k.get("curve")
                    if c is not None and c != "stepped" and len(c) != 4 * len(CHANNELS[tl]):
                        p.append(f"{name}/{bone}/{tl}: curve 應有 {4 * len(CHANNELS[tl])} 個數字，實際 {len(c)}")
    if "happy" in anims and duration(anims["happy"]) < HAPPY_MIN_SECONDS:
        p.append(f"happy 長度 {duration(anims['happy'])} 秒，不足 {HAPPY_MIN_SECONDS} 秒")
    add("animations", p, "；".join(f"{n} {duration(a)} 秒、{sum(len(k) for t in a['bones'].values() for k in t.values())} 個關鍵影格"
                                  for n, a in anims.items()))

    # 用 Spine JSON 與 spine/images 把初始姿勢重新算一次圖，和「原圖在部件範圍內的像素」比對。
    # 一次抓到：骨頭／附件座標換算錯誤、圖層順序錯誤、匯出的圖片內容錯誤（換錯圖、翻轉、損毀）。
    if not any(c["status"] == "FAIL" for c in checks):
        source = np.array(Image.open(wd / "source_rgba.png").convert("RGBA"))
        h, w = source.shape[:2]
        assigned = np.zeros((h, w), bool)
        for part in load_json(wd / "parts.json")["parts"]:
            assigned |= part_mask(part, (h, w))
        source[..., 3] = np.where(assigned, source[..., 3], 0)
        mae = masked_mae(render_setup_pose(wd), composite([(source, 0, 0)], (w, h)))
        add("setup_pose", [f"骨架初始姿勢與原圖（部件範圍內）差異 {mae:.4f} 超過 {SETUP_POSE_MAX_MAE}"] if mae > SETUP_POSE_MAX_MAE else [],
            f"骨架初始姿勢與原圖（部件範圍內）差異 {mae:.4f}")
    else:
        checks.append({"check": "setup_pose", "status": "NOT_TESTED", "detail": "前面的檢查失敗，未進行算圖比對"})

    manual = [e["name"] for e in meta["parts"] if e["status"] == "needs_manual"]
    checks.append({"check": "manual_repairs", "status": "BLOCKED" if manual else "PASS",
                   "detail": ("等待人工修補：" + ", ".join(manual) + "（見 repair_tasks.md）") if manual else "沒有待人工修補的圖層"})

    report_path = wd / "export_report.json"
    imp = load_json(report_path)["spine_import"] if report_path.exists() else {"status": "NOT_TESTED", "detail": "沒有 export_report.json"}
    checks.append({"check": "spine_import", "status": imp["status"], "detail": imp["detail"]})
    rt = imp.get("roundtrip", {"status": "NOT_TESTED", "detail": "未建立 .spine，無法往返驗證"})
    checks.append({"check": "spine_roundtrip", "status": rt["status"], "detail": rt["detail"]})
    checks.append({"check": "spine_editable", "status": "NOT_TESTED",
                   "detail": "需要在 Spine Editor 內人工開啟專案並修改關鍵影格確認，程式無法代為宣稱"})

    statuses = [c["status"] for c in checks]
    overall = next(s for s in ("FAIL", "BLOCKED", "NOT_TESTED", "PASS") if s in statuses)
    result = {"status": overall, "checks": checks}
    save_json(wd / "validation_report.json", result)
    return result
