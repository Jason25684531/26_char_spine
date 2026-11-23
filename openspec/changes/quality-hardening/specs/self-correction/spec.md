## ADDED Requirements

### Requirement: 自動修正迴圈
`c2s refine` SHALL 執行品質檢查。有可歸因的異常時，把相關骨頭的動作幅度乘以 0.5，重新產生動畫並重新檢查，最多 3 輪修正；某一輪沒有降低總異常量時 MUST 還原到最佳那一輪並停止。每一輪的量測值、歸因與調整內容 MUST 寫入 `quality_report.json`。

#### Scenario: 修正後通過
- **WHEN** 合成角色的身體擠壓幅度放大 3 倍，把不可靠的腿部補圖擠出來
- **THEN** 異常歸因到 body，refine 在 3 輪內降低 body 幅度使露出消失，報告記錄每輪的變化，`tuning.json` 記錄最後的係數

#### Scenario: 修正後仍失敗
- **WHEN** 異常在 3 輪修正後、或修正不再改善時仍存在
- **THEN** 不再重試，`animation_quality` 檢查為 BLOCKED，保留異常影格與每輪紀錄

#### Scenario: 確定性
- **WHEN** 刪除工作目錄後重跑 `c2s run`
- **THEN** `tuning.json` 與上次相同

### Requirement: 驗證報告納入動畫品質
`c2s validate` SHALL 新增 `animation_quality` 檢查：沒有 `quality_report.json` 時為 NOT_TESTED；有未解決的異常時為 BLOCKED，並列出類別與影格；全部在門檻內時為 PASS。

#### Scenario: 尚未執行 refine
- **WHEN** 分步執行到 export 就直接 validate
- **THEN** `animation_quality` 為 NOT_TESTED