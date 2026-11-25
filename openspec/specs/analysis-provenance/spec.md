# analysis-provenance Specification

## Purpose
TBD - created by archiving change character-generalization. Update Purpose after archive.
## Requirements
### Requirement: 由真正被觸發的 Skill 產生 parts.json
每個測試案例的 `parts.json` SHALL 由一個全新的 Claude Code session（`claude -p`，工作目錄為 repo 外只含 Skill 與圖片的沙盒，Skill 依 README 安裝打包後的套件，c2s 由 Skill 自己的 `.venv` 提供）產生，提示只包含圖片路徑與一句需求，不得提到 `SKILL.md`、`c2s` 或 `parts.json`。每個案例 MUST 用自然語言觸發；至少一個案例另以 `/character-to-spine` 觸發。使用者 MUST NOT 需要手寫 `parts.json`。

Skill 觸發驗證 MUST 以該 session 的工具呼叫紀錄（stream-json）為證據：自然語言觸發要出現名稱為 `character-to-spine` 的 Skill 工具呼叫，且之後有執行 `c2s` 的指令。slash 觸發不會產生 Skill 工具呼叫（headless 模式不記錄被展開的提示），改以間接證據判定：`character-to-spine` 出現在可用的 slash 指令中，沒有讀取 `SKILL.md`，而前兩個指令就是 Skill 的 `c2s` 指令。只讀取 `SKILL.md` 檔案不算觸發。

#### Scenario: 自然語言觸發
- **WHEN** session 只收到「幫我把這張角色圖做成 Spine 動畫：<路徑>」
- **THEN** 紀錄中有 Skill 工具呼叫 `character-to-spine`，接著有 `c2s` 指令，圖片旁出現 `parts.json`

#### Scenario: 沒有觸發 Skill
- **WHEN** session 自己寫了切圖程式，或只用 Read 讀 `SKILL.md` 而沒有 Skill 工具呼叫
- **THEN** 該案例的 Skill 觸發判定為 FAIL，報告如實記錄

#### Scenario: 失敗時的回報
- **WHEN** `c2s` 結束碼為 1、2 或 3
- **THEN** session 的最後回覆說明失敗或限制原因，沒有宣稱成功

#### Scenario: 保留分析紀錄
- **WHEN** session 結束
- **THEN** `docs/generalization/<id>/` 內有完整的工具呼叫清單、最後回覆，以及它辨識出的部件、遮擋順序、pivot、需補畫部位

### Requirement: 程式查核來源
執行器 SHALL 比對新 `parts.json` 與所有既有 `parts.json`：多邊形逐點相同或僅差平移縮放時判定為雷同。座標 MUST 落在新圖前景外框附近。分析 session 的工具呼叫 MUST NOT 讀取被禁止的路徑。

#### Scenario: 複製舊角色座標
- **WHEN** 新 `parts.json` 的某個多邊形與 `人.parts.json` 的多邊形相同
- **THEN** 來源查核 FAIL，該案例不得判為 PASS 或 PARTIAL

#### Scenario: 查核通過
- **WHEN** 沒有雷同多邊形、座標在外框內、沒有讀取被禁止的路徑
- **THEN** 來源查核 PASS，並在報告標明分析者是同模型的獨立子代理

### Requirement: 分析失敗要記錄原因
分析無法辨識必要部件、道具接觸或遮擋順序時，SHALL 記錄失敗原因，不得套用其他角色的部件配置補上。

#### Scenario: 看不出手臂
- **WHEN** 分析 session 無法在圖上找到某隻手臂
- **THEN** 紀錄說明原因，並以 `absent` 或 `unsupported` 宣告，而不是畫一個猜測的多邊形

