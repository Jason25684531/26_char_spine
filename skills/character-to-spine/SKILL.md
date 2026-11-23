---
name: character-to-spine
description: 把一張 2D 角色圖片（PNG/JPG）做成 Spine 骨架動畫：看圖寫 parts.json、用 c2s 切出透明分層 PNG、建立骨架、產生 Idle/Happy 動畫、輸出 Spine JSON 並驗證。Use when the user wants to rig / split / animate a 2D character for Spine, or mentions c2s, parts.json, Character-to-Spine.
compatibility: 需要已安裝本專案的 Python 套件（提供 c2s 指令）。Claude Code 與 Codex 共用這份內容。
metadata:
  version: "0.1.0"
---

# Character-to-Spine

所有處理都由 `c2s` 指令完成，你（Agent）只負責兩件 Python 做不到的事：**看圖判斷部件**，以及**檢視輸出、修正 parts.json**。不要自己寫切圖或骨架程式，也不要用其他方式產生 Spine 檔。

`c2s` 位置：專案虛擬環境的 `.venv\Scripts\c2s.exe`（Windows）或 `.venv/bin/c2s`；已加入 PATH 時直接用 `c2s`。

## 規則

- 角色圖片只能在本機與目前的 Agent 內使用，不要上傳到其他服務。
- 原圖不可修改。
- **永久素材放在圖片旁**：`<圖名>.parts.json`、遮罩、人工修補圖 `<圖名>.overrides/`。
- `output/<圖片檔名>/` 只放可重建的產物，刪掉後重跑 `c2s run` 會得到相同結果。
- 回報狀態只用 PASS／FAIL／BLOCKED／NOT_TESTED，以 `validation_report.json` 的每一項為準，不要看結束碼就說成功。
- `BLOCKED` 與 `NOT_TESTED` 不是完成。尤其 `.spine` 專案需要完整版 Spine，沒有就照實回報 BLOCKED。
- 預覽 GIF 是 Python Simulation Preview，不是 Spine 算圖，回報時要這樣稱呼它。
- 自動填補的區域只是草稿；`needs_manual` 的部件要列給使用者，不能說已修好。

## 流程

1. **分析**：`c2s analyze <圖片>`
   - 圖片沒有透明度時會自動去背（只適用純色背景）。
   - 沒有 parts.json 時結束碼為 2，工作目錄會有 `parts.template.json` 與 `grid_overlay.png`。
2. **看圖寫 parts.json**：開啟 `grid_overlay.png`（原圖加上每 50 像素一條、標了座標的格線），依下方格式寫出**圖片旁的** `<圖名>.parts.json`。工作目錄內的 `parts.json` 只是複本，改了會被覆寫。
3. **跑完整流程**：`c2s run <圖片> --motion happy`
   - 結束碼 2 表示還缺資料，照輸出的 `message` 補上後重跑。
   - 流程內含 `c2s refine`：逐格檢查破洞、關節縫隙、接觸分離、補圖露出，自動降低相關骨頭的幅度，最多 3 輪。
4. **檢查切圖**：開啟 `layer_preview.png`，三欄依序是原圖、圖層重組（洋紅＝未分配像素）、部件外框與 pivot 標示。
   - `missing_parts.json` 的 `unassigned_regions` 列出每塊漏畫區域與最近的部件，照著擴大該部件的 polygon。
   - 重組結果和原圖有落差、部件邊界切錯、pivot 位置不對時，修改 `parts.json` 後重跑 `c2s run`。
   - 同一個問題最多修三輪；仍然不行就改用遮罩（`mask`），或列為人工修補任務。
5. **檢查動畫品質**：讀 `quality/quality_report.json`，開啟 `unresolved` 列出的異常影格（`quality/round_N/*.png`，紅色標出問題區域）。
   - `gap`（關節縫隙）：相鄰部件重疊太少，擴大兩者的 polygon 讓它們多重疊幾個像素。
   - `attach`（接觸分離）：確認 pivot 在關節上，或降低該部件的 `motion`。
   - `hole`（破洞）：看是哪兩個部件分開，處理方式同 gap。
   - `exposure`（補圖露出）：該部件已被改為 `needs_manual`，列入修補任務。
   - 再開 `preview/happy_python_simulation_preview.gif` 目視：
   - 肢體轉錯方向：檢查 `_l`／`_r` 與 pivot。
   - 動作太大露出沒畫的區域：降低該部件的 `motion`。
   - 道具或頭髮亂甩：確認 `role` 與 `parent`。
