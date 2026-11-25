## ADDED Requirements

### Requirement: 永久素材不放在 output
正式的 `parts.json`、遮罩與人工修補圖 SHALL 存放在圖片旁（`<圖名>.parts.json`、`<圖名>.overrides/`），工作目錄內的 `parts.json` MUST 只是正規化複本並記錄來源路徑。

#### Scenario: 圖片旁的 parts.json 是正式來源
- **WHEN** 圖片旁有 `<圖名>.parts.json`，且工作目錄內有一份不同內容的 `parts.json`
- **THEN** analyze 使用圖片旁的版本，並把它的正規化複本（含 `source` 路徑）寫入工作目錄

#### Scenario: 人工修補圖存到永久位置
- **WHEN** 執行 `c2s prepare --replace head=fixed.png`，而 parts.json 來自圖片旁
- **THEN** 修補圖被複製到 `<圖名>.overrides/head.png`，不是工作目錄

### Requirement: 刪除 output 後可完整重建
刪除整個工作目錄後，以同一個指令重跑 SHALL 產生相同的圖層、骨架、動畫與修補狀態。

#### Scenario: 重建包含人工修補
- **WHEN** 某部件已用 `--replace` 替換，之後刪除工作目錄並重跑 `c2s run`
- **THEN** 新的圖層與替換後的圖片位元組相同，狀態為 `replaced`，`spine/character.json` 與刪除前相同