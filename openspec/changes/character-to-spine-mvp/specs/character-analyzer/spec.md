## ADDED Requirements

### Requirement: 讀取角色圖片並建立工作複本
系統 SHALL 接受 PNG 與 JPG 角色圖片，在工作目錄建立 RGBA 工作複本與 `analysis.json`，且 MUST NOT 修改原始圖片。

#### Scenario: 帶透明度的 PNG
- **WHEN** 對一張含有透明像素的 PNG 執行 analyze
- **THEN** 工作目錄出現 `source_rgba.png` 與 `analysis.json`，`alpha_source` 為 `embedded`，原圖的雜湊值不變

#### Scenario: 不透明的純色背景圖片
- **WHEN** 對一張沒有透明度、背景接近純色的圖片執行 analyze
- **THEN** 系統以邊界 flood fill 去背，`alpha_source` 為 `flood-fill`，角色本體保持不透明

#### Scenario: 圖片不存在或沒有前景
- **WHEN** 圖片路徑不存在，或圖片整張透明
- **THEN** 系統回報錯誤並以結束碼 1 結束，不產生後續檔案

### Requirement: parts.json 交換格式
系統 SHALL 以 `parts.json` 作為部件語意資訊的唯一輸入。每個部件 MUST 有唯一的英數字名稱、`polygon`（至少 3 點）或 `mask`（與原圖同尺寸）其中之一，以及數字 `z`；`pivot`、`parent`、`role`、`motion` 為選填。

#### Scenario: 合法的 parts.json
- **WHEN** analyze 找到格式正確且包含 preset 所有必要部件的 `parts.json`
- **THEN** 結果狀態為 `ok`，正規化後的 `parts.json` 寫入工作目錄，遮罩路徑轉為絕對路徑

#### Scenario: 格式錯誤
- **WHEN** `parts.json` 有名稱重複、缺少 `z`、多邊形少於 3 點、遮罩檔不存在或遮罩尺寸與原圖不同
- **THEN** 結果狀態為 `needs_parts`，`parts_errors` 逐條列出是哪個部件、什麼問題

### Requirement: 缺少部件資訊時不假裝完成
當 `parts.json` 不存在或缺少必要部件時，系統 MUST 停在分析階段，列出缺少的部件與接續步驟，且 MUST NOT 以猜測的範圍代替。

#### Scenario: 沒有 parts.json
- **WHEN** 對一張沒有對應 `parts.json` 的圖片執行 analyze
- **THEN** 系統寫出 `parts.template.json`，結果的 `missing_required` 列出 preset 的全部必要部件，`next_steps` 說明要補什麼檔案、下一個指令是什麼，CLI 結束碼為 2

#### Scenario: 缺少部分必要部件
- **WHEN** `parts.json` 只定義了部分必要部件
- **THEN** `missing_required` 只列出缺少的那些，狀態為 `needs_parts`
