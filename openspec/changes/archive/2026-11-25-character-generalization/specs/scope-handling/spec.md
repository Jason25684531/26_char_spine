## ADDED Requirements

### Requirement: 宣告超出支援範圍
`parts.json` SHALL 接受頂層欄位 `unsupported`（非空字串，說明原因）。出現時，`c2s analyze` 與 `c2s run` MUST 以狀態 `unsupported`、結束碼 3 結束，把原因寫入 `analysis.json` 與 `validation_report.json`，且 MUST NOT 產生骨架、動畫或 Spine JSON。

#### Scenario: 非人形角色
- **WHEN** `parts.json` 含 `"unsupported": "四足動物，沒有可對應的手臂與腿"`
- **THEN** `c2s run` 結束碼為 3，輸出包含該原因，工作目錄沒有 `rig.json`

#### Scenario: 殘留的舊輸出
- **WHEN** 工作目錄先前有成功的輸出，之後 `parts.json` 改為宣告 unsupported
- **THEN** 舊的骨架與動畫被移除或標為失效，驗證報告不會顯示 PASS

### Requirement: 宣告看不到的必要部件
`parts.json` SHALL 接受頂層欄位 `absent`（必要部件名稱的清單）。被列入的部件不建立骨頭與動畫，流程其餘部分照常完成，並在 `repair_tasks.md` 列為可選擇補畫。`head` 與 `body` MUST NOT 被列入。

#### Scenario: 3/4 側面遠側的手
- **WHEN** `parts.json` 含 `"absent": ["arm_r"]` 且沒有 `arm_r` 部件
- **THEN** `c2s run` 完成，Spine JSON 沒有 `arm_r` 骨頭，驗證報告註明該部件缺席

#### Scenario: 列入不可缺的部件
- **WHEN** `absent` 含 `body`
- **THEN** `c2s analyze` 結束碼為 2，訊息說明 `head`、`body` 不可缺席

#### Scenario: 同時宣告缺席又提供部件
- **WHEN** `absent` 含 `arm_r`，`parts` 也有 `arm_r`
- **THEN** `c2s analyze` 結束碼為 2，訊息指出矛盾

### Requirement: 既有角色不受影響
沒有這兩個欄位的 `parts.json` MUST 得到與不認識這兩個欄位時相同的輸出。

#### Scenario: 既有角色回歸
- **WHEN** 對 `人.png` 與 `转场2.png` 重跑 `c2s run`
- **THEN** Spine JSON、圖層與驗證報告的各項狀態與修改前相同

### Requirement: Skill 說明範圍宣告
`SKILL.md` 或它引用的 `references/` 文件 SHALL 說明何時使用 `unsupported` 與 `absent`、結束碼 3 的意義，以及回報時要告訴使用者限制所在。

#### Scenario: Agent 遇到超出範圍的圖
- **WHEN** Agent 依 Skill 處理一張非人形角色圖
- **THEN** Agent 的回報指出不支援的原因，沒有宣稱成功
