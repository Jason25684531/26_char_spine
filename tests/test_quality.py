"""spec（quality-hardening）：asset-persistence、repair-risk、animation-quality、motion-constraints、self-correction"""
import json
import math
import shutil

import pytest

from character_to_spine import NeedsInput, load_json, pipeline, quality, save_json
from character_to_spine.analyzer import analyze
from character_to_spine.animation_builder import CONTACT_TOL, TEMPLATES, build_animations, contact_limits
from character_to_spine.image_processor import CONTOUR_HIDDEN_MAX, HOLDOUT_MAX, prepare
from character_to_spine.rig_builder import build_rig
from character_to_spine.spine_exporter import build_skeleton, export
from character_to_spine.validator import validate
from synthetic import make, make_custom, rect


def part(wd, name):
    return next(e for e in load_json(wd / "metadata.json")["parts"] if e["name"] == name)


def checks(wd):
    return {c["check"]: c for c in validate(wd)["checks"]}


# ---------- asset-persistence ----------

def test_replace_goes_to_permanent_overrides(tmp_path):
    img, _ = make("synth_a", tmp_path / "src")
    wd = tmp_path / "w"
    analyze(img, wd)
    prepare(wd)
    fixed = tmp_path / "fixed.png"
    shutil.copy(wd / "layers" / "head.png", fixed)
    prepare(wd, replace={"head": fixed})
    assert (tmp_path / "src" / "synth_a.overrides" / "head.png").exists()
    assert not (wd / "overrides").exists()


def test_rebuild_after_deleting_output(tmp_path):
    """刪除工作目錄後重跑，成果（含人工修補）完全相同。"""
    img, _ = make("synth_b", tmp_path / "src")
    wd = tmp_path / "w"
    pipeline.run(img, workdir=wd)
    from PIL import Image
    fixed = tmp_path / "fixed_flag.png"
    Image.open(wd / "layers" / "flag.png").transpose(Image.FLIP_LEFT_RIGHT).save(fixed)
    prepare(wd, replace={"flag": fixed})
    pipeline.run(img, workdir=wd)
    before = {p: (wd / p).read_bytes() for p in ("spine/character.json", "layers/flag.png", "tuning.json")}
    shutil.rmtree(wd)
    pipeline.run(img, workdir=wd)
    assert {p: (wd / p).read_bytes() for p in before} == before
    assert part(wd, "flag")["status"] == "replaced"


# ---------- repair-risk ----------

def test_solid_fill_is_reliable(built):
    body = part(built("synth_b"), "body")
    assert body["repair_reliable"] and body["holdout_error"] < 0.02


def _risk_case(tmp_path, kind):
    if kind == "stripes":  # 條紋部件被一塊方形擋住中間
        parts = [("body", rect(40, 40, 200, 200), "stripes", 1, {}), ("badge", rect(100, 100, 140, 140), (200, 40, 40), 2, {})]
    else:  # 單色部件，右半邊連同輪廓整個被擋住
        parts = [("body", rect(40, 40, 200, 200), (60, 120, 200), 1, {}), ("panel", rect(140, 20, 230, 220), (200, 40, 40), 2, {})]
    img = make_custom(tmp_path / "src", kind, (240, 240), parts)
    analyze(img, tmp_path / "w")
    prepare(tmp_path / "w")
    return part(tmp_path / "w", "body")


def test_stripes_are_unreliable(tmp_path):
    body = _risk_case(tmp_path, "stripes")
    assert body["holdout_error"] > HOLDOUT_MAX and body["repair_reliable"] is False


def test_hidden_contour_is_unreliable(tmp_path):
    body = _risk_case(tmp_path, "contour")
    assert body["holdout_error"] < HOLDOUT_MAX  # 單色：紋理補得回來
    assert body["contour_hidden"] > CONTOUR_HIDDEN_MAX and body["repair_reliable"] is False  # 但形狀是猜的


