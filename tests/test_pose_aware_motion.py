"""H7：地面影子不跟著角色跳，也不算角色身體。"""
from character_to_spine import load_json, pipeline
from synthetic import make_custom


def rect(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def _character(tmp_path, extra=()):
    parts = [
        ("leg_l", rect(170, 300, 198, 380), (60, 60, 140), 1, {"pivot": [184, 302]}),
        ("leg_r", rect(212, 300, 240, 380), (60, 60, 150), 2, {"pivot": [226, 302]}),
        ("body", rect(160, 200, 250, 310), (200, 80, 80), 3, {"pivot": [205, 300]}),
        ("head", [[165, 120], [245, 120], [250, 205], [160, 205]], (250, 215, 180), 4, {"pivot": [205, 204]}),
        ("arm_l", rect(130, 205, 168, 290), (240, 200, 170), 5, {"pivot": [160, 212]}),
        ("arm_r", rect(244, 205, 282, 290), (235, 195, 160), 6, {"pivot": [250, 212]}),
        *extra,
    ]
    img = make_custom(tmp_path, "pose", (420, 440), parts)
    pipeline.run(img, "happy", workdir=tmp_path / "w")
    return tmp_path / "w"


def test_ground_shadow_stays_on_ground(tmp_path):
    wd = _character(tmp_path, [("shadow", [[150, 372], [260, 372], [270, 392], [140, 392]], (120, 120, 120), 0, {})])
    rig = load_json(wd / "rig.json")
    assert next(b for b in rig["bones"] if b["name"] == "shadow")["parent"] == "root"
    happy = load_json(wd / "animations.json")["happy"]["bones"]
    assert "translate" not in happy.get("shadow", {}), "影子不跟著跳"
    assert "scale" in happy["shadow"], "角色跳起時影子縮小"



def _peak(keys):
    return max(abs(k.get("value", 0)) for k in keys)


def test_raised_arm_waves_instead_of_swinging_over_head(tmp_path):
    """Happy 舉手依初始姿勢：下垂的手舉到外側略高於水平，已經舉起的手只小幅揮動（照模板再轉 110° 會甩過頭）。"""
    parts = [
        ("leg_l", rect(170, 300, 198, 380), (60, 60, 140), 1, {"pivot": [184, 302]}),
        ("leg_r", rect(212, 300, 240, 380), (60, 60, 150), 2, {"pivot": [226, 302]}),
        ("body", rect(160, 200, 250, 310), (200, 80, 80), 3, {"pivot": [205, 300]}),
        ("head", [[165, 120], [245, 120], [250, 205], [160, 205]], (250, 215, 180), 4, {"pivot": [205, 204]}),
        ("arm_l", rect(150, 205, 168, 290), (240, 200, 170), 5, {"pivot": [160, 212]}),  # 垂直下垂
        ("arm_r", rect(244, 130, 262, 215), (235, 195, 160), 6, {"pivot": [250, 212]}),  # 往上舉
    ]
    pipeline.run(make_custom(tmp_path, "raised", (420, 440), parts), "happy", workdir=tmp_path / "w")
    happy = load_json(tmp_path / "w" / "animations.json")["happy"]["bones"]
    assert _peak(happy["arm_l"]["rotate"]) > 100, "下垂的手照模板舉滿"
    assert 25 <= _peak(happy["arm_r"]["rotate"]) <= 40, "已舉起的手小幅揮動，不是不動，也不是轉 110°"


def test_squash_keeps_hem_on_legs(tmp_path):
    """擠壓伸展時 body 下緣（裙襬、長袍）相對於腿不動：以腰為中心縮放會讓下襬往上縮，露出底下的腿。"""
    import numpy as np
    from character_to_spine.preview import _matrix, world_matrices
    wd = _character(tmp_path)
    skel = load_json(wd / "spine" / "character.json")
    att = skel["skins"][0]["attachments"]["body"]["body"]
    hem = np.array([0, -att["height"] / 2, 1])  # 附件本地座標的下緣中央

    def hem_on_hip(t):
        w = world_matrices(skel, "happy", t)
        local = _matrix(att.get("x", 0), att.get("y", 0), att.get("rotation", 0)) @ hem
        return (np.linalg.inv(w["hip"]) @ w["body"] @ local)[:2]
    happy = load_json(wd / "animations.json")["happy"]["bones"]["body"]
    crouch = next(k["time"] for k in happy["scale"] if k.get("time"))  # 第一個壓扁影格
    assert np.abs(hem_on_hip(crouch) - hem_on_hip(0)).max() < 0.5
