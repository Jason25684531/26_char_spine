# Agent 狀態（Checkpoint）

新的 session 先讀這份，再看 `git log`、兩個 OpenSpec change 的 `tasks.md`、`docs/TEST_RESULTS.md`，從最近的未完成任務繼續。不要重新規劃整個專案。

## 最後更新：2026-11-23

**分支**：`feat/character-to-spine-mvp`（尚未合併到 `main`）

**環境**：
- 一律使用專案虛擬環境：`.venv\Scripts\python.exe -m pytest -q`、`.venv\Scripts\c2s.exe`（使用者要求：安裝與測試前先建立並使用虛擬環境）。
- `.venv` 用 `uv venv` 建立，`ensurepip` 補上 pip，`pip install -e ".[dev]"` 安裝。

**OpenSpec change**：
- `character-to-spine-mvp`：55/56，只剩 7.7（BLOCKED，需完整版 Spine）。
- `quality-hardening`：資料管理、補圖風險、動畫品質、接觸約束、自我修正。見其 `tasks.md`。

**素材與產物**：
- 永久素材在 `examples/real/`：圖片、`<圖名>.parts.json`，以及有人工修補時的 `<圖名>.overrides/`。
- `output/` 全部可刪，`c2s run examples\real\人.png --workdir output\ren` 會重建出相同結果。
- 交付目錄由 `scripts/package_deliverables.py --chars output\ren output\zc2` 產生，不進版控。

**測試**：101 passed（約 2.5 分鐘）。

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
