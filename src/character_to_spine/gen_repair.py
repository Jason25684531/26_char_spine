"""生成式補圖的紀錄與狀態（<圖名>.overrides/provenance.json）。

每個部件的 attempts 是唯一的事實來源，依時間排列；其餘狀態（剩餘次數、是否用盡、目前採用哪一次）都由它推導。
verdict：pending（已登記、還沒匯入）、interrupted（登記後沒有結果）、reject、pass。
流程：begin 登記 → Agent 呼叫圖像生成 → prepare --generated 匯入（融合＋數值判定）→ review 目視判定。
"""
import hashlib
import os
import shutil
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image

from . import C2SError, NeedsInput, __version__, load_json, save_json
from .fusion import MARKER, fuse, judge

MAX_ATTEMPTS = 3  # 同一部件連續未通過（含中斷、目視不通過）的上限，用完就列人工修補
IMAGE_GEN_TOOL = "codex image_gen (built-in)"
STATUS = {"generated": "ai_repaired", "reference": "ref_repaired"}
# 每次重試換一個策略；同一個部件不會被建議重複用過的策略
STRATEGIES = {
    "mask": "整張圖，被遮住的區域塗成洋紅色（gen_inputs/<部件>.png）",
    "mask-local": "只給部件附近的局部圖（gen_inputs/<部件>_local.png）：生成工具看得更清楚、比較不會重畫整個角色；匯入時加 --strategy mask-local",
    "reference": "局部圖之外，另外附上同一角色、這個部件看得見的參考圖，要求照參考圖的設計補畫",
}
VERDICTS = ("pass", "fail", "unsure")


def overrides_dir(wd, doc):
    """人工修補圖與生成素材的永久位置：正式 parts.json 旁的 <圖名>.overrides/。來源就在工作目錄時才退回 工作目錄/overrides/。"""
    src = Path(doc.get("source", wd / "parts.json")).resolve()
    if src.parent == Path(wd).resolve():
        return Path(wd) / "overrides"
    return src.parent / f"{Path(doc.get('image') or src.name.split('.')[0]).stem}.overrides"


def load_provenance(odir):
    path = Path(odir) / "provenance.json"
    return load_json(path) if path.exists() else {"parts": {}}


def _open(workdir):
    wd = Path(workdir)
    doc = load_json(wd / "parts.json")
    odir = overrides_dir(wd, doc)
    return wd, doc, odir, load_provenance(odir)


def grant_consent(workdir):
    """記錄使用者已明確許可這個角色交給 Codex 內建 image_gen 處理（雲端）。只有 Agent 問過使用者、得到同意後才呼叫。"""
    wd, doc, odir, prov = _open(workdir)
    prov["image"] = doc.get("image")
    prov["cloud_consent"] = {"granted": True, "date": date.today().isoformat(), "scope": IMAGE_GEN_TOOL}
    save_json(odir / "provenance.json", prov)
    return {"status": "ok", "provenance": str(odir / "provenance.json")}


def _valid_pass(a):
    return a["verdict"] == "pass" and a.get("review", {}).get("verdict") != "fail" and not a.get("rolled_back")


def _window(rec):
    """目前這一輪計次的起點：最後一次重開，或最後一次有效通過之後。"""
    att = rec["attempts"]
    last_pass = max((i + 1 for i, a in enumerate(att) if _valid_pass(a)), default=0)
    return max(last_pass, max((r["after_attempt"] for r in rec.get("reopened", [])), default=0))


def remaining(rec):
    used = sum(1 for a in rec["attempts"][_window(rec):] if a["verdict"] in ("reject", "interrupted", "pending") or
               (a["verdict"] == "pass" and not _valid_pass(a)))
    return MAX_ATTEMPTS - used


def next_strategy(rec):
    used = [a.get("strategy") for a in rec["attempts"][_window(rec):]]
    return next((s for s in STRATEGIES if s not in used), list(STRATEGIES)[-1])


def _record(prov, name):
    return prov["parts"].setdefault(name, {"attempts": [], "accepted": None})


