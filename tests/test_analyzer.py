"""spec: character-analyzer"""
import hashlib
import json

import numpy as np
import pytest
from PIL import Image

from character_to_spine import C2SError, cli, load_json
from character_to_spine.analyzer import analyze
from character_to_spine.rig_builder import PRESETS

REQUIRED = PRESETS["humanoid-chibi"]["required"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_transparent_png_keeps_original(synth, tmp_path):
    img, _ = synth("synth_a")
    before = sha(img)
    r = analyze(img, tmp_path)
    assert r["alpha_source"] == "embedded" and r["status"] == "ok"
    assert (tmp_path / "source_rgba.png").exists() and (tmp_path / "analysis.json").exists()
    assert Image.open(tmp_path / "grid_overlay.png").size == Image.open(img).size
    assert sha(img) == before


def test_opaque_background_flood_fill(synth, tmp_path):
    img, truth = synth("synth_b")
    r = analyze(img, tmp_path)
    assert r["alpha_source"] == "flood-fill"
    alpha = np.array(Image.open(tmp_path / "source_rgba.png"))[..., 3]
    x, y, w, h = truth["body"]
    assert alpha[y + h // 2, x + w // 2] == 255 and alpha[0, 0] == 0 and alpha[-1, -1] == 0


def test_missing_or_empty_image(tmp_path):
    assert cli.main(["analyze", str(tmp_path / "nope.png"), "-w", str(tmp_path / "w1")]) == 1
    empty = tmp_path / "empty.png"
    Image.new("RGBA", (50, 50), (0, 0, 0, 0)).save(empty)
    with pytest.raises(C2SError):
        analyze(empty, tmp_path / "w2")
    assert not (tmp_path / "w2" / "analysis.json").exists()


def test_valid_parts_normalized(synth, tmp_path):
    img, _ = synth("synth_a")
    r = analyze(img, tmp_path)
    parts = load_json(tmp_path / "parts.json")["parts"]
    assert r["status"] == "ok" and sorted(r["parts"]) == sorted(REQUIRED)
    assert all(p["mask"].startswith(str(img.parent.resolve())) for p in parts)


def _with_parts(img, tmp_path, mutate):
    doc = json.loads(img.with_suffix(".parts.json").read_text(encoding="utf-8"))
    mutate(doc["parts"])
    for p in doc["parts"]:  # 遮罩改成絕對路徑，parts.json 才能放在別處
        if "mask" in p:
            p["mask"] = str(img.parent / p["mask"])
    path = tmp_path / "custom.parts.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return analyze(img, tmp_path / "w", parts_path=path)


@pytest.mark.parametrize("mutate, expect", [
    (lambda ps: ps.append(dict(ps[0])), "名稱重複"),
    (lambda ps: ps[0].pop("z"), "z"),
    (lambda ps: ps.append({"name": "tail", "polygon": [[0, 0], [1, 1]], "z": 9}), "polygon"),
    (lambda ps: ps[0].update(mask="no_such_mask.png"), "找不到遮罩"),
    (lambda ps: ps.append({"name": "bad_role", "polygon": [[0, 0], [5, 0], [5, 5]], "z": 9, "role": "wing"}), "role"),
    (lambda ps: ps.append({"name": "bad_motion", "polygon": [[0, 0], [5, 0], [5, 5]], "z": 9, "motion": -1}), "motion"),
    (lambda ps: ps.append({"name": "root", "polygon": [[0, 0], [5, 0], [5, 5]], "z": 9}), "保留名稱"),
    (lambda ps: ps.append({"name": "badge", "polygon": [[0, 0], [5, 0], [5, 5]], "z": 1}), "z=1"),
    (lambda ps: ps.append({"name": "blob", "polygon": [[0, 0], [5, 0], "x"], "z": 9}), "polygon"),
])
def test_parts_format_errors(synth, tmp_path, mutate, expect):
    img, _ = synth("synth_a")
    r = _with_parts(img, tmp_path, mutate)
    assert r["status"] == "needs_parts"
    assert any(expect in e for e in r["parts_errors"]), r["parts_errors"]


def test_mask_size_mismatch(synth, tmp_path):
    img, _ = synth("synth_a")
    small = tmp_path / "small.png"
    Image.new("L", (10, 10), 255).save(small)
    r = _with_parts(img, tmp_path, lambda ps: ps[0].update(mask=str(small)))
    assert any(e.startswith("leg_l:") and "尺寸" in e for e in r["parts_errors"]), r["parts_errors"]


def test_no_parts_json_template_and_exit_2(tmp_path):
    img = tmp_path / "lonely.png"
    im = Image.new("RGBA", (40, 60), (0, 0, 0, 0))
    im.paste((200, 0, 0, 255), (10, 10, 30, 50))
    im.save(img)
    r = analyze(img, tmp_path / "w")
    assert r["status"] == "needs_parts" and r["missing_required"] == REQUIRED
    assert (tmp_path / "w" / "parts.template.json").exists() and any("c2s prepare" in s for s in r["next_steps"])
    assert cli.main(["analyze", str(img), "-w", str(tmp_path / "w")]) == 2


def test_workdir_parts_json_wins_over_sidecar(synth, tmp_path):
    img, _ = synth("synth_a")
    analyze(img, tmp_path)  # 第一次：從圖片旁的 parts.json 匯入
    doc = load_json(tmp_path / "parts.json")
    doc["parts"][0]["pivot"] = [1, 2]  # 使用者照指示修改工作目錄內的版本
    (tmp_path / "parts.json").write_text(json.dumps(doc), encoding="utf-8")
    analyze(img, tmp_path)
    assert load_json(tmp_path / "parts.json")["parts"][0]["pivot"] == [1, 2]


def test_partial_required(synth, tmp_path):
    img, _ = synth("synth_a")
    def drop(ps):
        ps[:] = [p for p in ps if p["name"] not in ("leg_l", "arm_r")]
    r = _with_parts(img, tmp_path, drop)
    assert r["status"] == "needs_parts" and sorted(r["missing_required"]) == ["arm_r", "leg_l"]