6. **處理修補任務**：讀 `repair_tasks.md`，把需要人工修補的部件告訴使用者。
   - 使用者修好後執行 `c2s prepare --replace <部件>=<修好的.png>`（會存到 `<圖名>.overrides/`），再執行 `c2s run <圖片>`。
7. **回報**：逐項列出 `validation_report.json` 的狀態，以及待人工處理的部件。

分步指令（同一個工作目錄，後面的指令不必再帶圖片）：`c2s analyze <圖片>` → `c2s prepare` → `c2s rig --preset humanoid-chibi` → `c2s animate --motion happy` → `c2s refine` → `c2s validate` → `c2s preview`。`c2s refine` 結束時會 export；單獨重跑 `c2s export` 會讓舊的品質報告失效（驗證報告的 `animation_quality` 變成 NOT_TESTED）。任何指令都可加 `--workdir <目錄>`。

結束碼：0 完成（但仍要看驗證報告的各項狀態）、1 失敗（看 `c2s_error.log`）、2 需要補資料。

## parts.json 格式

```json
{
  "version": 1,
  "preset": "humanoid-chibi",
  "parts": [
    {"name": "body",  "polygon": [[120, 400], [260, 400], [270, 560], [110, 560]], "z": 3},
    {"name": "arm_l", "polygon": [[...]], "z": 7, "pivot": [140, 410], "motion": 0.3},
    {"name": "hair_back", "polygon": [[...]], "z": 0, "parent": "head", "role": "hair"},
    {"name": "guitar", "mask": "masks/guitar.png", "z": 6, "parent": "body", "role": "prop"}
  ]
}
```

| 欄位 | 必填 | 說明 |
|---|---|---|
| `name` | 是 | 英數字與底線，不可重複，不可用 `root`、`hip` |
| `polygon` 或 `mask` | 二擇一 | 原圖像素座標（左上為原點）。`mask` 是與原圖同尺寸的灰階 PNG，白色為範圍，路徑相對於 parts.json |
| `z` | 是 | 前後順序，越大越前面，不可重複 |
| `pivot` | 否 | 關節位置 `[x, y]`，例如頭接脖子處、手臂接肩膀處。省略時依部件類型估計 |
| `parent` | 否 | 跟著哪根骨頭動。必要部件由 preset 決定；其他部件預設 `body` |
| `role` | 否 | 套用哪種動作：`head` `body` `arm` `leg` `hair` `skirt` `prop` `accessory`。必要部件由名稱推得，其他預設 `accessory` |
| `motion` | 否 | 動作幅度係數，預設 1.0，0 表示不動 |
| `attach` | 否 | 必須保持接觸的部件名稱（或清單），例如抱著吉他的手 `"attach": "guitar"`。動畫會自動限制幅度，讓接觸點位移不超過角色高度的 1%；初始姿勢沒有接觸時 rig 會要求修正 |

**必要部件**（preset `humanoid-chibi`）：`head`、`body`、`arm_l`、`arm_r`、`leg_l`、`leg_r`。`_l`／`_r` 指**畫面**的左右，不是角色自己的左右。

**額外部件**：頭髮、裙擺、樂器、配件等會影響動畫的元素都應該拆出來，數量不限。

## 寫多邊形的要點

- **範圍要包含被擋住的部分。** 例如手臂擋住身體，身體的多邊形仍要畫完整的身體輪廓，被擋住的區域系統會自動填補或列為修補任務。實際可見的像素歸 z 最大的部件。
- **部件交界要畫在真正的分界線上。** 頭與身體分在脖子，手臂分在肩膀，腿分在裙擺下緣或褲管。
- **散落的特效**（花瓣、光點）不要包含在任何部件裡，系統會自動排除，也不影響骨架位置。
- **持物的手臂**（抱著樂器、捧著東西）用 `attach` 宣告接觸，系統會自動算出不會分離的幅度。
- **相鄰部件要互相重疊**幾個到十幾個像素（例如手臂蓋過肩膀），轉動時才不會透出細縫。
- **pivot 放在關節。** 肩膀、脖子、髖部、頭髮的根部、道具被握住的地方。