def _save(odir, prov, rec):
    rec["exhausted"] = remaining(rec) <= 0 and rec["accepted"] is None
    save_json(Path(odir) / "provenance.json", prov)


def _need_consent(prov):
    if not prov.get("cloud_consent", {}).get("granted"):
        raise C2SError("尚未取得使用者對這個角色雲端處理的明確許可，不能使用雲端生成。"
                       "請先詢問使用者，同意後執行 c2s consent，再繼續")


def begin(workdir, name, prompt, strategy=None):
    """生成前登記一次嘗試。回傳剩餘次數、這次該用的策略與要交給生成工具的圖。登記後沒有匯入就再登記，前一次記為中斷。"""
    wd, doc, odir, prov = _open(workdir)
    if name not in {p["name"] for p in doc["parts"]}:
        raise C2SError(f"沒有名為 {name} 的部件")
    _need_consent(prov)
    rec = _record(prov, name)
    if rec["attempts"] and rec["attempts"][-1]["verdict"] == "pending":
        rec["attempts"][-1]["verdict"] = "interrupted"  # 生成途中被中斷：仍算一次，避免無限重試
    if remaining(rec) <= 0:
        _save(odir, prov, rec)
        raise C2SError(f"{name} 的生成式補圖已達 {MAX_ATTEMPTS} 次上限，請改用人工修補（c2s prepare --replace），"
                       "或在使用者明確要求時以 c2s prepare --reopen 附理由重開")
    strategy = strategy or next_strategy(rec)
    if strategy not in STRATEGIES:
        raise C2SError(f"未知的策略 {strategy}（可用：{', '.join(STRATEGIES)}）")
    rec["attempts"].append({"verdict": "pending", "strategy": strategy, "prompt": prompt, "date": date.today().isoformat(),
                            "c2s_version": __version__})
    _save(odir, prov, rec)
    image = wd / "gen_inputs" / (f"{name}_local.png" if strategy != "mask" else f"{name}.png")
    if not image.exists():
        raise NeedsInput(f"找不到 {image}，請先執行 c2s prepare（這個部件沒有被遮住的區域時不需要補圖）")
    return {"status": "ok", "part": name, "remaining": remaining(rec), "strategy": strategy, "how": STRATEGIES[strategy],
            "input": str(image)}


def reopen(workdir, name, reason):
    """已用盡次數的部件重新計次。只在使用者明確要求、或方法有實質改變時使用，理由會留在紀錄裡。"""
    _, _, odir, prov = _open(workdir)
    if not (reason or "").strip():
        raise C2SError("重開需要寫明理由（--reason），例如使用者的要求或這次改用的新方法")
    if name not in prov["parts"]:
        raise C2SError(f"{name} 沒有生成式補圖的紀錄，不需要重開")
    rec = prov["parts"][name]
    if rec["attempts"] and rec["attempts"][-1]["verdict"] == "pending":
        rec["attempts"][-1]["verdict"] = "interrupted"
    rec.setdefault("reopened", []).append({"after_attempt": len(rec["attempts"]), "reason": reason.strip(),
                                           "date": date.today().isoformat(), "c2s_version": __version__})
    _save(odir, prov, rec)
    return {"status": "ok", "part": name, "remaining": remaining(rec)}


def _adopt(odir, rec, name, index):
    """把第 index 次的融合結果設為目前採用的圖層；None 表示不採用任何生成結果。"""
    dest = Path(odir) / f"{name}.png"
    rec["accepted"] = index
    if index is None:
        dest.unlink(missing_ok=True)
    else:
        shutil.copyfile(Path(odir) / rec["attempts"][index]["fused_candidate"], dest)


def _earlier_pass(odir, rec, before):
    return next((i for i in range(before - 1, -1, -1) if _valid_pass(rec["attempts"][i])
                 and (Path(odir) / rec["attempts"][i].get("fused_candidate", "?")).exists()), None)