# ---------- animation-quality ----------

def test_clean_character_has_no_anomalies(workcopy):
    """溫和的 idle 動畫：四類檢查都在門檻內，第 0 輪就通過。"""
    wd = workcopy("synth_b")
    assert quality.refine(wd, "idle")["status"] == "PASS"
    q = load_json(wd / "quality" / "quality_report.json")
    assert q["unresolved"] == [] and q["rounds"][0]["anomalies"] == []
    assert checks(wd)["animation_quality"]["status"] == "PASS"


def _assess(wd):
    ctx = quality._context(wd)
    skel = build_skeleton(wd)
    quality._prepare_context(ctx, skel)
    return ctx, skel, quality.assess(ctx, skel)[1]


def test_detects_joint_gap_and_attributes_it(built):
    """synth_b 的手臂只和身體重疊 2px，一轉動肩膀就透出細縫：要被抓到、歸因到那隻手臂，並且處理掉——
    縮小那隻手的幅度，或修不掉時判 BLOCKED。不能留著縫卻回報 PASS。"""
    wd = built("synth_b")
    q = load_json(wd / "quality" / "quality_report.json")
    gaps = [a for a in q["rounds"][0]["anomalies"] if a["kind"] == "gap" and a["subject"].startswith("arm_")]
    assert gaps and all(a["attributed_to"] == a["subject"] for a in gaps)
    arm = gaps[0]["subject"]
    if any(a["kind"] == "gap" and a["subject"] == arm for a in q["unresolved"]):
        assert checks(wd)["animation_quality"]["status"] == "BLOCKED"
    else:
        assert q["tuning"]["happy"][arm] < 1 and not any(a["kind"] == "gap" for a in q["rounds"][q["chosen_round"]]["anomalies"])


def test_detects_unreliable_repair_exposure(built):
    """synth_a 的 body 側邊被手臂蓋住（輪廓是猜的），抬手後露出 → 改為 needs_manual。"""
    wd = built("synth_a")
    q = load_json(wd / "quality" / "quality_report.json")
    assert "body" in q["downgraded_to_needs_manual"]
    body = part(wd, "body")
    assert body["status"] == "needs_manual" and "露出" in body["reason"]
    assert "body" in (wd / "repair_tasks.md").read_text(encoding="utf-8")
    assert checks(wd)["manual_repairs"]["status"] == "BLOCKED"
    frames = [a["frame"] for r in q["rounds"] for a in r["anomalies"]]
    assert frames and all(__import__("pathlib").Path(f).exists() for f in frames)


# ---------- motion-constraints ----------

def test_attach_to_unknown_part_is_rejected(tmp_path):
    img = make_custom(tmp_path, "c", (100, 100), [("head", rect(10, 10, 60, 60), (200, 0, 0), 1, {"attach": "ghost"})])
    r = analyze(img, tmp_path / "w")
    assert r["status"] == "needs_parts" and any("attach" in e for e in r["parts_errors"])


def test_attach_without_contact_refuses_rig(tmp_path):
    img, _ = make("synth_a", tmp_path / "src")
    doc = json.loads(img.with_suffix(".parts.json").read_text(encoding="utf-8"))
    for p in doc["parts"]:
        if p["name"] == "arm_l":
            p["attach"] = "leg_r"  # 不相鄰
    img.with_suffix(".parts.json").write_text(json.dumps(doc), encoding="utf-8")
    analyze(img, tmp_path / "w")
    prepare(tmp_path / "w")
    with pytest.raises(NeedsInput, match="沒有接觸"):
        build_rig(tmp_path / "w")


def _attached_synth(tmp_path):
    img, _ = make("synth_a", tmp_path / "src")
    doc = json.loads(img.with_suffix(".parts.json").read_text(encoding="utf-8"))
    for p in doc["parts"]:
        if p["name"] == "arm_l":
            p["attach"] = "body"
    img.with_suffix(".parts.json").write_text(json.dumps(doc), encoding="utf-8")
    wd = tmp_path / "w"
    analyze(img, wd)
    prepare(wd)
    build_rig(wd)
    return wd


