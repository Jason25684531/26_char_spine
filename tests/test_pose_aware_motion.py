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