def rollback(workdir, name):
    """回到上一個通過的成果（新的成果雖然通過，但實際看起來比較差時使用）。之後要重跑 c2s prepare。"""
    _, _, odir, prov = _open(workdir)
    rec = prov["parts"].get(name)
    if not rec or rec["accepted"] is None:
        raise C2SError(f"{name} 目前沒有採用任何生成式補圖")
    earlier = _earlier_pass(odir, rec, rec["accepted"])
    if earlier is None:
        raise C2SError(f"{name} 沒有更早的通過成果可以還原")
    rec["attempts"][rec["accepted"]]["rolled_back"] = True
    _adopt(odir, rec, name, earlier)
    _save(odir, prov, rec)
    return {"status": "ok", "part": name, "accepted_attempt": earlier + 1}


def review(workdir, name, verdict, note, by):
    """目視判定目前採用的補圖。fail 會撤回它（回到更早的成果或草稿）並計一次失敗。之後要重跑 c2s prepare。"""
    _, _, odir, prov = _open(workdir)
    if verdict not in VERDICTS:
        raise C2SError(f"verdict 必須是 {'／'.join(VERDICTS)}")
    if not (note or "").strip():
        raise C2SError("目視判定需要說明看到了什麼（--note），例如「手掌形狀自然，沒有殘留花瓣」")
    rec = prov["parts"].get(name)
    if not rec or rec["accepted"] is None:
        raise C2SError(f"{name} 目前沒有採用任何生成式補圖，沒有可以判定的對象")
    att = rec["attempts"][rec["accepted"]]
    att["review"] = {"verdict": verdict, "note": note.strip(), "by": (by or "agent").strip(), "date": date.today().isoformat()}
    if verdict == "fail":
        att.setdefault("reasons", []).append(f"目視不通過：{note.strip()}")
        att["next_strategy"] = next_strategy(rec)
        _adopt(odir, rec, name, _earlier_pass(odir, rec, rec["accepted"]))
    _save(odir, prov, rec)
    out = {"status": "ok", "part": name, "verdict": verdict, "remaining": remaining(rec)}
    if verdict == "fail":
        out["next_strategy"] = att["next_strategy"]
    return out


def find_raw(path, sha):
    """在 Codex 的生成輸出目錄找雜湊相同的檔案：找得到才能說匯入的是工具的原始輸出。"""
    home = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "generated_images"
    if not home.is_dir():
        return None
    size = Path(path).stat().st_size
    for f in home.rglob("*.png"):
        try:
            if f.stat().st_size == size and hashlib.sha256(f.read_bytes()).hexdigest() == sha:
                return str(f)
        except OSError:
            continue
    return None


def local_box(mask):
    """mask-local 策略的裁切範圍 (x0, y0, x1, y1)：部件外框四周各留 35%（至少 40px）。"""
    h, w = mask.shape
    ys, xs = np.nonzero(mask)
    mx, my = max(40, round(0.35 * (xs.max() - xs.min()))), max(40, round(0.35 * (ys.max() - ys.min())))
    return max(0, int(xs.min()) - mx), max(0, int(ys.min()) - my), min(w, int(xs.max()) + mx + 1), min(h, int(ys.max()) + my + 1)


def write_gen_inputs(wd, rgba, parts, masks):
    """每個有被遮區的部件：原圖的被遮區塗成 MARKER，交給 image_gen 填。另存局部版（mask-local 策略用）。"""
    out = Path(wd) / "gen_inputs"
    shutil.rmtree(out, ignore_errors=True)
    z = {p["name"]: p["z"] for p in parts}
    fg = rgba[..., 3] > 0
    for p in parts:
        name = p["name"]
        above = np.zeros(fg.shape, bool)
        for n, m in masks.items():
            if z.get(n, -1) > z[name]:
                above |= m
        hid = masks[name] & above & fg
        if not hid.any() or p.get("role") in ("ground", "effect"):
            continue
        img = rgba.copy()
        img[hid] = (*MARKER, 255)
        out.mkdir(exist_ok=True)
        Image.fromarray(img).save(out / f"{name}.png")
        box = local_box(masks[name] & fg)
        Image.fromarray(img[box[1]:box[3], box[0]:box[2]]).save(out / f"{name}_local.png")
        save_json(out / f"{name}_local.json", {"box": list(box)})


