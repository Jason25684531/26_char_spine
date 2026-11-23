## ADDED Requirements

### Requirement: 補圖可靠度以實測值判定
prepare SHALL 對每個有被遮擋區域的部件記錄 `hidden_ratio`、`holdout_error`、`contour_hidden` 與 `occluders`，並輸出補圖遮罩。被遮擋面積超過 35% MUST 為 `needs_manual`；其餘部件在 `holdout_error` 或 `contour_hidden` 超過門檻時 MUST 標記 `repair_reliable: false`。

#### Scenario: 單色部件可靠
- **WHEN** 被遮擋的部件是單一顏色
- **THEN** `holdout_error` 接近 0，`repair_reliable` 為 true

#### Scenario: 高紋理部件不可靠
- **WHEN** 被遮擋的部件是高對比的細紋理（例如條紋）
- **THEN** `holdout_error` 超過門檻，`repair_reliable` 為 false

#### Scenario: 被遮住的輪廓
- **WHEN** 部件範圍的輪廓線有一大段落在被遮擋區
- **THEN** `contour_hidden` 反映該比例，超過門檻時 `repair_reliable` 為 false

### Requirement: 不可靠且會露出的補圖不得宣稱成功
refine 之後，`repair_reliable` 為 false 且動畫中露出超過門檻的部件 MUST 改為 `needs_manual`，並出現在 `repair_tasks.md`，原因中列出實測的露出比例。

#### Scenario: 不可靠補圖露出
- **WHEN** 一個不可靠的部件，在三輪修正後動畫中仍露出補圖
- **THEN** 狀態為 `needs_manual`，`manual_repairs` 檢查為 BLOCKED