"""彙整 Ref_pic 驗收 session 的輸出：每個案例的驗證狀態、需人工部件、未分配比例、自我修正縮小的動作幅度。

python scripts/refpic_summary.py <前綴>    例：v10_ → output/acceptance/v10_*/ 與沙盒 %TEMP%/c2s_acceptance/v10_*/
python scripts/refpic_summary.py --rerun <來源前綴> <標籤>
    沿用來源 session 寫好的 parts.json，用目前的 Python Core 重跑（parts.json 不變，差異只來自程式），
    結果在 output/refpic/<標籤>/<案例>/。
輸出 output/refpic/<前綴或標籤>summary.json，並印出表格。
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOXES = Path(tempfile.gettempdir()) / "c2s_acceptance"


def _load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def case(box):
    wd = next((d for d in (box / "output").iterdir() if d.is_dir()), None) if (box / "output").exists() else None
    res = _load(ROOT / "output" / "acceptance" / box.name / "result.json") or {}
    row = {"case": box.name, "skill": res.get("skill_tool_called"), "escapes": len(res.get("tool_escapes") or []),
           "forbidden": len(res.get("forbidden_reads") or [])}
    if wd is None:
        return row | {"status": "NO_OUTPUT"}
    val = _load(wd / "validation_report.json") or {}
    row["status"] = val.get("status") or "NO_REPORT"
    row["checks"] = {c["check"]: c["status"] for c in val.get("checks", [])}
    meta = _load(wd / "metadata.json")
    if meta:
        row["parts"] = len([e for e in meta["parts"] if "file" in e])
        row["needs_manual"] = [e["name"] for e in meta["parts"] if e["status"] == "needs_manual"]
        row["unassigned"] = meta["unassigned_ratio"]
        row["fx"] = [e["name"] for e in meta["parts"] if e.get("role") == "effect"]
    q = _load(wd / "quality" / "quality_report.json")
    if q:
        tun = q["tuning"].get("happy", {}) | {f"idle:{k}": v for k, v in q["tuning"].get("idle", {}).items()}
        row["tuning"] = tun
        row["min_factor"] = min(tun.values(), default=1.0)
        row["unresolved"] = [f"{a['kind']}:{a['subject']}" for a in q["unresolved"]]
        row["exposure_driven"] = sorted({a["subject"] for r in q["rounds"] for a in r["anomalies"] if a["kind"] == "exposure"})
    return row


def _rerun(args):
    src_box, dest = args
    import shutil
    from character_to_spine import pipeline
    parts = next(src_box.glob("*.parts.json"))
    img = next(p for p in src_box.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if '"unsupported"' in parts.read_text(encoding="utf-8"):
        return
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    shutil.copy(img, dest / img.name)
    shutil.copy(parts, dest / parts.name)
    try:
        pipeline.run(dest / img.name, "happy", workdir=dest / "output" / img.stem)
    except Exception as e:  # 單一案例失敗不影響其他案例；錯誤留在 rerun_error.txt
        (dest / "rerun_error.txt").write_text(repr(e), encoding="utf-8")


def rerun(src_prefix, tag):
    from multiprocessing import Pool
    sys.path.insert(0, str(ROOT / "src"))
    jobs = [(b, ROOT / "output" / "refpic" / tag / b.name.removeprefix(src_prefix))
            for b in sorted(BOXES.glob(src_prefix + "*")) if b.is_dir()]
    with Pool(len(jobs)) as pool:
        pool.map(_rerun, jobs)
    return main(tag, ROOT / "output" / "refpic" / tag)


def main(prefix, root=None):
    rows = [case(b) for b in sorted((root or BOXES).glob("*" if root else prefix + "*")) if b.is_dir()]
    out = ROOT / "output" / "refpic"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{prefix}summary.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in rows:
        print(f"{r['case']:<24} {r['status']:<12} parts={r.get('parts', '-')!s:<3} min_factor={r.get('min_factor', '-')!s:<7} "
              f"unassigned={r.get('unassigned', '-')!s:<7} manual={r.get('needs_manual', '-')} unresolved={r.get('unresolved', '-')} "
              f"escapes={r['escapes']} forbidden={r['forbidden']}")
        if r.get("tuning"):
            print(f"{'':<24} tuning={r['tuning']} exposure={r.get('exposure_driven')}")
    return rows


if __name__ == "__main__":
    if sys.argv[1:2] == ["--rerun"]:
        rerun(sys.argv[2], sys.argv[3])
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else "v10_")