def _score(metrics):
    return metrics.get("visible_mae", 1) + metrics.get("seam_delta", 1)


def import_generated(generated, reference, strategy, rgba, parts, masks, odir, prov):
    """融合一張生成圖並記錄。通過且不比現有成果差：採用。不通過：還能重試就要求重試（NeedsInput），用完就標記人工。
    同一個檔案（雜湊相同）再匯入一次只會重新融合，不會多算一次。"""
    name, path, prompt = generated
    odir = Path(odir)
    rec = _record(prov, name)
    sha = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    att = rec["attempts"]
    index = next((i for i, a in enumerate(att) if a.get("sha256") == sha), None)
    again = index is not None
    if not again:
        if att and att[-1]["verdict"] == "pending":
            index = len(att) - 1
        elif remaining(rec) <= 0:
            raise C2SError(f"{name} 的生成式補圖已連續 {MAX_ATTEMPTS} 次未通過，已達上限，請改用人工修補（c2s prepare --replace）")
        else:
            att.append({"date": date.today().isoformat(), "c2s_version": __version__})
            index = len(att) - 1
    a = att[index]
    strategy = strategy or a.get("strategy") or "mask"
    z = next(p["z"] for p in parts if p["name"] == name)
    above = np.zeros(masks[name].shape, bool)
    for p in parts:
        if p["z"] > z:
            above |= masks[p["name"]]
    gen = np.array(Image.open(path).convert("RGBA"))
    if strategy == "mask":
        layer, metrics = fuse(rgba, masks[name], above, gen)
    else:  # 生成圖只涵蓋局部：在同一個裁切範圍內融合，再放回整張畫布
        x0, y0, x1, y1 = local_box(masks[name] & (rgba[..., 3] > 0))
        part_layer, metrics = fuse(rgba[y0:y1, x0:x1], masks[name][y0:y1, x0:x1], above[y0:y1, x0:x1], gen)
        layer = np.zeros(rgba.shape, np.uint8)
        layer[y0:y1, x0:x1] = part_layer
    reasons = judge(metrics)
    if again and reasons:
        raise C2SError(f"{name} 第 {index + 1} 次的生成圖以目前的部件範圍重新融合未通過（{'；'.join(reasons)}），保留原本的成果")
    keep = odir / "generated" / f"{name}_{index + 1}.png"
    keep.parent.mkdir(parents=True, exist_ok=True)
    if not again:
        shutil.copyfile(path, keep)  # 生成結果不可重現，永久保存；重跑不再需要生成
    fused = keep.with_name(f"{keep.stem}_fused.png")  # 每次的融合結果都留著：供還原，以及未通過時讓人工判斷
    Image.fromarray(layer).save(fused)
    a.update(file=keep.relative_to(odir).as_posix(), fused_candidate=fused.relative_to(odir).as_posix(), sha256=sha,
             source="reference" if reference else "generated", tool="reference image" if reference else IMAGE_GEN_TOOL,
             reference_image=str(reference) if reference else None, strategy=strategy, metrics=metrics,
             verdict="reject" if reasons else "pass", reasons=reasons)
    if not again:
        a.update(prompt=prompt or a.get("prompt"), original_file=str(Path(path).resolve()),
                 raw_source=None if reference else find_raw(path, sha))
    if not reasons:
        current = rec["accepted"]
        better = current is None or current == index or _score(metrics) <= _score(att[current]["metrics"])
        a["adopted"] = better  # 通過但比現有成果差：不取代（退步保護）
        if better:
            _adopt(odir, rec, name, index)
        _save(odir, prov, rec)
        return
    a["next_strategy"] = next_strategy(rec)
    _save(odir, prov, rec)
    if remaining(rec) > 0:
        raise NeedsInput(f"{name} 的生成圖未通過：{'；'.join(reasons)}。只修正這個問題後重新生成，還可重試 {remaining(rec)} 次。"
                         f"下一次改用策略 {a['next_strategy']}：{STRATEGIES[a['next_strategy']]}（融合結果：{odir / a['fused_candidate']}）")
