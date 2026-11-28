"""Spine-SKILL 落實到程式的動作規則：循環接縫有速度、落地有速度、腳不沉進地面、樞軸在相接處、跟隨延遲。"""
import json

import numpy as np
import pytest

from character_to_spine import load_json
from character_to_spine.analyzer import analyze
from character_to_spine.animation_builder import build_animations, duration
from character_to_spine.preview import _sample, world_matrices
from character_to_spine.spine_exporter import build_skeleton

EPS = 0.01


def velocity(keys, kind, channel, t):
    return (_sample(keys, kind, t + EPS)[channel] - _sample(keys, kind, t - EPS)[channel]) / (2 * EPS)


def test_loop_seam_keeps_speed(built):
    """數值穿越循環接縫的通道（例如點頭從 -1.5° 經過 0 到 +1.5°），接縫處不能停住，兩側速度一致；
    平切線版本在這裡速度為 0，每一圈都會頓一下。"""
    checked = 0
    for name in ("synth_a", "synth_b"):
        for an, a in load_json(built(name) / "animations.json").items():
            end = duration(a)
            for bone, tls in a["bones"].items():
                for tl, keys in tls.items():
                    for c in (["value"] if tl == "rotate" else ["x", "y"]):
                        f = lambda t: _sample(keys, tl, t)[c]  # noqa: E731
                        before, after = f(end) - f(end - 0.05), f(0.05) - f(0)
                        if before * after <= 0 or min(abs(before), abs(after)) < 1e-3:
                            continue  # 接縫是極值或靜止：速度本來就該是 0
                        e = 0.002
                        v_in, v_out = (f(end) - f(end - e)) / e, (f(e) - f(0)) / e
                        assert abs(v_in) >= 0.3 * abs(before) / 0.05 and abs(v_in - v_out) <= 0.3 * max(abs(v_in), abs(v_out)), (name, an, bone, tl, c, v_in, v_out)
                        checked += 1
    assert checked >= 3  # idle 的頭、頭髮、飾品都在接縫穿越 0


def test_landing_keeps_downward_speed(built):
    """Happy 著地（0.8s）時 hip 仍在往下，不是飄著停在地面。"""
    hip = load_json(built("synth_a") / "animations.json")["happy"]["bones"]["hip"]["translate"]
    assert velocity(hip, "translate", "y", 0.8) < 0


def test_feet_do_not_sink(built):
    """蹲下與落地時腿不跟著 hip 沉進地面。"""
    wd = built("synth_a")
    skel = build_skeleton(wd)
    rest = {n: world_matrices(skel)[n][1, 2] for n in ("leg_l", "leg_r")}
    h = load_json(wd / "rig.json")["height"]
    for an in ("idle", "happy"):
        for t in np.arange(0, duration(skel["animations"][an]), 0.05):
            w = world_matrices(skel, an, t)
            for n, y in rest.items():
                assert w[n][1, 2] >= y - 0.002 * h, (an, t, n)


def test_secondary_pivot_at_parent_contact(built):
    """沒寫 pivot 的頭髮掛在它與頭部相接的地方，不在自己裁切框的中心。"""
    meta = {e["name"]: e for e in load_json(built("synth_b") / "metadata.json")["parts"]}
    hair = meta["hair_back"]
    center = (hair["x"] + hair["w"] / 2, hair["y"] + hair["h"] / 2)
    assert hair["pivot"] != [round(center[0], 1), round(center[1], 1)]
    head = meta["head"]
    assert head["x"] <= hair["pivot"][0] <= head["x"] + head["w"] and head["y"] <= hair["pivot"][1] <= head["y"] + head["h"]


def test_hair_peaks_after_body_lowest(built):
    """落地壓到最低點之後，頭髮才甩到最大（跟隨），而不是和身體同時。"""
    a = load_json(built("synth_b") / "animations.json")["happy"]["bones"]
    ts = np.arange(0.45, 1.2, 0.01)
    hip = np.array([_sample(a["hip"]["translate"], "translate", t)["y"] for t in ts])
    low = ts[np.argmin(hip)]
    near = ts[(ts > low - 0.15) & (ts < low + 0.3)]
    hair = [abs(_sample(a["hair_back"]["rotate"], "rotate", t)["value"]) for t in near]
    assert near[int(np.argmax(hair))] > low


def _peak(keys, channel):
    return max(abs(k.get(channel, 0)) for k in keys)


def test_motion_overrides_from_natural_language(workcopy):
    """「Happy 更活潑、頭髮多擺一點」→ parts.json 的 motion_overrides：Happy 整體與頭髮的量都變大，Idle 不變。"""
    wd = workcopy("synth_b")
    before = load_json(wd / "animations.json")
    doc = load_json(wd / "parts.json")
    doc["motion_overrides"] = {"happy": {"energy": 1.3, "hair": 1.5}}
    (wd / "parts.json").write_text(json.dumps(doc), encoding="utf-8")
    build_animations(wd, "happy")
    after = load_json(wd / "animations.json")
    hip = lambda a: _peak(a["happy"]["bones"]["hip"]["translate"], "y")  # noqa: E731
    hair = lambda a: _peak(a["happy"]["bones"]["hair_back"]["rotate"], "value")  # noqa: E731
    assert hip(after) == pytest.approx(1.3 * hip(before), rel=0.01)
    assert hair(after) == pytest.approx(1.95 * hair(before), rel=0.01)
    assert after["idle"] == before["idle"]


@pytest.mark.parametrize("bad, expect", [
    ({"happy": {"energy": 9}}, "0～2.5"),
    ({"happy": {"wings": 1.2}}, "wings"),
    ({"dance": {"energy": 1.2}}, "dance"),
])
def test_motion_overrides_validated(synth, tmp_path, bad, expect):
    img, _ = synth("synth_b")
    doc = json.loads(img.with_suffix(".parts.json").read_text(encoding="utf-8"))
    doc["motion_overrides"] = bad
    path = tmp_path / "p.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    r = analyze(img, tmp_path / "w", str(path))
    assert r["status"] == "needs_parts" and any(expect in e for e in r["parts_errors"]), r["parts_errors"]
