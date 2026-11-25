"""動畫品質檢查與自我修正（Python Simulation，不是 Spine 算圖）。

逐格量測四類問題，與初始姿勢比較：
- hole：角色內部新出現的透明破洞（閉運算後的內部空洞面積 ÷ 角色面積）
- gap：關節縫隙（部件與它最貼近的部件之間，新出現的透明夾縫像素 ÷ 兩者初始接觸區面積）
- attach：parts.json 宣告要接觸的兩個部件，重疊量 ÷ 初始姿勢的重疊量（分離）
- intrude：受約束的部件（有 attach 的部件與道具）和「初始姿勢沒有接觸」的部件新產生的重疊 ÷ 較小部件面積（穿插，
  例如吉他甩進臉）。部件前後順序本身是 parts.json 的語意判斷，程式無法自動驗證，請看 layer_preview.png
- exposure：不可靠的補圖在動畫中被看見的面積 ÷ 部件面積

refine：有異常 → 在最差的影格逐一凍結各骨頭（hip 除外）找出改善最多的那根 → 該骨頭幅度 ×0.5 → 重做動畫。
最多 MAX_ROUNDS 輪；沒有改善就還原到最佳那輪並停止。之後把被縮小的骨頭逐一放大 √2 倍，總異常量沒有增加就保留（回升）。
各輪的量測、調整與異常影格都留在 quality/。
"""
import copy
import math
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import load_json, save_json
from .animation_builder import build_animations, duration
from .image_processor import write_reports
from .preview import framing, render, warp_slots, world_matrices
from .rig_builder import PRESETS
from .spine_exporter import DEFAULT_SPINE_VERSION, build_skeleton, export

FPS = 10
MAX_ROUNDS = 3
# 門檻（校準依據見 docs/DECISIONS.md D-31、D-32）
THRESHOLDS = {"hole": 0.003, "gap": 0.1, "attach": 0.6, "intrude": 0.02, "exposure": 0.02}
LOWER_IS_BAD = {"attach"}  # attach 是比值越低越糟，其餘越高越糟


def violation(kind, value):
    """超出門檻多少（> 0 才是異常）。"""
    th = THRESHOLDS[kind]
    return th - value if kind in LOWER_IS_BAD else value - th


def _context(wd):
    wd = Path(wd)
    meta, rig = load_json(wd / "metadata.json"), load_json(wd / "rig.json")
    canvas, origin, scale = framing(meta)
    parts = {e["name"]: e for e in meta["parts"] if "file" in e}
    return {"wd": wd, "meta": meta, "rig": rig, "canvas": canvas, "origin": origin, "scale": scale, "cache": {},
            "images": wd / "layers", "masks": wd / "repair_masks", "parts": parts,
            # 要擔心露出的補圖：「自動補、但量測為不可靠」與「已判為需人工」的草稿。可靠的補圖露出也看不出破綻；
            # 需人工的草稿在補畫前也不該露出，補畫後（--replace）沒有補圖遮罩，限制自然解除
            "exposure_parts": [n for n, e in parts.items() if e["status"] == "needs_manual"
                               or (e["status"] == "auto_repaired" and not e.get("repair_reliable", True))],
            "contacts": [(c["a"], c["b"]) for c in rig.get("contacts", [])],
            "ground": {n for n, r in rig.get("roles", {}).items() if r == "ground"},
            # 穿插檢查的對象：有宣告接觸的部件與道具（使用者要求手、吉他、身體不得穿插）
            "constrained": sorted({n for c in rig.get("contacts", []) for n in (c["a"], c["b"])}
                                  | {n for n, r in rig.get("roles", {}).items() if r == "prop"})}


def _frame(ctx, skel, anim, t):
    slots = list(warp_slots(skel, ctx["images"], ctx["canvas"], ctx["origin"], anim, t, ctx["scale"], ctx["cache"], ctx["masks"]))
    w, h = ctx["canvas"]
    every = {n: wp[..., 3] / 255 for n, wp, _ in slots}
    through, vis = np.ones((h, w)), {}
    for n, _, _ in reversed(slots):  # 由前往後：每個 slot 最後真正看得見的比例
        vis[n] = every[n] * through
        through = through * (1 - every[n])
    # 地面影子不是角色身體：破洞、縫隙、穿插只看身體部件；影子草稿的露出仍用 vis／masks 量
    alphas = {n: a for n, a in every.items() if n not in ctx["ground"]}
    body = 1 - np.prod([1 - a for a in alphas.values()], axis=0)
    return {"alpha": body, "alphas": alphas, "all_alphas": every, "vis": vis, "masks": {n: m for n, _, m in slots},
            "world": world_matrices(skel, anim, t), "dil": {}}


