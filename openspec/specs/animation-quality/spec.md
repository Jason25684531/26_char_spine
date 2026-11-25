# animation-quality Specification

## Purpose
TBD - created by archiving change quality-hardening. Update Purpose after archive.
## Requirements
### Requirement: 逐格動畫品質檢查
系統 SHALL 以 Python Simulation 逐格檢查每個動畫，量測透明破洞（被角色包住的透明像素中，初始姿勢被某部件蓋住、而該部件已不在這塊透明區旁邊的部分；初始位置依 body 骨頭換算到當格，初始就是背景的被圍區域不算）、關節縫隙（部件與它在身體結構上的父部件之間新出現的透明夾縫；必要部件依 preset，其他部件依骨架父骨頭，父部件在初始姿勢沒有接觸時才改用接觸最大的鄰居）、`attach` 部件分離與補圖露出，並寫出 `quality/quality_report.json`，內容包含每類異常的最大值、所在影格與歸因的骨頭或部件。

#### Scenario: 正常動畫沒有異常
- **WHEN** 檢查一個部件彼此有足夠重疊、只有溫和 idle 動作的合成角色
- **THEN** 四類檢查都在門檻內

#### Scenario: 抓到關節縫隙
- **WHEN** 手臂與身體只重疊 2px，手臂轉動時兩者之間透出背景細縫
- **THEN** 報告出現該手臂的關節縫隙（新增的透明夾縫像素 ÷ 初始接觸區面積超過門檻），歸因到該手臂骨頭

#### Scenario: 初始就被圍住的背景不是破洞
- **WHEN** 長杖頂端碰到帽簷、或叉腰的手臂與身體圍出一塊背景，動畫中部件微動讓這塊背景「圍起來或打開」
- **THEN** 不列為破洞異常

#### Scenario: 碰巧接觸的部件不是關節
- **WHEN** 手指在初始姿勢碰到頭上的角，接觸面積比肩膀還大
- **THEN** 手臂的關節縫隙仍以手臂與身體之間量測

#### Scenario: 抓到補圖露出
- **WHEN** 遮住某部件的手臂大幅移開
- **THEN** 報告列出被遮部件的補圖露出比例大於 0

### Requirement: 異常影格供自我檢查
每個超過門檻的異常 SHALL 輸出一張影格圖，標出問題區域，檔名包含動畫名稱、時間與異常類別。

#### Scenario: 輸出異常影格
- **WHEN** 檢查發現異常
- **THEN** `quality/` 內有對應的 PNG，`quality_report.json` 記錄其路徑

