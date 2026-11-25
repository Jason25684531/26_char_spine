## ADDED Requirements

### Requirement: 切出透明分層 PNG 與 metadata
系統 SHALL 依 `parts.json` 為每個部件輸出一張裁切到自身範圍的透明 PNG，並在 `metadata.json` 記錄每個部件的名稱、在原圖中的位置與尺寸、pivot、z 順序與狀態。

#### Scenario: 位置資訊正確
- **WHEN** 對已知真實範圍的合成角色執行 prepare
- **THEN** 每個圖層的 `x`、`y`、`w`、`h` 與真實範圍相差不超過 2 像素

#### Scenario: 圖層重組等於原圖
- **WHEN** 把所有圖層依 z 順序疊回畫布
- **THEN** 與原圖角色部分的平均差異 `recompose_mae` 低於 0.02

#### Scenario: 散落的特效不影響角色
- **WHEN** 圖片中有不屬於任何部件的前景像素
- **THEN** 這些像素不出現在任何圖層，其比例寫入 `unassigned_ratio`，骨架原點與外框只由部件範圍的聯集決定

### Requirement: 被遮擋區域分級處理
系統 SHALL 以部件自身可見像素填補被較高 z 部件遮住的區域。被遮擋面積不超過門檻時狀態 MUST 為 `auto_repaired`；超過門檻或完全不可見時狀態 MUST 為 `needs_manual`，且 MUST NOT 被回報為完成。

#### Scenario: 小面積遮擋
- **WHEN** 部件被遮住的面積不超過門檻
- **THEN** 圖層在被遮住的區域有不透明的填補像素，狀態為 `auto_repaired`

#### Scenario: 大面積遮擋
- **WHEN** 部件被遮住的面積超過門檻
- **THEN** 圖層仍輸出填補草稿，狀態為 `needs_manual`，並出現在 `missing_parts.json` 與 `repair_tasks.md`

#### Scenario: 完全被遮住
- **WHEN** 部件沒有任何可見像素
- **THEN** 不輸出該圖層，狀態為 `needs_manual`，修補任務註明需要整張重畫

### Requirement: 修補任務輸出
每次 prepare 系統 SHALL 輸出 `missing_parts.json`、`repair_tasks.md` 與 `layer_preview.png`，內容足以讓人不重新分析就接續修補。

#### Scenario: 修補任務內容
- **WHEN** 有部件狀態為 `needs_manual`
- **THEN** `repair_tasks.md` 列出部件名稱、原因、草稿圖層路徑，以及修好後要執行的 `c2s prepare --replace` 指令與可接受的圖片尺寸

#### Scenario: 檢查圖
- **WHEN** prepare 完成
- **THEN** `layer_preview.png` 並排顯示原圖、圖層重組結果，以及標出每個部件外框、名稱、狀態與 pivot 的標示圖

### Requirement: 外部遮罩、單一部件重做與替換
系統 SHALL 支援以遮罩圖定義部件範圍、只重新處理指定的單一部件，以及用人工修好的 PNG 取代單一部件；替換結果在之後重新執行 prepare 時 MUST 保留。

#### Scenario: 外部遮罩
- **WHEN** 部件以 `mask` 而不是 `polygon` 定義
- **THEN** 圖層範圍等於遮罩的白色區域與前景的交集

#### Scenario: 只重做一個部件
- **WHEN** 執行 `c2s prepare --part head`
- **THEN** 只有 `head` 的圖層檔被重寫，其他圖層檔的內容不變，`metadata.json` 仍包含全部部件

#### Scenario: 替換部件
- **WHEN** 以整張畫布大小或與原圖層相同大小的 PNG 執行 `--replace arm_l=fixed.png`
- **THEN** `arm_l` 的圖層改用該圖，狀態為 `replaced`，再次執行不帶參數的 prepare 後仍然是替換後的圖

#### Scenario: 替換圖尺寸無法定位
- **WHEN** 替換用的 PNG 既不是畫布大小也不是原圖層大小
- **THEN** 系統回報錯誤並說明可接受的尺寸，原圖層不變
