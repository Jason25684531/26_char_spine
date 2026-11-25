## ADDED Requirements

### Requirement: c2s 指令
系統 SHALL 提供可獨立執行的 CLI `c2s`，包含子指令 `analyze`、`prepare`、`rig`、`animate`、`export`、`validate`、`preview` 與 `run`，每個子指令 MUST 以 JSON 輸出結果。

#### Scenario: 分步執行
- **WHEN** 依序執行 `c2s analyze character.png`、`c2s prepare`、`c2s rig --preset humanoid-chibi`、`c2s animate --motion happy`、`c2s export --format spine`、`c2s validate`
- **THEN** 每一步都以結束碼 0 完成，後面的指令不需要再指定圖片或工作目錄

#### Scenario: 一次跑完
- **WHEN** 對已有 `parts.json` 的圖片執行 `c2s run character.png --motion happy`
- **THEN** 工作目錄內產生分層 PNG、`metadata.json`、`spine/character.json`、`validation_report.json` 與預覽 GIF

#### Scenario: 指定工作目錄
- **WHEN** 任一指令帶 `--workdir <path>`
- **THEN** 所有處理結果都寫在該目錄；唯一的例外是 `./output/.current` 記錄最後使用的工作目錄（絕對路徑），讓之後不帶參數的指令接續同一個目錄

### Requirement: 結束碼與接續流程
CLI SHALL 以結束碼 0 表示完成、1 表示失敗、2 表示需要補資料後接續。結束碼為 2 時輸出 MUST 說明缺少什麼與下一步指令。

#### Scenario: 圖片尚未分層
- **WHEN** 對沒有 `parts.json` 的圖片執行 `c2s run`
- **THEN** 結束碼為 2，輸出列出缺少的必要部件與接續步驟，不產生 `rig.json` 與 `spine/`

#### Scenario: 步驟順序錯誤
- **WHEN** 在還沒執行 prepare 的工作目錄執行 `c2s rig`
- **THEN** 結束碼為 2，訊息說明要先執行哪個指令

### Requirement: 失敗留下診斷資訊
任何失敗 CLI MUST 在工作目錄寫入 `c2s_error.log`，內容包含執行的指令與完整的錯誤追蹤（例外）或失敗的檢查項目（驗證 FAIL）。指令成功時 MUST 移除過期的 `c2s_error.log`。

#### Scenario: 未預期的例外
- **WHEN** 某個步驟拋出未預期的例外
- **THEN** 結束碼為 1，stderr 輸出錯誤訊息與 log 路徑，`c2s_error.log` 含有 traceback

### Requirement: Claude 與 Codex 共用同一個 Skill 與核心
系統 SHALL 提供 Skill `character-to-spine`，供 Claude Code 與 Codex 使用。Skill MUST 只透過 `c2s` 指令操作，MUST NOT 另外實作處理邏輯；兩邊的 Skill 內容 MUST 相同。

#### Scenario: Skill 內容一致
- **WHEN** 比對 `skills/character-to-spine/SKILL.md`、`.claude/skills/character-to-spine/SKILL.md` 與 `.codex/skills/character-to-spine/SKILL.md`
- **THEN** 三份內容完全相同

#### Scenario: Skill 說明完整流程
- **WHEN** Agent 依 Skill 處理一張新的角色圖
- **THEN** Skill 的步驟涵蓋：檢視圖片、撰寫 `parts.json`（含格式說明）、執行 `c2s run`、檢視 `layer_preview.png`、依修補任務接續、回報各項狀態