def test_contact_limit_is_applied(tmp_path):
    """約束上限要真的套用到產生的關鍵影格：手臂最大轉角 × 關節到接觸點距離 ≤ 容許位移。"""
    wd = _attached_synth(tmp_path)
    build_animations(wd, "happy")
    rig = load_json(wd / "rig.json")
    c = rig["contacts"][0]
    world = {b["name"]: b["world"] for b in rig["bones"] if "world" in b}
    r = math.hypot(world["arm_l"][0] - c["point"][0], world["arm_l"][1] - c["point"][1])
    peak = max(abs(k.get("value", 0)) for k in load_json(wd / "animations.json")["happy"]["bones"]["arm_l"]["rotate"])
    assert 0 < math.radians(peak) * r <= CONTACT_TOL * rig["height"] * 1.01
    assert contact_limits(rig, "happy")["arm_l"] < 1


def test_separation_detected_without_constraint(tmp_path):
    """有約束時接觸維持；拿掉約束（同樣的動作）就會被偵測為分離，並歸因到手臂。"""
    wd = _attached_synth(tmp_path)
    build_animations(wd, "happy")
    ctx, skel, anomalies = _assess(wd)
    assert not [a for a in anomalies if a["kind"] == "attach"]
    rig = load_json(wd / "rig.json")
    contacts = rig.pop("contacts")
    save_json(wd / "rig.json", rig)
    build_animations(wd, "happy")
    rig["contacts"] = contacts
    save_json(wd / "rig.json", rig)  # 品質檢查仍以約束為準
    ctx, skel, anomalies = _assess(wd)
    sep = [a for a in anomalies if a["kind"] == "attach"]
    assert sep and quality.attribute(ctx, skel, sep[0]) == "arm_l"


# ---------- self-correction ----------

def test_refine_fixes_and_records_rounds(workcopy):
    """身體擠壓幅度 ×3，把不可靠的腿部補圖擠出來：歸因到 body、自動降低，但只因草稿露出時最多縮到 EXPOSURE_FLOOR；
    仍露出的草稿改列人工補畫（不默默留在動畫裡），每輪紀錄都在。"""
    wd = workcopy("synth_b")
    rig = load_json(wd / "rig.json")
    rig["motion"]["body"] = 3.0
    save_json(wd / "rig.json", rig)
    quality.refine(wd)
    q = load_json(wd / "quality" / "quality_report.json")
    first = [a for a in q["rounds"][0]["anomalies"] if a["kind"] == "exposure"]
    assert {a["subject"] for a in first} == {"leg_l", "leg_r"} and all(a["attributed_to"] == "body" for a in first)
    final = q["rounds"][q["chosen_round"]]["anomalies"]
    shown = {a["subject"] for a in final if a["kind"] == "exposure"}
    assert shown <= set(q["downgraded_to_needs_manual"])
    assert quality.EXPOSURE_FLOOR <= q["tuning"]["happy"]["body"] < 1 and load_json(wd / "tuning.json") == q["tuning"]
    assert len(q["rounds"]) <= quality.MAX_ROUNDS + 1


