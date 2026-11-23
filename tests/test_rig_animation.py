"""spec: auto-rigging、animation-builder"""
import json

import pytest

from character_to_spine import C2SError, NeedsInput, load_json, save_json
from character_to_spine.analyzer import analyze
from character_to_spine.animation_builder import build_animations, duration
from character_to_spine.image_processor import prepare
from character_to_spine.rig_builder import PRESETS, build_rig

REQUIRED_BONES = ["root", "hip", "body", "head", "arm_l", "arm_r", "leg_l", "leg_r"]


def bones(wd):
    return {b["name"]: b for b in load_json(wd / "rig.json")["bones"]}


def test_required_bones_follow_pivots(built):
    for name in ("synth_a", "synth_b"):
        wd = built(name)
        meta = load_json(wd / "metadata.json")
        ox, oy = meta["origin"]
        bs = bones(wd)
        assert set(REQUIRED_BONES) <= set(bs)
        for e in meta["parts"]:
            if "file" in e:
                px, py = e["pivot"]
                assert bs[e["name"]]["world"][:2] == pytest.approx([px - ox, oy - py], abs=0.05)


def test_custom_pivot(synth, tmp_path):
    img, _ = synth("synth_a")
    doc = json.loads(img.with_suffix(".parts.json").read_text(encoding="utf-8"))
    for p in doc["parts"]:
        p["mask"] = str(img.parent / p["mask"])
        if p["name"] == "head":
            p["pivot"] = [151, 170]
    path = tmp_path / "p.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    wd = tmp_path / "w"
    analyze(img, wd, parts_path=path)
    prepare(wd)
    build_rig(wd)
    ox, oy = load_json(wd / "metadata.json")["origin"]
    assert bones(wd)["head"]["world"][:2] == pytest.approx([151 - ox, oy - 170], abs=0.05)


def test_extra_parts_get_bones(built):
    wd = built("synth_b")
    bs = bones(wd)
    assert bs["hair_back"]["parent"] == "head" and bs["flag"]["parent"] == "arm_r"
    assert {"hair_back", "flag"} <= {s["name"] for s in load_json(wd / "rig.json")["slots"]}


def test_unknown_parent(workcopy):
    wd = workcopy("synth_b")
    meta = load_json(wd / "metadata.json")
    for e in meta["parts"]:
        if e["name"] == "flag":
            e["parent"] = "tail"
    save_json(wd / "metadata.json", meta)
    with pytest.raises(C2SError, match="flag"):
        build_rig(wd)


def test_slot_order_by_z(built):
    wd = built("synth_b")
    meta = {e["name"]: e["z"] for e in load_json(wd / "metadata.json")["parts"]}
    order = [s["name"] for s in load_json(wd / "rig.json")["slots"]]
    assert order == sorted(order, key=meta.get)
    assert order.index("body") < order.index("head") < order.index("arm_l")


def test_missing_required_layer_refuses(workcopy):
    wd = workcopy("synth_a")
    meta = load_json(wd / "metadata.json")
    for e in meta["parts"]:
        if e["name"] == "leg_r":
            e.pop("file")
    save_json(wd / "metadata.json", meta)
    (wd / "rig.json").unlink()
    with pytest.raises(NeedsInput, match="leg_r"):
        build_rig(wd)
    assert not (wd / "rig.json").exists()


# ---- animation-builder ----

def anim(wd, name="happy"):
    return load_json(wd / "animations.json")[name]


def test_happy_contents(built):
    a = anim(built("synth_a"))
    assert duration(a) >= 2.0
    b = a["bones"]
    assert "translate" in b["hip"] and "scale" in b["body"]
    assert all("rotate" in b[n] for n in ("head", "arm_l", "arm_r"))
    assert "idle" in load_json(built("synth_a") / "animations.json")


def test_loops_and_keys_are_editable(built):
    for name in ("synth_a", "synth_b"):
        for an, a in load_json(built(name) / "animations.json").items():
            for bone, tls in a["bones"].items():
                for tl, keys in tls.items():
                    times = [k.get("time", 0) for k in keys]
                    assert times == sorted(set(times)) and 2 <= len(keys) <= 16, (an, bone, tl)
                    chans = ["value"] if tl == "rotate" else ["x", "y"]
                    first = [keys[0].get(c, 1 if tl == "scale" else 0) for c in chans]
                    last = [keys[-1].get(c, 1 if tl == "scale" else 0) for c in chans]
                    assert first == pytest.approx(last), (an, bone, tl)
                    for k in keys[:-1]:
                        assert len(k["curve"]) == 4 * len(chans)


def peak(keys, channel):
    return max(abs(k.get(channel, 0)) for k in keys)


def test_amplitude_scales_with_height(workcopy):
    wd = workcopy("synth_a")
    p1 = peak(anim(wd)["bones"]["hip"]["translate"], "y")
    rig = load_json(wd / "rig.json")
    rig["height"] *= 2
    save_json(wd / "rig.json", rig)
    build_animations(wd, "happy")
    assert peak(anim(wd)["bones"]["hip"]["translate"], "y") == pytest.approx(2 * p1, rel=0.02)


def test_left_right_mirror(built):
    b = anim(built("synth_a"))["bones"]
    for kl, kr in zip(b["arm_l"]["rotate"], b["arm_r"]["rotate"]):
        if kl.get("value"):
            assert kl["value"] == pytest.approx(-kr["value"])


def test_motion_factor(workcopy):
    wd = workcopy("synth_a")
    base = peak(anim(wd)["bones"]["arm_l"]["rotate"], "value")
    rig = load_json(wd / "rig.json")
    rig["motion"]["arm_l"] = 0.2
    save_json(wd / "rig.json", rig)
    build_animations(wd, "happy")
    assert peak(anim(wd)["bones"]["arm_l"]["rotate"], "value") == pytest.approx(0.2 * base, rel=0.02)


def test_secondary_motion_for_hair(built):
    assert "rotate" in anim(built("synth_b"))["bones"]["hair_back"]


def test_absent_bones_skipped(built):
    rig_bones = set(bones(built("synth_a")))
    for a in load_json(built("synth_a") / "animations.json").values():
        assert set(a["bones"]) <= rig_bones
