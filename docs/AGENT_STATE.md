# Agent 狀態（Checkpoint）

新的 session 先讀這份，再看 `git log`、`openspec/changes/character-to-spine-mvp/tasks.md`、`docs/TEST_RESULTS.md`，從最近的未完成任務繼續。不要重新規劃整個專案。

## 最後更新：2026-11-23

**分支**：`feat/character-to-spine-mvp`

**環境**：
- 一律使用專案虛擬環境：`.venv\Scripts\python.exe -m pytest -q`、`.venv\Scripts\c2s.exe`（使用者要求：安裝與測試前先建立並使用虛擬環境）。
- `.venv` 用 `uv venv` 建立，再以 `ensurepip` 補上 pip，`pip install -e ".[dev]"` 安裝。

**已完成**：tasks 第 1～9 組（第 7.7 組 BLOCKED）。
- Python Core、CLI、Skill 全部可執行，68 個測試通過。
- 合成角色 A／B 跑完整流程，所有不依賴 Spine 的驗證項目都是 PASS。

**下一步**：tasks 第 10 組，真實角色。
1. `c2s analyze examples\real\人.png`，看 `grid_overlay.png` 寫 `parts.json`。
2. 反覆修正到 `layer_preview.png` 合理。
3. 再做 `转场2.png`。

**阻礙**：完整版 Spine（K-01）。

**版控**：`.claude/`、`.codex/` 被使用者排除；修改 Skill 時改 `skills/character-to-spine/SKILL.md`，再複製到 `.claude/skills/character-to-spine/` 與 `.codex/skills/character-to-spine/`。

**pstack**：`/pstack:tdd`、`/pstack:poteto-mode`、`/pstack:architect`、`/pstack:interrogate` 都設定為只能由使用者親自輸入，Agent 無法呼叫，也不應模仿其流程。工程審查改由獨立子代理進行（只給程式碼與設計文件，不給 Agent 的結論）。
