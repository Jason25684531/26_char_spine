## ADDED Requirements

### Requirement: 輸出 Spine JSON 與圖片
系統 SHALL 輸出 `spine/character.json` 與 `spine/images/`，JSON MUST 含有 `skeleton`、`bones`、`slots`、`skins`、`animations`，且每個附件 MUST 對應到 `images/` 內存在的同名 PNG。

#### Scenario: 結構完整
- **WHEN** 對完成骨架與動畫的角色執行 export
- **THEN** JSON 的骨頭以 root 開頭且父骨頭排在子骨頭之前，每個插槽對應到存在的骨頭與 default skin 內的附件，每個附件的寬高等於對應 PNG 的實際尺寸

#### Scenario: 指定版本
- **WHEN** 執行 `c2s export --spine-version 4.2.43`
- **THEN** `skeleton.spine` 為 `4.2.43`；未指定時為 4.3 系列

#### Scenario: 與官方匯出檔的鍵名一致
- **WHEN** 比對輸出的 JSON 與官方 4.3 spineboy 匯出檔
- **THEN** 輸出中使用的每個骨頭、插槽、region 附件、timeline、關鍵影格的鍵名都出現在官方檔案中

### Requirement: 以完整版 Spine CLI 建立可編輯專案
找到完整版 Spine CLI 時，系統 SHALL 以 CLI 將 JSON 匯入為 `spine/character.spine`，確認檔案存在且非空，再匯出回 JSON 比對骨頭、插槽與動畫名稱。

#### Scenario: 匯入成功
- **WHEN** 完整版 Spine CLI 可用且匯入指令以結束碼 0 完成
- **THEN** `spine/character.spine` 存在且大小大於 0，`export_report.json` 的 `spine_import.status` 為 PASS，並記錄實際執行的指令與 log 路徑

#### Scenario: 匯入失敗
- **WHEN** Spine CLI 回傳非 0 結束碼、逾時，或沒有產生檔案
- **THEN** 狀態為 FAIL，`spine_import.log` 保留完整輸出

#### Scenario: 往返驗證
- **WHEN** 匯入成功後把 `.spine` 匯出回 JSON
- **THEN** 骨頭、插槽、動畫名稱與原始 JSON 相同時 `roundtrip.status` 為 PASS，否則為 FAIL 並列出不一致的項目

### Requirement: 沒有完整版 Spine 時標記 BLOCKED
找不到 Spine CLI 或只找到試用版時，系統 MUST 將匯入狀態標為 BLOCKED 並說明原因與解除方式，且 MUST NOT 產生任何 `.spine` 檔案或以模擬結果代替。

#### Scenario: 沒有安裝 Spine
- **WHEN** 找不到任何 Spine 執行檔
- **THEN** `spine_import.status` 為 BLOCKED，說明要設定 `SPINE_EXE` 或 `--spine-exe`，JSON 與圖片仍正常輸出

#### Scenario: 只有試用版
- **WHEN** 只找到 `SpineTrial.com`
- **THEN** `spine_import.status` 為 BLOCKED，說明試用版無法匯入與存檔，`spine/` 內沒有 `.spine` 檔

### Requirement: Python Simulation Preview
系統 SHALL 能不依賴 Spine 而由 Spine JSON 輸出每個動畫的預覽 GIF，每一幀與檔名 MUST 標示為 Python Simulation Preview，且 MUST NOT 被記錄為 Spine 算圖或匯入驗證的證據。

#### Scenario: 輸出預覽
- **WHEN** 執行 `c2s preview`
- **THEN** `preview/` 內每個動畫各有一個 GIF，幀數大於 1，畫面上有「Python Simulation Preview」字樣

#### Scenario: 動畫確實在動
- **WHEN** 比較 `happy` 預覽的第一幀與中間某一幀
- **THEN** 兩幀的像素內容不同
