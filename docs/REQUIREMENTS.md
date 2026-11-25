# 需求與假設

Grill Me 結果（2026-11-23）。正式規格以 `openspec/changes/character-to-spine-mvp/` 為準，這份文件是需求共識的摘要；決策原文見 `docs/DECISIONS.md`。

## 目標

把一張 2D 角色圖片（PNG／JPG）變成可在 Spine 內編輯的專案：透明分層 PNG、骨架、Idle 與 Happy 動畫。工具要能重複用在不同角色上，並同時提供 Python CLI（`c2s`）與 Skill 兩個入口，兩者共用同一套 Python 核心。

## 必要功能

| # | 需求 | 驗收方式 |
|---|---|---|
| R1 | 讀取 PNG／JPG，沒有透明度時自動去背；原圖不被覆寫 | 原圖雜湊值前後相同 |
| R2 | 依 `parts.json` 切出透明分層 PNG，每個部件有名稱、位置、尺寸、pivot、前後順序 | 圖層重組後與原圖比對 |
| R3 | 支援外部遮罩匯入、只重做單一部件、用人工修好的 PNG 取代單一部件 | 自動測試 |
| R4 | 被遮擋區域：小面積自動填補，大面積列為人工修補任務；輸出 `missing_parts.json`、`repair_tasks.md`、`layer_preview.png` | 自動測試，輸出檔內容檢查 |
| R5 | 自動建立人形／Q 版骨架：最少 6 個部件（頭、身體、左右手、左右腳），可增加頭髮、裙擺、道具等部件 | 用骨架資料重新算圖，與圖層重組比對 |
| R6 | 自動產生 Idle 與 Happy 動畫，Happy 至少 2 秒，都是可在 Spine 修改的骨架關鍵影格 | 驗證器檢查 timeline 結構與長度 |
| R7 | 輸出 Spine JSON 與圖片；有完整版 Spine CLI 時匯入成 `.spine` 並往返驗證 | 無完整版時標 BLOCKED |
| R8 | CLI：`analyze`、`prepare`、`rig`、`animate`、`export`、`validate`、`run` | 每個指令都有實際執行的測試 |
| R9 | Skill 呼叫同一套 Python 核心，Claude 與 Codex 共用 | 兩邊的 Skill 都只呼叫 `c2s` |
| R10 | 圖層不齊時不假裝能綁定：列出缺少的部件與接續步驟 | 自動測試（結束碼 2） |
| R11 | 至少兩組不同的真實角色跑同一套流程 | `人.png` 與 `转场2.png` |
| R12 | 每個驗收項目的狀態只用 PASS／FAIL／BLOCKED／NOT_TESTED，並附證據 | `validation_report.json`、`docs/TEST_RESULTS.md` |
| R13 | 交付打包（分層素材、Spine 專案、預覽、簡報、原始碼、測試報告） | 打包腳本與目錄檢查 |

## 不在第一版範圍

- 非人形角色、Mesh、IK、物理模擬、進階動畫。
- 上臂／前臂、大腿／小腿的自動細拆（可用增加部件的方式手動達成）。
- 任何 AI 圖片生成或 Inpainting；本地 AI 模型；第三方付費 API；Web 服務。
- 表情切換（換嘴型、眨眼）。

## 限制

- 不使用 API Key。語意辨識由已登入的 Claude Code／Codex 在 Skill 層完成，Python CLI 單獨執行時只處理資料。
- 真實素材只在本機與 Claude Code 內使用，不上傳到其他服務。
- Agent 不購買授權、不代為登入。

## 假設

| # | 假設 | 若不成立 |
|---|---|---|
| A1 | 使用者會取得 Spine Essential 或 Professional 授權 | `.spine` 相關項目維持 BLOCKED，交付 Spine JSON 加圖片 |
| A2 | 完整版 Spine 4.3 能匯入本專案產生的 JSON | 依實際錯誤訊息調整匯出格式，`--spine-version` 可切換版本字串 |
| A3 | Agent 看圖標出的多邊形精度足以切出可用圖層 | 邊緣不準的部件改用外部遮罩，或人工修好後用 `--replace` 匯回 |
| A4 | 主要角色被吉他、頭髮遮住的區域可以靠「動作幅度不要太大」加自動填補處理 | 列為人工修補任務，由使用者補畫 |
| A5 | 試用版 Spine 的 Import Data 可以讓使用者目視確認 JSON（尚未驗證） | 只能等完整版授權 |

## 目前的阻礙

| 項目 | 狀態 | 原因 | 解除條件 |
|---|---|---|---|
| 用 Spine CLI 建立 `.spine` | BLOCKED | 只有試用版，CLI 沒有匯入參數，也不能存檔 | 使用者安裝並啟用完整版 |
| `.spine` 往返驗證、可編輯性驗證 | BLOCKED | 同上 | 同上 |
| Spine 算圖的動畫預覽 | BLOCKED | 同上 | 同上；在那之前提供 Python Simulation Preview |

## 素材分析

| 檔案 | 內容 | 用途 |
|---|---|---|
| `人.png`（630×887） | 正面、抱吉他、雙腳朝前坐跳姿勢。吉他擋住大部分身體與裙子上緣，雙手在吉他前面 | **主要角色** |
| `转场2.png`（942×1246） | 3/4 側面站姿、抬頭、一手上舉一手捧花瓣，沒有吉他。周圍有散落的花瓣與光效 | **第二組真實角色**（只取角色本體，特效不納入部件） |
| `人物 拷贝.png`（697×880） | 3/4 側面跑步、抱吉他 | 姿勢參考 |
| `预中奖.png`（1075×890） | 3/4 側面拋花瓣、單腳後踢，左側有大片花瓣特效 | 動作參考 |

四張圖的邊緣都有不透明的殘留色塊（去背不乾淨的痕跡），切圖時由部件範圍排除。

主要角色預計的部件（執行時依實際切圖結果調整）：`hair_back`、`leg_l`、`leg_r`、`skirt`、`body`、`guitar`、`arm_l`、`arm_r`、`head`、`flower_crown`。
