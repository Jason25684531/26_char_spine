## ADDED Requirements

### Requirement: 逐格動畫品質檢查
系統 SHALL 以 Python Simulation 逐格檢查每個動畫，量測透明破洞（被角色包住、且不是由新接觸圍出的透明區）、關節縫隙（相鄰部件之間新出現的透明夾縫）、`attach` 部件分離與補圖露出，並寫出 `quality/quality_report.json`，內容包含每類異常的最大值、所在影格與歸因的骨頭或部件。

#### Scenario: 正常動畫沒有異常
- **WHEN** 檢查一個部件彼此有足夠重疊、只有溫和 idle 動作的合成角色
- **THEN** 四類檢查都在門檻內

#### Scenario: 抓到關節縫隙
- **WHEN** 手臂與身體只重疊 2px，手臂轉動時兩者之間透出背景細縫
- **THEN** 報告出現該手臂的關節縫隙（新增的透明夾縫像素 ÷ 初始接觸區面積超過門檻），歸因到該手臂骨頭

#### Scenario: 抓到補圖露出
- **WHEN** 遮住某部件的手臂大幅移開
- **THEN** 報告列出被遮部件的補圖露出比例大於 0

### Requirement: 異常影格供自我檢查
每個超過門檻的異常 SHALL 輸出一張影格圖，標出問題區域，檔名包含動畫名稱、時間與異常類別。

#### Scenario: 輸出異常影格
- **WHEN** 檢查發現異常
- **THEN** `quality/` 內有對應的 PNG，`quality_report.json` 記錄其路徑