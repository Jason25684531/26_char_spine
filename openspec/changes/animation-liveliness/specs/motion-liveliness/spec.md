## ADDED Requirements

### Requirement: 在品質閘門內增加抱物手臂的動作
對 `attach` 的部件，系統 SHALL 在動畫品質檢查全部通過的前提下，讓接觸點相對身體的位移比原本的固定容許值更大。每個調整都 MUST 量測前後並記錄，品質變差時回退。

#### Scenario: 撥弦手更生動
- **WHEN** 對人.png 執行 `c2s run`
- **THEN** 撥弦手相對身體的位移至少是基準 4.4px 的 3 倍，`animation_quality` 為 PASS，attach 最低值 ≥ 0.6，需人工清單沒有增加

#### Scenario: 其他角色不退步
- **WHEN** 對转场2.png 與合成角色執行 `c2s run`
- **THEN** 品質閘門的結果與調整前相同或更好