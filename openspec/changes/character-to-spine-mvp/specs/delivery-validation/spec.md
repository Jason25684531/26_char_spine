## ADDED Requirements

### Requirement: 輸出驗證器
`c2s validate` SHALL 檢查實際輸出的內容並寫出 `validation_report.json`。檢查項目 MUST 包含：骨頭階層、插槽與附件對應、圖片引用與尺寸、動畫結構與長度、骨架初始姿勢算圖比對、人工修補是否完成、Spine 匯入、往返驗證、Editor 可編輯性。

#### Scenario: 正常輸出
- **WHEN** 對流程完整的合成角色執行 validate
- **THEN** `bones`、`slots`、`image_references`、`animations`、`setup_pose` 皆為 PASS

#### Scenario: 抓到被破壞的輸出
- **WHEN** 刪除 `spine/images/` 內的一張圖、把某個插槽指向不存在的骨頭，或把 `happy` 縮短到 2 秒以下
- **THEN** 對應的檢查項目為 FAIL，並指出是哪個檔案或哪個名稱

#### Scenario: 抓到錯誤的圖層位置
- **WHEN** 把某個附件的位置偏移到明顯錯誤的地方
- **THEN** `setup_pose` 為 FAIL

#### Scenario: 抓到錯誤的圖片內容
- **WHEN** 把 `spine/images/` 內某張圖換成純色或上下翻轉
- **THEN** `setup_pose` 為 FAIL（骨架初始姿勢算圖與原圖在部件範圍內的像素比對）

### Requirement: 狀態與證據
每個檢查項目的狀態 MUST 是 PASS、FAIL、BLOCKED、NOT_TESTED 其中之一，並附上說明。無法在目前環境執行的項目 MUST NOT 標為 PASS。

#### Scenario: 沒有完整版 Spine
- **WHEN** 在只有試用版 Spine 的環境執行 validate
- **THEN** `spine_import` 為 BLOCKED，`spine_roundtrip` 與 `spine_editable` 為 NOT_TESTED，整體狀態不是 PASS

#### Scenario: 有待人工修補的圖層
- **WHEN** 有部件狀態為 `needs_manual`
- **THEN** `manual_repairs` 為 BLOCKED 並列出部件名稱

#### Scenario: 測試結果紀錄
- **WHEN** 完成一個功能的測試
- **THEN** `docs/TEST_RESULTS.md` 記錄執行的指令、日期、結果，以及每個 spec scenario 對應的測試或證據檔案

### Requirement: 兩組真實角色的通用性驗收
系統 SHALL 以同一套程式與指令處理至少兩組部件組成不同的真實角色，不得為個別角色修改程式。合成角色的結果 MUST NOT 計入這項驗收。

#### Scenario: 兩組真實角色
- **WHEN** 分別對 `examples/real/` 內的兩組角色執行 `c2s run`
- **THEN** 兩組都產生分層 PNG、Spine JSON 與驗證報告，兩者只有 `parts.json` 與圖片不同

#### Scenario: 程式沒有寫死座標
- **WHEN** 檢視 `src/character_to_spine/` 的程式碼
- **THEN** 其中沒有任何特定角色的檔名或像素座標

### Requirement: 交付打包
系統 SHALL 提供腳本，從實際輸出組出 `Character-to-Spine-Deliverables/` 目錄：原始圖、分層素材與 metadata、Spine 專案、動畫預覽、簡報、原始碼與規格、測試報告、README。尚未完成或 BLOCKED 的項目 MUST 在 README 與簡報中標明。

#### Scenario: 打包內容
- **WHEN** 執行打包腳本
- **THEN** 目錄含有 `01_Original_Images` 到 `07_Test_Reports` 與 `README.md`，每個目錄內的檔案都複製自實際輸出

#### Scenario: 缺少 .spine 時的標示
- **WHEN** `.spine` 因授權而未產生
- **THEN** `03_Spine_Project/` 內有 `character.json` 與 `images/`，README 明確寫出 `.spine` 為 BLOCKED 及原因，目錄內沒有空白或假的 `.spine`

#### Scenario: 簡報內容來自實際輸出
- **WHEN** 產生 `workflow.pptx`
- **THEN** 簡報中的圖片取自工作目錄的實際輸出檔，測試結果取自 `validation_report.json`，並把每個環節標為已完成、半自動、人工修正或未來規劃
