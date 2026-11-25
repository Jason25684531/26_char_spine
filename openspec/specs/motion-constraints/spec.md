# motion-constraints Specification

## Purpose
TBD - created by archiving change quality-hardening. Update Purpose after archive.
## Requirements
### Requirement: 部件接觸約束
`parts.json` 的部件 SHALL 可以用 `attach` 宣告必須保持接觸的其他部件。動畫產生時 MUST 依接觸點限制相關骨頭的幅度；動畫中兩者的重疊量相對初始姿勢低於下限時，視為分離異常。

#### Scenario: 宣告不存在的部件
- **WHEN** `attach` 指向不存在的部件
- **THEN** analyze 回報 `parts_errors`，結束碼 2

#### Scenario: 手離開道具
- **WHEN** 宣告手臂 attach 道具，而手臂動作幅度大到離開道具
- **THEN** 品質報告列出分離異常，歸因到手臂與道具

### Requirement: 受約束部件不得穿插
有 `attach` 的部件與道具（role 為 prop），和初始姿勢沒有接觸的其他部件（頭髮背景層除外）在動畫中新產生的重疊，超過較小部件面積的門檻時 SHALL 視為穿插異常，並納入自我修正。

#### Scenario: 道具揮進臉
- **WHEN** 拿在手上的道具隨手臂擺動，蓋到原本沒有接觸的頭部
- **THEN** 品質報告列出穿插異常，歸因到拿道具的手臂；修不掉時 `animation_quality` 為 BLOCKED

#### Scenario: 頭髮背景層不算穿插
- **WHEN** 手臂畫在後方頭髮前面
- **THEN** 不列為穿插異常

