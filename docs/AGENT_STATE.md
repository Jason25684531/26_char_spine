# Agent 狀態（Checkpoint）

新的 session 先讀這份，再看 `git log`、`openspec/changes/character-to-spine-mvp/tasks.md`、`docs/TEST_RESULTS.md`，從最近的未完成任務繼續。不要重新規劃整個專案。

## 最後更新：2026-11-23

**分支**：`feat/character-to-spine-mvp`（尚未合併到 `main`）

**環境**：
- 一律使用專案虛擬環境：`.venv\Scripts\python.exe -m pytest -q`、`.venv\Scripts\c2s.exe`（使用者要求：安裝與測試前先建立並使用虛擬環境）。
- `.venv` 用 `uv venv` 建立，`ensurepip` 補上 pip，`pip install -e ".[dev]"` 安裝。

**進度**：tasks 55/56；只剩 7.7（BLOCKED）。83 個測試通過。
- 兩組真實角色：`output\ren`（人.png）、`output\zc2`（转场2.png）。
- 交付目錄：`Character-to-Spine-Deliverables/`，由 `scripts/package_deliverables.py --chars output\ren output\zc2` 產生，不進版控。

**唯一阻礙**：完整版 Spine（K-01）。到位後：
1. 設定 `SPINE_EXE` 指向 `Spine.com`，對兩個工作目錄執行 `c2s export --spine-version <實際 Editor 版本>`。
2. 若往返驗證 FAIL，先看 K-10（`-e json` 寫法）。
3. 人工在 Editor 開啟、修改關鍵影格，結果記入 `TEST_RESULTS.md`。
4. 重跑打包腳本，勾選 7.7，再 `openspec archive`。

**待使用者決定**：是否親自執行 `/pstack:interrogate`（Agent 無法呼叫）；是否補畫 `repair_tasks.md` 列出的部件。

**版控**：`.claude/`、`.codex/` 被使用者排除；修改 Skill 時改 `skills/character-to-spine/SKILL.md`，再複製到兩處。

**pstack**：`tdd`、`poteto-mode`、`architect`、`interrogate` 都只能由使用者親自輸入；工程審查改由獨立子代理進行。