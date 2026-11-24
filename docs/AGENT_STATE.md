# Agent 狀態（Checkpoint）

新的 session 先讀這份，再看 `git log`、`docs/SKILL_V1_REPORT.md`、`docs/KNOWN_ISSUES.md`。不要重新規劃整個專案。

## 最後更新：2026-11-24（Skill v1.0）

**交付物**：`dist/character-to-spine-skill-v1.0.0.zip`（`scripts/build_skill.py`）與 `Character-to-Spine-Deliverables/`（`scripts/package_deliverables.py --chars output/generalization/{ren,zc2,rq,yz}/work`），兩者都不進版控、可重建。實測報告 `docs/SKILL_V1_REPORT.md`。

- Skill 正本 `skills/character-to-spine/`：`SKILL.md`、`references/parts-format.md`、啟動器 `scripts/c2s.py`。改完要重跑 `build_skill.py`，再把 `dist/character-to-spine/` 複製到 `.claude/skills/`、`.codex/skills/`（`test_skill_copies_identical`）。
- 新使用者驗收：`python scripts/acceptance.py <圖片> [--slash]`（真正的 `claude -p`，照 README 解壓 zip）。
- 泛化：`scripts/generalization.py`，快照 `v1_before`（HEAD 基準）、`v1_final`（N1–N4 第一次執行）、`v1_final2`（影子修正後）。N1–N4 已用過，下一輪要新的保留集。
- 測試：153 passed。
- 唯一外部阻礙仍是完整版 Spine（K-01）。其餘未解見 KNOWN_ISSUES K-31～K-38。
- **不要在 Skill session 執行期間重建 `dist/`**：沙盒會複製到半成品（yz 第一次失敗的原因）。

## 前一階段：2026-11-24（泛化測試）

**OpenSpec change `character-generalization`**：泛化測試集、Skill 實測、`unsupported`／`absent`、`role: ground`。結果與待辦見 `docs/GENERALIZATION_TEST_REPORT.md`；下一步依該報告第 10 節，先修 K-24（破洞誤判）與 K-28（持物骨架顛倒），再用**新的**保留集驗證（H1–H4 已用過）。

- 泛化執行器：`scripts/generalization.py`（skill／run／snapshot／report）；manifest、目視紀錄在 `examples/generalization/`；證據匯出 `scripts/export_generalization_docs.py`。
- 測試：148 passed。
- 審查時發現先前報告沒提到的實況：preset 只有一個、pivot 預設是外框比例、motion_metrics 只量 attach 接觸點、`examples/real/` 四張圖是同一個角色。

## 前一階段：2026-11-23

**分支**：`feat/character-to-spine-mvp`（尚未合併到 `main`）

**環境**：
- 一律使用專案虛擬環境：`.venv\Scripts\python.exe -m pytest -q`、`.venv\Scripts\c2s.exe`（使用者要求：安裝與測試前先建立並使用虛擬環境）。
- `.venv` 用 `uv venv` 建立，`ensurepip` 補上 pip，`pip install -e ".[dev]"` 安裝。

**OpenSpec change**：
- `character-to-spine-mvp`：55/56，只剩 7.7（BLOCKED，需完整版 Spine）。
- `quality-hardening`：資料管理、補圖風險、動畫品質、接觸約束、自我修正。見其 `tasks.md`。
- `animation-liveliness`：樂器帶動手與撥弦節奏、需人工草稿納入自我修正、修補優先順序報告、Spine 匯入說明。爬坡實驗的每一步記在 `.audit/final-animation-quality.tsv`（不進版控）。

**素材與產物**：
- 永久素材在 `examples/real/`：圖片、`<圖名>.parts.json`，以及有人工修補時的 `<圖名>.overrides/`。
- `output/` 全部可刪，`c2s run examples\real\人.png --workdir output\ren` 會重建出相同結果。
- 交付目錄由 `scripts/package_deliverables.py --chars output\ren output\zc2` 產生，不進版控。

**測試**：114 passed（約 4 分鐘）。

**待使用者決定**：DECISIONS D-36。目前預設：需人工部件的草稿在補畫前不露出，代價是转场2 捧花的手動作變小。要改回優先活潑度，回退 `quality._context` 的 `exposure_parts` 中 `needs_manual` 那個條件。

**未達成**：撥弦手最大位移 ≥13px（目前 5.1px）。限制依序是吉他草稿，其次是 9px 的接觸容許值（KNOWN_ISSUES K-18）。補好吉他後重跑即可提升；全部補好後再試 H1。

**品質流程**：`c2s run` 依序執行 analyze → prepare → rig → animate → refine → validate → preview。
- refine 負責逐格品質檢查、自我修正，結束時 export。
- 門檻與校準依據見 `DECISIONS.md` D-31、D-32。

**唯一外部阻礙**：完整版 Spine（K-01）。到位後：
1. 設定 `SPINE_EXE` 指向 `Spine.com`，執行 `c2s run <圖片> --workdir <目錄> --spine-version <實際 Editor 版本>`。refine 結束時會 export 並匯入。
2. 若往返驗證 FAIL，先看 K-10（`-e json` 寫法）。
3. 人工在 Editor 開啟、修改關鍵影格，結果記入 `TEST_RESULTS.md`。
4. 重跑打包腳本，勾選 7.7，再 `openspec archive`。

**待使用者決定**：
- 是否親自執行 `/pstack:interrogate`、`/pstack:show-me-your-work`（Agent 無法呼叫）。
- 是否補畫 `repair_tasks.md` 列出的部件。

**版控**：`.claude/`、`.codex/` 被使用者排除；修改 Skill 時改 `skills/character-to-spine/SKILL.md`，再複製到兩處。

**pstack**：`tdd`、`poteto-mode`、`architect`、`interrogate`、`show-me-your-work` 都只能由使用者親自輸入；工程審查改由獨立子代理進行。