def test_refine_does_not_over_reduce(workcopy):
    """「過度縮小動作」：refine 結束後，任何被縮小的骨頭再放大 √2 倍，總異常量都會變多（否則就是縮過頭了）。"""
    wd = workcopy("synth_b")
    rig = load_json(wd / "rig.json")
    rig["motion"]["body"] = 3.0
    save_json(wd / "rig.json", rig)
    quality.refine(wd)
    q = load_json(wd / "quality" / "quality_report.json")
    final = load_json(wd / "tuning.json")
    assert final == q["tuning"] and final["happy"]["body"] < 1
    ctx = quality._context(wd)
    quality._prepare_context(ctx, build_skeleton(wd))
    score = lambda: sum(a["violation"] / a["threshold"] for a in quality.assess(ctx, build_skeleton(wd))[1])
    base = score()
    for anim, bones in final.items():
        for bone, factor in bones.items():
            save_json(wd / "tuning.json", {**final, anim: {**bones, bone: min(1.0, factor * math.sqrt(2))}})
            build_animations(wd, "happy")
            assert score() > base, f"{anim}/{bone} ×{factor} 還能放大而不增加異常"


def test_unfixable_is_blocked_with_evidence(workcopy, monkeypatch):
    wd = workcopy("synth_b")
    monkeypatch.setitem(quality.THRESHOLDS, "gap", -0.01)  # 讓每個關節都永遠「有縫」：修不掉
    r = quality.refine(wd)
    q = load_json(wd / "quality" / "quality_report.json")
    assert r["status"] == "BLOCKED" and q["unresolved"]
    assert all(__import__("pathlib").Path(a["frame"]).exists() for a in q["unresolved"])
    c = checks(wd)["animation_quality"]
    assert c["status"] == "BLOCKED" and "gap" in c["detail"]


def test_refine_is_deterministic(workcopy):
    wd = workcopy("synth_a")
    quality.refine(wd)
    first = (wd / "tuning.json").read_bytes(), (wd / "spine" / "character.json").read_bytes()
    quality.refine(wd)  # 每次從 1 開始，不會越乘越小
    assert ((wd / "tuning.json").read_bytes(), (wd / "spine" / "character.json").read_bytes()) == first


def test_stale_quality_report_is_not_trusted(workcopy):
    wd = workcopy("synth_b")
    assert checks(wd)["animation_quality"]["status"] != "NOT_TESTED"
    export(wd)  # 重新匯出後，舊報告不再代表目前的動畫
    assert checks(wd)["animation_quality"]["status"] == "NOT_TESTED"


def test_stale_report_after_prepare_and_animate(workcopy):
    for step in (lambda wd: prepare(wd), lambda wd: build_animations(wd, "happy")):
        wd = workcopy("synth_b")
        step(wd)
        assert checks(wd)["animation_quality"]["status"] == "NOT_TESTED"
        shutil.rmtree(wd)


def test_real_holes_only_count_what_a_departed_part_used_to_cover():
    """K-24：破洞 = 初始姿勢被某部件蓋住、現在透明、且那個部件已經不在旁邊的被包圍像素。
    初始姿勢就是背景的區域（長杖與帽簷、叉腰手臂圍出的空間）不論圍不圍得起來都不算；整體跳起不影響判定。"""
    import numpy as np
    eye = np.eye(3)
    ring = np.zeros((40, 40), np.float32); ring[5:35, 5:35] = 1; ring[12:28, 12:28] = 0
    patch = np.zeros((40, 40), np.float32); patch[12:28, 12:28] = 1
    ctx = {"scale": 1.0, "origin": (0.0, 0.0), "canvas": (40, 40), "setup_body": eye,
           "setup_alphas": {"body": ring, "patch": patch}}
    gone = {"alpha": ring, "alphas": {"body": ring, "patch": np.zeros_like(ring)}, "world": {"body": eye}, "dil": {}}
    assert quality._real_holes(ctx, gone).sum() == 16 * 16  # 蓋在中間的部件離開，露出身體上的洞

    up = eye.copy(); up[1, 2] = 3  # body 骨頭往上 3（Spine y 向上 = 畫面往上 3 列）
    lifted = np.roll(ring, -3, axis=0)
    jump = {"alpha": lifted, "alphas": {"body": lifted, "patch": np.zeros_like(ring)}, "world": {"body": up}, "dil": {}}
    assert quality._real_holes(ctx, jump).sum() == 16 * 16

    left = ring.copy(); left[:, 20:] = 0
    right = ring.copy(); right[:, :20] = 0
    ctx_bg = {**ctx, "setup_alphas": {"left": left, "right": right}}
    moved = np.roll(right, 1, axis=1)  # 右半邊微動：圍住的背景變大、也蓋過右半邊原本的位置
    swing = {"alpha": np.maximum(left, moved), "alphas": {"left": left, "right": moved}, "world": {"body": eye}, "dil": {}}
    assert quality._real_holes(ctx_bg, swing).sum() == 0


