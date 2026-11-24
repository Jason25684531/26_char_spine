"""泛化測試執行器：用同一套 c2s 處理 manifest 的每個案例與既有兩組角色，量測、判定、產生報告。

python scripts/generalization.py skill <id> [--slash]   用全新的 Claude Code session 處理新圖（Skill 實測，產生 parts.json）
python scripts/generalization.py run [id ...]           c2s run → 量測 → 視覺驗收圖 → results.json
python scripts/generalization.py snapshot <label>       保存目前的 results.json 與視覺驗收圖，供前後比較
python scripts/generalization.py report [--compare a b] 由 results.json 產生 docs/GENERALIZATION_TEST_MATRIX.md

判定等級：PASS／PARTIAL／FAIL／BLOCKED／UNSUPPORTED／NOT_TESTED（規則見 GRADE_RULES）。
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from character_to_spine import load_json, save_json  # noqa: E402
from character_to_spine.animation_builder import duration  # noqa: E402
from character_to_spine.analyzer import ALPHA_MIN, load_rgba  # noqa: E402
from character_to_spine.image_processor import part_mask  # noqa: E402
from character_to_spine.preview import framing, render, world_matrices  # noqa: E402
from motion_metrics import fill_exposure, limb_travel  # noqa: E402

SET = ROOT / "examples" / "generalization"
OUT = ROOT / "output" / "generalization"
DOCS = ROOT / "docs" / "generalization"
C2S = ROOT / ".venv" / "Scripts" / "c2s.exe"
LEGACY = {"ren": ROOT / "examples" / "real" / "人.png", "zc2": ROOT / "examples" / "real" / "转场2.png"}
FONT = "C:/Windows/Fonts/msjh.ttc"
REQUIRED_FIELDS = ("id", "type", "file", "sha256", "origin", "source_url", "license", "author", "features", "expected_scope")
# Spine 正式輸出需要完整版授權（K-01），與泛化能力無關，判定時不計
SPINE_CHECKS = {"spine_import", "spine_roundtrip", "spine_editable"}
FORBIDDEN = ("examples/real", "examples\\real", "examples/synthetic", "examples\\synthetic", "人.parts", "转场2.parts",
             "synth_a", "synth_b", "tests/", "tests\\", "output/ren", "output\\ren", "output/zc2", "output\\zc2",
             "Character-to-Spine-Deliverables", "visual_review.json", "manifest.json")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def manifest():
    return load_json(SET / "manifest.json")


def cases():
    """{id: (圖片路徑, manifest 項目或 None)}，既有兩組角色排在最後。"""
    out = {c["id"]: (SET / c["file"], c) for c in manifest()["cases"]}
    out.update({k: (v, None) for k, v in LEGACY.items()})
    return out


def check_case(case):
    """manifest 項目的問題清單（空 = 可以執行）。"""
    problems = [f"缺少欄位 {f}" for f in REQUIRED_FIELDS if not case.get(f)]
    img = SET / case.get("file", "")
    if not img.is_file():
        return problems + [f"找不到圖片 {img}"]
    if case.get("sha256") and sha256(img) != case["sha256"]:
        problems.append("圖片雜湊與 manifest 不符")
    excluded = set(manifest().get("excluded_sha256", []))
    if sha256(img) in excluded:
        problems.append("這張圖是參與過開發的既有角色")
    return problems


# ---------- Skill 實測 ----------

def skill(case_id, slash=False):
    """在只有 Skill 與圖片的乾淨沙盒裡開一個全新的 Claude Code session（c2s 經由 PATH 可用）。
    真實使用者的專案裡沒有本專案的範例角色、測試與案例描述，沙盒重現這個條件。"""
    img, case = cases()[case_id]
    tag = "slash" if slash else "nl"
    box = OUT / case_id / f"sandbox_{tag}"
    shutil.rmtree(box, ignore_errors=True)
    shutil.copytree(ROOT / "skills" / "character-to-spine", box / ".claude" / "skills" / "character-to-spine")
    shutil.copy(img, box / img.name)
    prompt = f"/character-to-spine {img.name}" if slash else f"幫我把這張角色圖做成 Spine 動畫：{img.name}"
    raw = OUT / case_id / f"skill_{tag}.jsonl"
    n = 1 + len(list(raw.parent.glob(f"skill_{tag}.run*.jsonl")))
    for old in (raw, raw.with_suffix(".json"), DOCS / case_id / f"skill_session_{tag}.md"):
        if old.exists():  # 重跑不覆寫先前的紀錄
            shutil.move(old, old.with_name(f"{old.stem}.run{n}{old.suffix}"))
    cmd = ["claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--no-session-persistence",
           "--permission-mode", "acceptEdits",
           "--allowedTools", "Read", "Write", "Edit", "Glob", "Grep", "Skill", "Bash", "PowerShell"]
    env = {**os.environ, "PATH": str(ROOT / ".venv" / "Scripts") + os.pathsep + os.environ["PATH"]}
    with raw.open("w", encoding="utf-8") as f:
        proc = subprocess.run(cmd, cwd=box, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=3600,
                              shell=sys.platform == "win32")
    result = box / f"{img.stem}.parts.json"
    if result.exists():
        dest = OUT / case_id / f"{img.stem}.slash.parts.json" if slash else img.with_suffix(".parts.json")
        if dest.exists():
            shutil.move(dest, dest.with_name(f"{img.stem}.before_run{n}.parts.json"))
        shutil.copy(result, dest)
    evidence = skill_evidence(raw, box)
    evidence.update(prompt=prompt, exit_code=proc.returncode, sandbox=box.relative_to(ROOT).as_posix(),
                    parts_written=result.exists())
    save_json(OUT / case_id / f"skill_{tag}.json", evidence)
    _write_session_md(case_id, tag, evidence)
    return evidence


def _escapes(text, box):
    """工具參數裡跑出沙盒的路徑。反斜線先正規化：JSON 裡的 Windows 路徑是雙反斜線，直接比對字串會漏抓。"""
    t = text.replace("\\\\", "/").replace("\\", "/").lower()
    if box is not None:
        t = t.replace(Path(box).resolve().as_posix().lower(), "<sandbox>")
    hits = [("答案", f) for f in FORBIDDEN if f.replace("\\", "/").lower() in t]
    own = Path(box).parent.name if box is not None else None
    hits += [("答案", f"其他案例 {o}") for o in "ABCDE"
             if o != own and (f"generalization/{o.lower()}/" in t or f"gen_{o.lower()}." in t)]
    if "26_char_spine" in t:  # 多半是呼叫專案的 c2s.exe／python.exe，屬於使用工具；讀到答案時會同時命中上面的規則
        hits.append(("工具", "沙盒外的專案路徑"))
    if "../" in t:
        hits.append(("工具", "上層目錄 ../"))
    return hits


def skill_evidence(raw, box=None):
    """從 stream-json 判定：Skill 是否被觸發、是否執行 c2s、是否讀了不該讀的路徑。只讀 SKILL.md 不算觸發。
    headless 模式不記錄被展開的 slash 提示，slash 只能取得間接證據：指令可用，且第一個動作就是 Skill 第 1 步的 c2s。"""
    calls, final, triggered_by_slash, available = [], "", False, False
    for line in Path(raw).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        msg = ev.get("message") or {}
        content = msg.get("content") if isinstance(msg.get("content"), list) else []
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            available = "character-to-spine" in ev.get("slash_commands", [])
        if ev.get("type") == "user":
            text = json.dumps(msg.get("content"), ensure_ascii=False)
            triggered_by_slash |= "<command-name>/character-to-spine</command-name>" in text
        for c in content:
            if c.get("type") == "tool_use":
                calls.append({"tool": c["name"], "input": c.get("input", {})})
        if ev.get("type") == "result":
            final = ev.get("result", "")
    skill_calls = [c for c in calls if c["tool"] == "Skill" and "character-to-spine" in json.dumps(c["input"])]
    shell = [c for c in calls if c["tool"] in ("Bash", "PowerShell")]
    c2s_calls = [c["input"].get("command", "") for c in shell if "c2s" in c["input"].get("command", "")]
    escapes = [{"tool": c["tool"], "kind": k, "hit": h, "input": json.dumps(c["input"], ensure_ascii=False)[:200]}
               for c in calls for k, h in _escapes(json.dumps(c["input"], ensure_ascii=False), box)]
    forbidden = [e for e in escapes if e["kind"] == "答案"]
    read_skill_md = any("SKILL.md" in json.dumps(c["input"]) for c in calls)
    first_cmds = [c["input"].get("command", "") for c in calls if c["tool"] in ("Bash", "PowerShell")][:2]
    # slash 展開的提示不會出現在 stream-json；沒有 Skill 呼叫、沒讀 SKILL.md，卻一開始就照 Skill 用 c2s，內容只能來自 slash 注入
    slash_indirect = available and not skill_calls and not read_skill_md and any("c2s" in c for c in first_cmds)
    first_skill = next((i for i, c in enumerate(calls) if c in skill_calls), None)
    return {"skill_tool_called": bool(skill_calls), "slash_command_expanded": triggered_by_slash,
            "slash_available": available, "slash_indirect": slash_indirect,
            "c2s_after_skill": bool(c2s_calls) and (triggered_by_slash or slash_indirect or first_skill is not None),
            "c2s_commands": c2s_calls, "forbidden_reads": forbidden,
            "tool_escapes": [e for e in escapes if e["kind"] == "工具"], "read_skill_md": read_skill_md,
            "tool_counts": {t: sum(c["tool"] == t for c in calls) for t in sorted({c["tool"] for c in calls})},
            "calls": [{"tool": c["tool"], "input": json.dumps(c["input"], ensure_ascii=False)[:300]} for c in calls],
            "final_reply": final}


def _write_session_md(case_id, tag, ev):
    ok = lambda b: "是" if b else "否"
    lines = [f"# {case_id} Skill 實測（{'/character-to-spine' if tag == 'slash' else '自然語言'}）", "",
             "同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。", "",
             f"- 提示：`{ev['prompt']}`", f"- 結束碼：{ev['exit_code']}",
             f"- Skill 工具呼叫 `character-to-spine`：{ok(ev['skill_tool_called'])}",
             f"- slash command 展開（直接證據）：{ok(ev['slash_command_expanded'])}",
             f"- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：{ok(ev.get('slash_indirect'))}",
             f"- 讀過 SKILL.md 檔案：{ok(ev.get('read_skill_md'))}",
             f"- 觸發後執行 c2s：{ok(ev['c2s_after_skill'])}（{len(ev['c2s_commands'])} 次）",
             f"- 讀到答案（既有角色、其他案例、案例描述）：{len(ev['forbidden_reads'])} 次",
             f"- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：{len(ev.get('tool_escapes', []))} 次",
             f"- 工具呼叫次數：{ev['tool_counts']}", "",
             "## c2s 指令", ""] + [f"- `{c}`" for c in ev["c2s_commands"]] + [
             "", "## 讀到答案", ""] + ([f"- {f['tool']}：`{f['hit']}`：{f['input']}" for f in ev["forbidden_reads"]] or ["- 無"]) + [
             "", "## 使用沙盒外的工具", ""] + ([f"- {f['tool']}：{f['input']}" for f in ev.get("tool_escapes", [])] or ["- 無"]) + [
             "", "## 全部工具呼叫", ""] + [f"{i + 1}. {c['tool']}：`{c['input']}`" for i, c in enumerate(ev["calls"])] + [
             "", "## 最後回覆（原文）", "", ev["final_reply"]]
    (DOCS / case_id).mkdir(parents=True, exist_ok=True)
    (DOCS / case_id / f"skill_session_{tag}.md").write_text("\n".join(lines), encoding="utf-8")


# ---------- 來源查核 ----------

def _shape(poly):
    p = np.array(poly, float)
    c = p - p.mean(0)
    s = np.sqrt((c ** 2).sum(1).mean()) or 1.0
    return c / s, s


def provenance(img, parts_path):
    """新 parts.json 與既有 parts.json 的多邊形雷同比對（逐點相同，或平移縮放後殘差 < 3px），以及座標是否在前景附近。"""
    doc = load_json(parts_path)
    olds = [p for f in list((ROOT / "examples").glob("real/*.parts.json")) + list((ROOT / "examples").glob("synthetic/*.parts.json"))
            for p in load_json(f)["parts"] if p.get("polygon")]
    for f in SET.glob("*/*.parts.json"):
        if f.resolve() != Path(parts_path).resolve():
            olds += [p for p in load_json(f).get("parts", []) if p.get("polygon")]
    rgba, _ = load_rgba(img)
    ys, xs = np.nonzero(rgba[..., 3] > ALPHA_MIN)
    h, w = rgba.shape[:2]
    margin = 0.1 * max(w, h)
    problems = []
    for p in doc.get("parts", []):
        poly = p.get("polygon")
        if not poly or len(poly) < 3:
            continue
        a, sa = _shape(poly)
        for o in olds:
            if len(o["polygon"]) == len(poly):
                b, _ = _shape(o["polygon"])
                if np.abs(a - b).max() * sa < 3:
                    problems.append(f"{p['name']} 與既有部件 {o['name']} 的多邊形雷同")
        q = np.array(poly)
        if (q[:, 0] < xs.min() - margin).any() or (q[:, 0] > xs.max() + margin).any() or \
                (q[:, 1] < ys.min() - margin).any() or (q[:, 1] > ys.max() + margin).any():
            problems.append(f"{p['name']} 的座標超出前景範圍")
    return {"status": "FAIL" if problems else "PASS", "detail": problems or ["沒有雷同多邊形，座標都在前景附近"]}


# ---------- 執行與量測 ----------

def run_case(case_id):
    img, case = cases()[case_id]
    wd = OUT / case_id / "work"
    r = {"id": case_id, "origin": case["origin"] if case else "legacy", "type": case["type"] if case else "regression",
         "expected_scope": case["expected_scope"] if case else "supported"}
    if case:
        problems = check_case(case)
        if problems:
            return {**r, "status": "not_run", "problems": problems}
        parts = img.with_suffix(".parts.json")
        r["has_parts"] = parts.exists()
        doc = load_json(parts) if parts.exists() else {}
        r["unsupported"], r["absent"] = doc.get("unsupported"), doc.get("absent", [])
        r["provenance"] = provenance(img, parts) if parts.exists() else {"status": "NOT_TESTED", "detail": ["沒有 parts.json"]}
        skills = {t: load_json(OUT / case_id / f"skill_{t}.json") for t in ("nl", "slash") if (OUT / case_id / f"skill_{t}.json").exists()}
        r["skill"] = {t: {k: v for k, v in e.items() if k not in ("calls", "final_reply")} for t, e in skills.items()}
    shutil.rmtree(wd, ignore_errors=True)
    proc = subprocess.run([str(C2S), "run", str(img), "--workdir", str(wd)], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    r["exit_code"] = proc.returncode
    r["command"] = f"c2s run {img.relative_to(ROOT).as_posix()} --workdir {wd.relative_to(ROOT).as_posix()}"
    if proc.returncode not in (0, 1) or not (wd / "spine" / "character.json").exists():
        r["status"] = "stopped"
        r["message"] = (proc.stdout + proc.stderr)[-1500:]
        if (wd / "analysis.json").exists():
            r["analysis"] = {k: v for k, v in load_json(wd / "analysis.json").items() if k in ("parts", "parts_errors", "missing_required", "status")}
        return r
    r["status"] = "ran"
    r.update(measure(wd))
    sheet(wd, OUT / case_id / "visual_sheet.png", case_id)
    return r


def measure(wd):
    skel, meta = load_json(wd / "spine" / "character.json"), load_json(wd / "metadata.json")
    v = load_json(wd / "validation_report.json")
    q = load_json(wd / "quality" / "quality_report.json")
    travel = limb_travel(wd, skel)
    roles = load_json(wd / "rig.json")["roles"]
    attached = {e["name"] for e in meta["parts"] if e.get("attach")}
    # 自我修正把哪根骨頭降了多少、是被哪一類異常拖累（素材限制 = 補圖露出；其他 = 演算法限制）
    cause = {}
    for rnd in q["rounds"]:
        for a in rnd["anomalies"]:
            if a.get("attributed_to"):
                cause.setdefault(a["attributed_to"], set()).add(a["kind"])
    tuning = q["tuning"].get("happy", {})
    over = {b: {"factor": f, "limit": "素材限制" if cause.get(b, set()) <= {"exposure"} else "演算法限制",
                "caused_by": sorted(cause.get(b, set()))}
            for b, f in tuning.items() if roles.get(b) == "arm" and f < 0.25}
    loop = all(np.allclose(world_matrices(skel, n, 0)[b], world_matrices(skel, n, duration(a))[b], atol=1e-3)
               for n, a in skel["animations"].items() for b in world_matrices(skel))
    return {"validator": {c["check"]: c["status"] for c in v["checks"]},
            "validator_detail": {c["check"]: c["detail"] for c in v["checks"] if c["status"] != "PASS"},
            "recompose": {"setup_mae": meta.get("recompose_mae"), "unassigned_all": meta.get("unassigned_ratio"),
                          "unassigned_ratio": body_unassigned(wd),
                          "setup_pose": next(c["detail"] for c in v["checks"] if c["check"] == "setup_pose")},
            "quality": {"unresolved": [f"{a['kind']}:{a['subject']}" for a in q["unresolved"]], "tuning": q["tuning"],
                        "downgraded": q["downgraded_to_needs_manual"]},
            "motion": travel, "free_arms": {n: t.get("happy", 0) for n, t in travel.items() if roles.get(n) == "arm" and n not in attached},
            "bounce_only": all(t.get("happy", 0) < criteria()["bounce_only_max"] for t in travel.values()),
            "over_reduced": over, "loop_ok": bool(loop),
            "exposure": fill_exposure(wd, skel),
            "manual": [e["name"] for e in meta["parts"] if e["status"] == "needs_manual"],
            "parts": [e["name"] for e in meta["parts"]]}


def body_unassigned(wd):
    """與角色本體相連、卻不屬於任何部件的前景比例。散落的特效（不和任何部件相連）依 Skill 規定刻意不歸屬，不算漏切。"""
    fg = np.array(Image.open(wd / "source_rgba.png"))[..., 3] > ALPHA_MIN
    assigned = np.zeros_like(fg)
    for p in load_json(wd / "parts.json")["parts"]:
        assigned |= part_mask(p, fg.shape)
    lab = cv2.connectedComponents(fg.astype(np.uint8), connectivity=8)[1]
    body = np.isin(lab, np.unique(lab[fg & assigned]))
    return round(float((body & ~assigned).sum() / max(1, body.sum())), 4)


def criteria():
    return manifest()["criteria"]


# ---------- 判定 ----------

def _visual(case_id):
    path = SET / "visual_review.json"
    return load_json(path).get(case_id) if path.exists() else None


def _algo_failures(r, c):
    out = []
    if r["recompose"]["unassigned_ratio"] is not None and r["recompose"]["unassigned_ratio"] > c["unassigned_max"]:
        out.append(f"未分配前景 {r['recompose']['unassigned_ratio']:.1%} > {c['unassigned_max']:.0%}")
    if not r["loop_ok"]:
        out.append("動畫首尾不一致，不能循環")
    if r["bounce_only"]:
        out.append("所有肢體相對身體幾乎不動，只剩整體跳動")
    out += [f"未持物手臂 {n} 動作量 {t:.1%} < {c['free_arm_min']:.0%}" for n, t in r["free_arms"].items() if t < c["free_arm_min"]]
    out += [f"品質未解：{u}" for u in r["quality"]["unresolved"]]
    out += [f"{b} 被自我修正縮到 ×{o['factor']}（{o['limit']}：{o['caused_by']}）" for b, o in r["over_reduced"].items() if o["limit"] == "演算法限制"]
    return out


def _bad_validator(r):
    return [f"驗證器 {k} FAIL" for k, s in r["validator"].items() if s == "FAIL" and k not in SPINE_CHECKS]


def _vis(r, level):
    v = r.get("visual") or {}
    return [f"目視 {k}：{v[k][1]}" for k in ("layers", "joints", "motion", "occlusion") if k in v and v[k][0] == level]


# 由上往下，第一條回傳非空理由的規則決定等級。合成角色與既有角色也走同一張表。
GRADE_RULES = [
    ("NOT_TESTED", lambda r, c: r.get("problems") or []),
    ("UNSUPPORTED", lambda r, c: [f"宣告超出範圍：{r['unsupported']}"] if r.get("unsupported") and r["expected_scope"] == "unsupported" else []),
    ("FAIL", lambda r, c: [f"預期 {r['expected_scope']} 卻宣告超出範圍：{r['unsupported']}"] if r.get("unsupported") else []),
    ("FAIL", lambda r, c: ["沒有產生 parts.json（分析失敗）"] if r.get("has_parts") is False else []),
    ("FAIL", lambda r, c: [f"來源查核：{d}" for d in r["provenance"]["detail"]] if r.get("provenance", {}).get("status") == "FAIL" else []),
    ("FAIL", lambda r, c: [f"流程停止（結束碼 {r['exit_code']}）：{r.get('message', '')[-300:]}"] if r.get("status") == "stopped" else []),
    ("FAIL", lambda r, c: _bad_validator(r) + _algo_failures(r, c) + _vis(r, "BAD")),
    ("NOT_TESTED", lambda r, c: ["沒有目視紀錄"] if not r.get("visual") else []),
    ("PARTIAL", lambda r, c: [f"需人工修補：{', '.join(r['manual'])}"] * bool(r["manual"])
     + [f"宣告看不到：{', '.join(r['absent'])}"] * bool(r.get("absent"))
     + [f"{b} 被自我修正縮到 ×{o['factor']}（素材限制：{o['caused_by']}）" for b, o in r["over_reduced"].items()]
     + _vis(r, "MINOR") + _vis(r, "UNKNOWN")),
    ("PASS", lambda r, c: ["所有登記門檻與目視項目通過"]),
]


def grade(r, c):
    for level, rule in GRADE_RULES:
        reasons = rule(r, c)
        if reasons:
            return level, reasons


# ---------- 視覺驗收圖 ----------

def _font(size):
    return ImageFont.truetype(FONT, size)


def _fit(img, h):
    return img.resize((max(1, round(img.width * h / img.height)), h))


def sheet(wd, out_path, title):
    """原圖｜重組｜骨架圖｜Idle 3 格｜Happy 4 格（Python Simulation Preview，不是 Spine 算圖）。"""
    meta, rig = load_json(wd / "metadata.json"), load_json(wd / "rig.json")
    skel = load_json(wd / "spine" / "character.json")
    src = Image.open(wd / "source_rgba.png").convert("RGBA")
    white = lambda im: Image.alpha_composite(Image.new("RGBA", im.size, "white"), im).convert("RGB")
    recomposed = Image.fromarray(render(skel, wd / "spine" / "images", meta["canvas"], meta["origin"])[0].clip(0, 255).astype(np.uint8))
    faded = Image.blend(white(src), Image.new("RGB", src.size, "white"), 0.6)
    d = ImageDraw.Draw(faded)
    ox, oy = meta["origin"]
    pos = {b["name"]: (b["world"][0] + ox, oy - b["world"][1]) for b in rig["bones"] if "world" in b}
    pos["root"] = (ox, oy)
    r = max(4, src.height // 120)
    for b in rig["bones"]:
        if b["name"] in pos and b.get("parent") in pos:
            d.line([pos[b["parent"]], pos[b["name"]]], fill=(120, 120, 120), width=max(1, r // 2))
    for b in rig["bones"]:
        if "world" in b and b.get("length"):
            x, y = pos[b["name"]]
            ang = np.radians(b["world"][2])
            d.line([(x, y), (x + np.cos(ang) * b["length"] / 2, y - np.sin(ang) * b["length"] / 2)], fill=(220, 0, 90), width=max(2, r // 2))
    for n, (x, y) in pos.items():
        d.ellipse([x - r, y - r, x + r, y + r], fill=(0, 120, 255))
        d.text((x + r + 2, y - r), n, fill=(0, 60, 160), font=_font(max(12, r * 3)))
    canvas, origin, scale = framing(meta)
    frames = []
    for name, times in (("idle", (0, 1 / 3, 2 / 3)), ("happy", (0, 0.2, 0.5, 0.9))):
        if name in skel["animations"]:
            dur = duration(skel["animations"][name])
            for f in times:
                t = round(f * dur if name == "idle" else f, 2)
                img = Image.fromarray(render(skel, wd / "spine" / "images", canvas, origin, name, t, scale)[0].clip(0, 255).astype(np.uint8))
                frames.append((f"{name} t={t}s", img))
    H = 420
    tiles = [("原圖", white(src)), ("圖層重組（骨架初始姿勢算圖）", recomposed), ("骨架：藍點=pivot、紅=骨頭方向、灰=父子", faded)] + frames
    tiles = [(label, _fit(im, H)) for label, im in tiles]
    row1, row2 = tiles[:3], tiles[3:]
    width = max(sum(im.width for _, im in row1), sum(im.width for _, im in row2)) + 10 * 8
    out = Image.new("RGB", (width, 40 + (H + 34) * 2), "white")
    dd = ImageDraw.Draw(out)
    dd.text((8, 6), f"{title}｜Python Simulation Preview，不是 Spine 算圖", fill=(0, 0, 0), font=_font(22))
    for row, y in ((row1, 40), (row2, 40 + H + 34)):
        x = 6
        for label, im in row:
            out.paste(im, (x, y + 28))
            dd.text((x, y + 4), label, fill=(60, 60, 60), font=_font(18))
            x += im.width + 10
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)


# ---------- 報告 ----------

COUNTED = {"PASS": "支援並完成", "PARTIAL": "部分完成，需人工修補", "UNSUPPORTED": "超出目前支援範圍",
           "FAIL": "技術失敗", "BLOCKED": "缺少測試素材", "NOT_TESTED": "尚未測試"}


def results_path(label=None):
    return OUT / "_snapshots" / label / "results.json" if label else OUT / "results.json"


def report(compare=None):
    res = load_json(results_path())
    for r in res.values():
        r["visual"] = _visual(r["id"])
        r["grade"], r["reasons"] = grade(r, criteria())
    save_json(results_path(), res)
    real = [r for r in res.values() if r["origin"] in ("user", "public")]
    n = len(real)
    count = {g: sum(r["grade"] == g for r in real) for g in COUNTED}
    lines = ["# 泛化測試矩陣", "", "由 `python scripts/generalization.py report` 依 `output/generalization/results.json` 產生，請勿手改。", "",
             "## 成功率（只計真實陌生角色）", "",
             f"- 成功率（PASS）：{count['PASS']}/{n}", f"- 可處理率（PASS＋PARTIAL）：{count['PASS'] + count['PARTIAL']}/{n}",
             "- " + "、".join(f"{COUNTED[g]} {count[g]}" for g in COUNTED), "- UNSUPPORTED 不計入成功；合成角色不計入任何比率。", "",
             "## 案例", "",
             "| 案例 | 類型 | 來源 | 預期 | 等級 | Skill 觸發 | 來源查核 | 重組 MAE | 未分配 | 未持物手臂動作量 | 只剩跳動 | 循環 | 需人工 | 主要理由 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res.values():
        sk = r.get("skill", {}).get("nl", {})
        trig = "—" if r["origin"] == "legacy" else ("是" if sk.get("skill_tool_called") and sk.get("c2s_after_skill") else "否" if sk else "未測")
        rc = r.get("recompose", {})
        arms = "、".join(f"{k} {v:.1%}" for k, v in r.get("free_arms", {}).items()) or "—"
        un = "—" if rc.get("unassigned_ratio") is None else f"{rc['unassigned_ratio']:.2%}"
        lines.append(f"| {r['id']} | {r['type']} | {r['origin']} | {r['expected_scope']} | **{r['grade']}** | {trig} | "
                     f"{r.get('provenance', {}).get('status', '—')} | {rc.get('setup_mae', '—')} | "
                     f"{un} | {arms} | "
                     f"{'是' if r.get('bounce_only') else '否' if 'bounce_only' in r else '—'} | "
                     f"{'是' if r.get('loop_ok') else '否' if 'loop_ok' in r else '—'} | {', '.join(r.get('manual', [])) or '—'} | "
                     f"{'；'.join(r['reasons'])[:220]} |")
    lines += ["", "## 驗證器原始狀態（PASS／FAIL／BLOCKED／NOT_TESTED）", "",
              "| 案例 | " + " | ".join(next((list(r["validator"]) for r in res.values() if r.get("validator")), [])) + " |",
              "|---|" + "---|" * len(next((r["validator"] for r in res.values() if r.get("validator")), {}))]
    for r in res.values():
        if r.get("validator"):
            lines.append(f"| {r['id']} | " + " | ".join(r["validator"].values()) + " |")
    lines += ["", "## 自動量測與目視判斷（分開記錄）", "",
              "| 案例 | 目視者 | 分層 | 關節 | 動作 | 遮擋補圖 | 補圖最大露出 | 各肢體 happy 動作量 |", "|---|---|---|---|---|---|---|---|"]
    for r in res.values():
        v = r.get("visual") or {}
        cell = lambda k: f"{v[k][0]}：{v[k][1]}" if k in v else "NOT_TESTED"
        exp = "、".join(f"{k} {x:.1%}" for k, x in r.get("exposure", {}).items()) or "—"
        mot = "、".join(f"{k} {x.get('happy', 0):.1%}" for k, x in r.get("motion", {}).items()) or "—"
        lines.append(f"| {r['id']} | {v.get('reviewer', '—')} | {cell('layers')} | {cell('joints')} | {cell('motion')} | {cell('occlusion')} | {exp} | {mot} |")
    if compare:
        lines += ["", *compare_lines(*compare)]
    (ROOT / "docs" / "GENERALIZATION_TEST_MATRIX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return count, n


def compare_lines(a, b):
    ra, rb = load_json(results_path(a)), load_json(results_path(b))
    out = [f"## 前後比較：{a} → {b}", "", "| 案例 | 等級 | 重組 MAE | 未分配 | 未持物手臂動作量 | 需人工 | 品質未解 |", "|---|---|---|---|---|---|---|"]
    for k in rb:
        x, y = ra.get(k, {}), rb[k]
        f = lambda r, key, sub: (r.get(key) or {}).get(sub, "—")
        arms = lambda r: "、".join(f"{n} {v:.1%}" for n, v in r.get("free_arms", {}).items()) or "—"
        out.append(f"| {k} | {x.get('grade', '—')} → {y.get('grade', '—')} | {f(x, 'recompose', 'setup_mae')} → {f(y, 'recompose', 'setup_mae')} | "
                   f"{f(x, 'recompose', 'unassigned_ratio')} → {f(y, 'recompose', 'unassigned_ratio')} | {arms(x)} → {arms(y)} | "
                   f"{len(x.get('manual', []))} → {len(y.get('manual', []))} | {len(f(x, 'quality', 'unresolved') or [])} → {len(f(y, 'quality', 'unresolved') or [])} |")
    return out


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("skill")
    s.add_argument("id")
    s.add_argument("--slash", action="store_true")
    s = sub.add_parser("run")
    s.add_argument("ids", nargs="*")
    s = sub.add_parser("snapshot")
    s.add_argument("label")
    s = sub.add_parser("report")
    s.add_argument("--compare", nargs=2)
    a = p.parse_args()
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    if a.cmd == "skill":
        print(json.dumps({k: v for k, v in skill(a.id, a.slash).items() if k != "calls"}, ensure_ascii=False, indent=2))
    elif a.cmd == "run":
        path = results_path()
        res = load_json(path) if path.exists() else {}
        for cid in a.ids or list(cases()):
            print(f"== {cid}", flush=True)
            res[cid] = run_case(cid)
            save_json(path, res)
        report()
    elif a.cmd == "snapshot":
        dst = OUT / "_snapshots" / a.label
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copy(results_path(), dst / "results.json")
        for f in OUT.glob("*/visual_sheet.png"):
            shutil.copy(f, dst / f"{f.parent.name}_visual_sheet.png")
    else:
        count, n = report(a.compare)
        print(json.dumps({"real_cases": n, **count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
