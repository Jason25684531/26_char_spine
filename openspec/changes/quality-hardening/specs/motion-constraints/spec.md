## ADDED Requirements

### Requirement: 部件接觸約束
`parts.json` 的部件 SHALL 可以用 `attach` 宣告必須保持接觸的其他部件。動畫中兩者的重疊量相對初始姿勢 MUST 維持在設定範圍內，否則視為分離或穿插異常。

#### Scenario: 宣告不存在的部件
- **WHEN** `attach` 指向不存在的部件
- **THEN** analyze 回報 `parts_errors`，結束碼 2

#### Scenario: 手離開道具
- **WHEN** 宣告手臂 attach 道具，而手臂動作幅度大到離開道具
- **THEN** 品質報告列出分離異常，歸因到手臂與道具