def _stick_rig(tmp_path, holders):
    """synth_a 加一根橫過雙手的棍子，holders 的手 attach 它。回傳綁好骨架的工作目錄。"""
    img, _ = make("synth_a", tmp_path / "src")
    doc = json.loads(img.with_suffix(".parts.json").read_text(encoding="utf-8"))
    for p in doc["parts"]:
        p["mask"] = str(img.parent / p["mask"])
        if p["name"] in holders:
            p["attach"] = "stick"
    doc["parts"].append({"name": "stick", "polygon": [[60, 250], [240, 250], [240, 262], [60, 262]], "z": 7, "role": "prop"})
    path = tmp_path / "p.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    wd = tmp_path / "w"
    analyze(img, wd, parts_path=path)
    prepare(wd)
    build_rig(wd)
    return wd


def test_single_hand_holds_prop_as_child(tmp_path):
    """K-28：只有一隻手 attach 道具（拿著夾板、書、長杖）→ 道具掛在手下跟著手動，手仍掛在身體上。
    接觸由骨架階層保證，所以只限制道具自己的旋轉，不為了接觸縮小手臂動作。"""
    wd = _stick_rig(tmp_path, ["arm_l"])
    rig = load_json(wd / "rig.json")
    parent = {b["name"]: b.get("parent") for b in rig["bones"]}
    assert parent["stick"] == "arm_l" and parent["arm_l"] == "body"
    limits = contact_limits(rig, "happy")
    assert "arm_l" not in limits and "stick" in limits


def test_gap_joint_follows_skeleton_not_largest_contact(workcopy):
    """K-24：縫隙要量骨架上的關節（手臂接身體），不是碰巧接觸面積最大的部件（手指碰到角、手靠著尾巴）。"""
    wd = workcopy("synth_b")
    ctx = quality._context(wd)
    quality._prepare_context(ctx, build_skeleton(wd))
    joints = {c: a for c, a, _ in ctx["joints"]}
    assert joints["arm_r"] == "body"  # 旗子（prop）與手的接觸比肩膀大，但手臂的關節在身體
    assert joints["hair_back"] == "head"


def test_refine_is_deterministic_with_fixes(workcopy):
    wd = workcopy("synth_b")
    rig = load_json(wd / "rig.json")
    rig["motion"]["body"] = 3.0
    save_json(wd / "rig.json", rig)
    quality.refine(wd)
    first = load_json(wd / "tuning.json")
    assert first  # 有實際修正
    quality.refine(wd)
    assert load_json(wd / "quality" / "quality_report.json")["rounds"][0]["tuning"] == {}  # 每次都從 1 開始
    assert load_json(wd / "tuning.json") == first


def test_detects_interpenetration(built):
    """synth_b 的旗子（道具）揮進頭部：要被抓到、歸因到拿旗子的手臂；修不掉就 BLOCKED。"""
    q = load_json(built("synth_b") / "quality" / "quality_report.json")
    first = {a["subject"]: a for a in q["rounds"][0]["anomalies"] if a["kind"] == "intrude"}
    assert "flag+head" in first and first["flag+head"]["attributed_to"] == "arm_r"
    assert not any("hair_back" in s for s in first)  # 頭髮是背景層，不算穿插


