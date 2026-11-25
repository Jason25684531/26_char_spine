## ADDED Requirements

### Requirement: Spine 匯入準備
交付目錄的每個角色 Spine 專案資料夾 SHALL 附一份匯入說明，內容包含：

- `skeleton.spine` 版本字串。
- 本機偵測到的 Spine 版本。
- 每個檔案的 SHA-256。
- 圖形介面與 CLI 的匯入步驟。
- 匯入後的驗收清單。

沒有完整版 Spine 時，說明 MUST 標明 `.spine` 驗收為 BLOCKED。

#### Scenario: 產生匯入說明
- **WHEN** 執行打包腳本
- **THEN** `03_Spine_Project/<角色>/IMPORT.md` 存在，列出的雜湊與實際檔案一致，並標明 BLOCKED