def _dilated(f, name):
    if name not in f["dil"]:
        f["dil"][name] = cv2.dilate((f["alphas"][name] > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    return f["dil"][name]


def _near(f, name):
    key = ("near", name)
    if key not in f["dil"]:
        f["dil"][key] = cv2.dilate((f["alphas"][name] > 0.5).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    return f["dil"][key]


def _crack(f, child, adj):
    """關節縫隙：畫面上透明、但同時離兩個部件都在 4px 內的像素（兩者之間透出背景的細縫）。
    只看畫面最後的結果：某部件離開了，但後面還有別的部件蓋著，就不算縫。"""
    return (f["alpha"] <= 0.5) & _near(f, child) & _near(f, adj)


def _holes(alpha, k=3):
    """被角色完全包住（不連到畫面邊緣）的透明區域。
    先做 k px 閉運算，消掉反鋸齒造成的假縫。不用大核閉運算的原因：它會把舉手時的腋下、捲髮的凹口
    這類自然凹處也算成破洞（真實角色實測誤判，見 DECISIONS D-31）。關節處張開的凹口由 gap 逐關節量測。"""
    solid = cv2.morphologyEx((alpha > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    outside = np.pad(1 - solid, 1, constant_values=1)
    cv2.floodFill(outside, None, (0, 0), 2)  # 從畫面邊緣灌水：灌得到的是外部背景
    return outside[1:-1, 1:-1] == 1


def _real_holes(ctx, f):
    """真正的破洞（K-24）：被包住的透明像素中，初始姿勢被某個部件蓋住、而那個部件現在已經不在這塊透明區旁邊的部分。
    初始姿勢就是背景的區域（長杖與帽簷、叉腰的手臂圍出的空間）不算：微小的動作就能讓它「圍起來或打開」，
    以前因此整塊被誤判。部件自己移開、旁邊露出它背後的背景也不算；關節處的分離由 gap 量。
    初始姿勢的位置先依 body 骨頭的變化換算到這一格（扣掉整體跳躍、蹲下與身體擺動）。
    ponytail: 移開的部件仍貼著洞口時（只移開一部分）不算；本流程的被遮區域都有補圖，這種洞只在 polygon 漏畫時出現"""
    holes = _holes(f["alpha"])
    n, lab = cv2.connectedComponents(holes.astype(np.uint8))
    if n <= 1:
        return holes
    s, (ox, oy) = ctx["scale"], ctx["origin"]
    to_canvas = np.array([[s, 0, ox], [0, -s, oy], [0, 0, 1]])
    m = (to_canvas @ f["world"]["body"] @ np.linalg.inv(ctx["setup_body"]) @ np.linalg.inv(to_canvas))[:2]
    covered = {p: cv2.warpAffine(a, m, ctx["canvas"]) > 0.5 for p, a in ctx["setup_alphas"].items()}
    kernel = np.ones((5, 5), np.uint8)
    keep = np.zeros_like(holes)
    for i in range(1, n):
        comp = lab == i
        ring = cv2.dilate(comp.astype(np.uint8), kernel).astype(bool) & ~comp
        for p, was in covered.items():
            if p not in f["alphas"] or not (_dilated(f, p) & ring).any():
                keep |= comp & was
    return keep


def _raw(ctx, f):
    """單一影格的原始量測值。"""
    raw = {("hole", "character"): float(_real_holes(ctx, f).sum())}
    for child, adj, _ in ctx["joints"]:
        raw[("gap", child)] = float(_crack(f, child, adj).sum())
    for a, b in ctx["contacts"]:
        raw[("attach", f"{a}+{b}")] = float((_dilated(f, a) & _dilated(f, b)).sum())
    for a, b in ctx["intrude_pairs"]:
        raw[("intrude", f"{a}+{b}")] = float(((f["alphas"][a] > 0.5) & (f["alphas"][b] > 0.5)).sum())
    for p in ctx["exposure_parts"]:
        m = f["masks"].get(p)
        raw[("exposure", p)] = float((m * f["vis"][p]).sum()) if m is not None else 0.0
    return raw


def _relative(ctx, raw, base):
    """相對初始姿勢的指標值（與 THRESHOLDS 同單位）。"""
    out = {}
    for (kind, subject), v in raw.items():
        b = base[(kind, subject)]
        if kind == "hole":
            out[(kind, subject)] = max(0.0, v - b) / ctx["char_area"]
        elif kind == "gap":  # 新增的夾縫像素 ÷ 兩者在初始姿勢的接觸區面積
            contact = next(c for ch, _, c in ctx["joints"] if ch == subject)
            out[(kind, subject)] = max(0.0, v - b) / contact
        elif kind == "attach":  # 基準為 0（縮圖後量不到接觸）時判為 0：寧可報異常，也不默默通過
            out[(kind, subject)] = v / b if b else 0.0
        elif kind == "intrude":
            a, c = subject.split("+")
            out[(kind, subject)] = max(0.0, v - b) / max(1.0, min(ctx["part_area"][a], ctx["part_area"][c]))
        else:
            out[(kind, subject)] = max(0.0, v - b) / max(1.0, ctx["part_area"][subject])
    return out


def _prepare_context(ctx, skel):
    """用初始姿勢算出基準值與各部件的鄰接關係。"""
    f = _frame(ctx, skel, None, 0.0)
    ctx["char_area"] = max(1.0, float((f["alpha"] > 0.5).sum()))
    ctx["part_area"] = {n: float((a > 0.5).sum()) for n, a in f["all_alphas"].items()}
    names = sorted(f["alphas"])
    ctx["setup_alphas"] = {n: a.astype(np.float32) for n, a in f["alphas"].items()}
    ctx["setup_body"] = f["world"]["body"]
    setup_contacts = {(a, b) for i, a in enumerate(names) for b in names[i + 1:] if (_dilated(f, a) & _dilated(f, b)).any()}
    # 頭髮是最後面的背景層，手或道具畫在它前面是正常的，不算穿插
    backdrop = {n for n, r in ctx["rig"].get("roles", {}).items() if r == "hair"}
    ctx["intrude_pairs"] = sorted({tuple(sorted((a, o))) for a in ctx["constrained"] for o in names
                                   if o != a and o not in backdrop and tuple(sorted((a, o))) not in setup_contacts})
    # 縫隙量身體結構上的關節：必要部件依 preset（抱樂器的手仍接在肩膀上），其他部件依骨架的父骨頭；hip 視為 body。
    # 碰巧接觸更多的部件（手指碰到角）不是關節（K-24）。父部件在初始姿勢沒有接觸時（腿被裙子隔開），
    # 才退回接觸區最大的鄰接部件。接觸區面積是縫隙的正規化基準
    parent = {**{b["name"]: b.get("parent") for b in ctx["rig"]["bones"]}, **PRESETS[ctx["rig"]["preset"]]["bones"]}
    parent = {n: "body" if p == "hip" else p for n, p in parent.items()}
    contact = lambda a, b: int((_near(f, a) & _near(f, b)).sum())
    ctx["joints"] = []
    for child in sorted(n for n in ctx["parts"] if n not in ctx["ground"] and n != "body"):
        adj = parent.get(child)
        best = (contact(child, adj), adj) if adj in f["alphas"] else (0, None)
        if not best[0]:
            best = max(((contact(child, o), o) for o in names if o != child), default=(0, None))
        if best[0]:
            ctx["joints"].append((child, best[1], float(best[0])))
    ctx["base"] = _raw(ctx, f)


def assess(ctx, skel):
    """逐格量測所有動畫。回傳 (各指標最差值, 異常清單)。"""
    worst = {}
    for anim, data in skel["animations"].items():
        keys = {k.get("time", 0) for tls in data["bones"].values() for ks in tls.values() for k in ks}
        for t in sorted({round(i / FPS, 4) for i in range(round(duration(data) * FPS) + 1)} | keys):  # 一定包含每個關鍵影格
            for key, v in _relative(ctx, _raw(ctx, _frame(ctx, skel, anim, t)), ctx["base"]).items():
                if key not in worst or violation(key[0], v) > violation(key[0], worst[key]["value"]):
                    worst[key] = {"value": round(v, 4), "anim": anim, "t": t}
    anomalies = [{"kind": k, "subject": s, **w, "threshold": THRESHOLDS[k], "violation": round(violation(k, w["value"]), 4)}
                 for (k, s), w in sorted(worst.items()) if violation(k, w["value"]) > 0]
    return worst, anomalies


def attribute(ctx, skel, a):
    """反事實歸因：在異常最嚴重的影格逐一凍結各骨頭的動畫，回傳凍結後改善最多的骨頭（沒有改善則 None）。"""
    key = (a["kind"], a["subject"])
    best, best_gain = None, 1e-4
    for bone in sorted(skel["animations"][a["anim"]]["bones"]):
        if bone == "hip":  # hip 讓全身一起移動，不會造成部件之間的相對問題
            continue
        trial = copy.deepcopy(skel)
        del trial["animations"][a["anim"]]["bones"][bone]
        v = _relative(ctx, _raw(ctx, _frame(ctx, trial, a["anim"], a["t"])), ctx["base"])[key]
        gain = violation(a["kind"], a["value"]) - violation(a["kind"], v)
        if gain > best_gain:
            best, best_gain = bone, gain
    return best


def _save_frame(ctx, skel, a, out_dir):
    """異常影格：紅色標出問題區域，給 Agent 自我檢查。"""
    f = _frame(ctx, skel, a["anim"], a["t"])
    rgb = render(skel, ctx["images"], ctx["canvas"], ctx["origin"], a["anim"], a["t"], ctx["scale"], ctx["cache"])[0]
    kind, s = a["kind"], a["subject"]
    if kind == "hole":
        mark = _real_holes(ctx, f)
    elif kind == "gap":
        adj = next(a for c, a, _ in ctx["joints"] if c == s)
        mark = cv2.dilate(_crack(f, s, adj).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    elif kind == "intrude":
        p1, p2 = s.split("+")
        mark = (f["alphas"][p1] > 0.5) & (f["alphas"][p2] > 0.5)
    elif kind == "attach":
        mark = np.zeros(f["alpha"].shape, bool)
        for n in s.split("+"):
            m = (f["alphas"][n] > 0.5).astype(np.uint8)
            mark |= (m - cv2.erode(m, np.ones((3, 3), np.uint8))).astype(bool)
    else:
        mark = f["masks"][s] * f["vis"][s] > 0.3
    rgb[mark] = rgb[mark] * 0.3 + np.array([255, 0, 0]) * 0.7
    img = Image.fromarray(rgb.clip(0, 255).astype(np.uint8))
    ImageDraw.Draw(img).text((4, 3), f"Python Simulation Preview | {a['anim']} t={a['t']:.1f}s | {kind}:{s} = {a['value']} "
                             f"(threshold {a['threshold']})", fill=(200, 0, 0))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{a['anim']}_t{a['t']:.1f}_{kind}_{s.replace('+', '-')}.png"
    img.save(path)
    return str(path)


def _score(anomalies):
    """總異常量：各類違規先除以自己的門檻再加總，單位才一致（hole 門檻 0.003 與 attach 0.6 差兩個數量級）。"""
    return round(sum(a["violation"] / a["threshold"] for a in anomalies), 4)


def _worst(worst):
    return {f"{k}:{s}": w for (k, s), w in sorted(worst.items())}


def refine(workdir, motion="happy", spine_version=None, spine_exe=None):
    """自我修正迴圈。結束時 export 一次（含 Spine CLI 匯入）並寫出 quality/quality_report.json。"""
    wd = Path(workdir)
    qdir = wd / "quality"
    shutil.rmtree(qdir, ignore_errors=True)
    tuning = {}  # 每次從 1 開始，重跑結果相同
    save_json(wd / "tuning.json", tuning)
    build_animations(wd, motion)
    ctx = _context(wd)
    _prepare_context(ctx, build_skeleton(wd))
    rounds, best = [], None
    for r in range(MAX_ROUNDS + 1):
        skel = build_skeleton(wd)
        worst, anomalies = assess(ctx, skel)
        for a in anomalies:
            a["frame"] = _save_frame(ctx, skel, a, qdir / f"round_{r}")
        rec = {"round": r, "tuning": copy.deepcopy(tuning), "score": _score(anomalies),
               "anomalies": anomalies, "worst": _worst(worst)}
        rounds.append(rec)
        if best is not None and rec["score"] >= best["score"]:
            rec["note"] = "這一輪的調整沒有降低總異常量，還原到第 %d 輪並停止" % best["round"]
            break
        best = rec
        if not anomalies or r == MAX_ROUNDS:
            break
        fixes = []
        for a in anomalies:
            a["attributed_to"] = bone = attribute(ctx, skel, a)
            if bone and (a["anim"], bone) not in fixes:
                fixes.append((a["anim"], bone))
        rec["fixes"] = [{"animation": an, "bone": b, "factor": 0.5} for an, b in fixes]
        if not fixes:
            rec["note"] = "找不到能改善的骨頭，停止"
            break
        for an, b in fixes:
            tuning.setdefault(an, {})[b] = tuning.get(an, {}).get(b, 1.0) * 0.5
        save_json(wd / "tuning.json", tuning)
        build_animations(wd, motion)

    # 回升（「過度縮小動作」）：減半是粗步，常常縮過頭。被縮小的骨頭逐一放大 √2 倍（不超過 1），
    # 總異常量沒有增加就保留，直到再放大會變差為止
    regrow = []
    for an, bone in sorted((an, b) for an, bs in best["tuning"].items() for b in bs):
        while bone in best["tuning"].get(an, {}):
            trial = copy.deepcopy(best["tuning"])
            factor = round(min(1.0, trial[an][bone] * math.sqrt(2)), 4)
            trial[an][bone] = factor
            if factor == 1.0:  # 回到原幅度就不再記錄
                del trial[an][bone]
                trial = {k: v for k, v in trial.items() if v}
            save_json(wd / "tuning.json", trial)
            build_animations(wd, motion)
            worst, anomalies = assess(ctx, build_skeleton(wd))
            score = _score(anomalies)
            regrow.append({"animation": an, "bone": bone, "factor": factor, "score": score, "kept": score <= best["score"]})
            if score > best["score"]:
                break
            best = {**best, "tuning": trial, "score": score, "anomalies": anomalies, "worst": _worst(worst)}

    save_json(wd / "tuning.json", best["tuning"])  # 採用最佳那一輪（含回升）
    build_animations(wd, motion)
    final = best["anomalies"]
    if any(g["kept"] for g in regrow):  # 回升後的異常影格另存，供 Agent 檢視
        skel = build_skeleton(wd)
        for a in final:
            a["frame"] = _save_frame(ctx, skel, a, qdir / "final")

    # 不可靠、且修正後仍露出的補圖 → 不能宣稱自動修補成功
    meta = load_json(wd / "metadata.json")
    auto = {e["name"] for e in meta["parts"] if e["status"] == "auto_repaired"}
    exposed = {a["subject"]: a for a in final if a["kind"] == "exposure" and a["subject"] in auto}
    best_worst = best["worst"]
    for e in meta["parts"]:
        w = best_worst.get(f"exposure:{e['name']}")
        if w:  # 不可靠的補圖：記錄實際露出量（門檻內也記，供目視檢查）
            e["exposure"] = w["value"]
        if e["name"] in exposed:
            a = exposed[e["name"]]
            e.update(status="needs_manual", reason=f"自動補圖不可靠（留出驗證誤差 {e.get('holdout_error')}、"
                     f"被遮輪廓 {e.get('contour_hidden')}），動畫中露出 {a['value']:.1%}（{a['anim']} t={a['t']}s）")
    save_json(wd / "metadata.json", meta)
    write_reports(wd)

    export(wd, spine_version or DEFAULT_SPINE_VERSION, spine_exe)
    unresolved = [a for a in final if a["kind"] != "exposure"]
    watch = {e["name"]: e["exposure"] for e in meta["parts"]
             if e.get("exposure") and e["status"] == "auto_repaired"}  # 不可靠、門檻內但有露出：建議目視
    report = {"fps": FPS, "thresholds": THRESHOLDS, "max_rounds": MAX_ROUNDS, "chosen_round": best["round"],
              "tuning": best["tuning"], "worst": best["worst"], "rounds": rounds, "regrow": regrow, "unresolved": unresolved,
              "downgraded_to_needs_manual": sorted(exposed), "unreliable_exposed_within_threshold": watch}
    save_json(qdir / "quality_report.json", report)
    return {"status": "BLOCKED" if unresolved else "PASS", "rounds": len(rounds), "chosen_round": best["round"],
            "tuning": best["tuning"], "unresolved": [f"{a['kind']}:{a['subject']}" for a in unresolved],
            "downgraded_to_needs_manual": sorted(exposed)}