def test_sidecar_edit_requires_reanalyze(tmp_path):
    import os, time
    img, _ = make("synth_a", tmp_path / "src")
    wd = tmp_path / "w"
    analyze(img, wd)
    sidecar = img.with_suffix(".parts.json")
    later = time.time() + 5
    os.utime(sidecar, (later, later))  # 模擬之後改過正式 parts.json
    with pytest.raises(NeedsInput, match="重新執行 c2s analyze"):
        prepare(wd)


def test_unreliable_exposure_within_threshold_is_reported(built):
    """不可靠的補圖即使露出量在門檻內，也要在報告與修補任務中列出，不能默默算成功。"""
    wd = built("synth_b")
    watch = load_json(wd / "quality" / "quality_report.json")["unreliable_exposed_within_threshold"]
    assert watch and all(0 < v <= quality.THRESHOLDS["exposure"] for v in watch.values())
    assert "建議目視" in checks(wd)["animation_quality"]["detail"]
    assert "建議目視" in (wd / "repair_tasks.md").read_text(encoding="utf-8")


def test_override_backup(tmp_path):
    from PIL import Image
    img, _ = make("synth_a", tmp_path / "src")
    wd = tmp_path / "w"
    analyze(img, wd)
    prepare(wd)
    for i, color in enumerate(((1, 2, 3, 255), (9, 9, 9, 255))):
        p = tmp_path / f"fix{i}.png"
        Image.new("RGBA", Image.open(wd / "layers" / "head.png").size, color).save(p)
        prepare(wd, replace={"head": p})
    odir = tmp_path / "src" / "synth_a.overrides"
    assert Image.open(odir / "head.png.bak").getpixel((0, 0)) == (1, 2, 3, 255)
    assert Image.open(odir / "head.png").getpixel((0, 0)) == (9, 9, 9, 255)

def test_prop_carries_hugging_arms(tmp_path):
    """雙手抱著道具（樂器）：兩隻手都掛在道具骨頭下，道具擺動帶著手、接觸處沒有相對移動，所以道具不受接觸約束限制，手仍受限制。"""
    wd = _stick_rig(tmp_path, ["arm_l", "arm_r"])
    rig = load_json(wd / "rig.json")
    parent = {b["name"]: b.get("parent") for b in rig["bones"]}
    assert parent["arm_l"] == parent["arm_r"] == "stick" and parent["stick"] == "body"
    limits = contact_limits(rig, "happy")
    assert "arm_l" in limits and "arm_r" in limits and "stick" not in limits


def test_needs_manual_drafts_are_kept_out_of_view(workcopy):
    """需人工部件的草稿在補畫前也不該被動畫露出：refine 要抓到並嘗試修正，但不重複降級、不改寫原因。"""
    wd = workcopy("synth_a")
    reason = part(wd, "body")["reason"]
    assert part(wd, "body")["status"] == "needs_manual"
    quality.refine(wd)
    q = load_json(wd / "quality" / "quality_report.json")
    assert any(a["kind"] == "exposure" and a["subject"] == "body" for a in q["rounds"][0]["anomalies"])
    assert "body" not in q["downgraded_to_needs_manual"] and part(wd, "body")["reason"] == reason


def test_carried_arm_strums(tmp_path):
    """被道具帶著的手（雙手抱樂器）改用撥弦節奏：Happy 的轉角來回變號多次；單手拿著道具的手仍是一般揮手。"""
    def arm_l_values(holders, sub):
        wd = _stick_rig(tmp_path / sub, holders)
        build_animations(wd, "happy")
        return [k.get("value", 0) for k in load_json(wd / "animations.json")["happy"]["bones"]["arm_l"]["rotate"]]
    values = arm_l_values(["arm_l", "arm_r"], "hug")
    signs = [v > 0 for v in values if v]
    assert sum(a != b for a, b in zip(signs, signs[1:])) >= 8
    held = arm_l_values(["arm_l"], "hold")
    assert len([v for v in held if v]) < len([v for v in values if v])
