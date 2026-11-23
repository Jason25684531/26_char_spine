import re
import subprocess
import sys
from pathlib import Path

import pytest

from character_to_spine import load_json, quality
from character_to_spine.animation_builder import duration

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "visual_report.py"
ROW = re.compile(r"^\| \d+ \| `([^`]+)` \| [^|]+ \| ([\d.]+)% \|")


@pytest.fixture(scope="module")
def report(built, tmp_path_factory):
    wd, out = built("synth_b"), tmp_path_factory.mktemp("report")
    subprocess.run([sys.executable, str(SCRIPT), str(wd), "--out", str(out)], check=True)
    sections = {}
    for chunk in (out / "repair_priority.md").read_text(encoding="utf-8").split("\n## ")[1:]:
        title, body = chunk.split("\n", 1)
        sections[title] = [(m[1], float(m[2])) for m in map(ROW.match, body.splitlines()) if m]
    return wd, out, sections


def test_lists_every_risky_part_with_its_image(report):
    wd, out, sections = report
    parts = load_json(wd / "metadata.json")["parts"]
    expected = {e["name"] for e in parts if e["status"] == "needs_manual"
                or (e["status"] == "auto_repaired" and e.get("repair_reliable") is False)}
    listed = {name for rows in sections.values() for name, _ in rows}
    assert listed == expected and expected
    assert all((out / f"repair_{name}.png").exists() for name in listed)
    assert (out / "visual_check.png").exists()


def test_parts_are_ranked_by_exposure(report):
    for rows in report[2].values():
        values = [v for _, v in rows]
        assert values == sorted(values, reverse=True)


def test_reported_exposure_matches_recomputation(report):
    wd, _, sections = report
    rows = dict(next(rows for title, rows in sections.items() if "needs_manual" in title))
    name = next(n for n in rows if (wd / "layers" / f"{n}.png").exists())
    ctx = quality._context(wd)
    skel = load_json(wd / "spine" / "character.json")

    def seen(anim, t):
        f = quality._frame(ctx, skel, anim, t)
        return float((f["masks"][name] * f["vis"][name]).sum()) if f["masks"].get(name) is not None else 0.0, f

    base, setup = seen(None, 0.0)
    area = max(1.0, float((setup["alphas"][name] > 0.5).sum()))
    worst = 0.0
    for anim, data in skel["animations"].items():
        keys = {k.get("time", 0) for tls in data["bones"].values() for ks in tls.values() for k in ks}
        for t in {round(i / quality.FPS, 4) for i in range(round(duration(data) * quality.FPS) + 1)} | keys:
            worst = max(worst, (seen(anim, t)[0] - base) / area)
    assert rows[name] == pytest.approx(worst * 100, abs=0.006)

    # quality.assess 也量過不可靠補圖的露出（採用那一輪的 worst）：兩邊應一致
    q = load_json(wd / "quality" / "quality_report.json")
    worst = q["rounds"][q["chosen_round"]]["worst"]
    unreliable = dict(next(rows for title, rows in sections.items() if "不可靠" in title))
    checked = [n for n in unreliable if f"exposure:{n}" in worst]
    assert checked
    for n in checked:
        assert unreliable[n] == pytest.approx(worst[f"exposure:{n}"]["value"] * 100, abs=0.011)
