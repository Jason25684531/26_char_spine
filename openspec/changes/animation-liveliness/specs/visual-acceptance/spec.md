## ADDED Requirements

### Requirement: 視覺驗收總覽
系統 SHALL 為每個角色輸出一張視覺驗收圖，包含：

- Happy 與 Idle 的關鍵影格。
- 接觸點標示。
- 拆圖重組對照。

所有畫面都 MUST 標示為 Python Simulation Preview。

#### Scenario: 產生總覽
- **WHEN** 對完成的工作目錄產生視覺驗收
- **THEN** 輸出一張 PNG，含上述三部分；接觸點的位置取自 rig.json 的 contacts