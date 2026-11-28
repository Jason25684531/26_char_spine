---
name: character-to-spine
description: 把一張人形／Q 版 2D 角色圖片（PNG/JPG）自動做成 Spine 骨架動畫：分析角色、拆成透明分層 PNG、補被遮住的部分、建立骨架、產生 Idle 與 Happy 動畫、逐格品質檢查，輸出 Spine JSON、動畫預覽與人工補畫清單。Use when the user wants to 拆圖、拆補圖、分層、綁骨架、做 Spine 動畫或 Idle／Happy 動畫 for a character image, or mentions Character-to-Spine, c2s, parts.json.
metadata:
  version: "1.2.0"
---

# Character-to-Spine

使用者只提供圖片和一句話，其餘由你完成，**不要請使用者執行任何指令**。全程（包括最後的報告）用使用者提問的語言回覆：中文提問就用中文，不要因為檔名或文件是英文就改用英文。

所有影像處理都由本 Skill 內附的 `c2s` 完成。你只負責 Python 做不到的兩件事：**看圖判斷部件**（寫 parts.json），以及**檢視輸出、修正 parts.json**。不要自己寫切圖、補圖、骨架或診斷程式，不要用其他方式產生 Spine 檔；要查原因就看 c2s 輸出的報告與圖片。所有檔案都留在目前的專案資料夾內。

## 執行 c2s

指令一律寫成（`<SKILL_DIR>` 是載入本 Skill 時顯示的 Base directory，路徑要加引號）：

```
python "<SKILL_DIR>/scripts/c2s.py" <子命令> [參數]
```

- 先單獨執行一次 `python "<SKILL_DIR>/scripts/c2s.py" --version`，timeout 設 10 分鐘：第一次使用會在 `<SKILL_DIR>/.venv` 安裝執行環境（需要網路，約 1～3 分鐘），之後就很快；Skill 資料夾唯讀時（例如 Codex 沙盒）會自動改裝在目前專案的 `.c2s-runtime/`，不要自己複製 c2s。
- Windows 找不到 `python` 時改用 `py -3`。需要 Python 3.11 以上；沒有就請使用者安裝 Python，這是唯一需要使用者動手的情況。
- 不要另外 `pip install`，也不要到別的資料夾找 `c2s`。

以下用 `c2s` 代表上面那一整串。

## 規則

- 角色圖片只在本機與目前的對話中使用，不要上傳到其他服務。唯一例外：使用者明確同意後，交給 Codex 內建 `image_gen` 補畫被遮住的部件（見「生成式補圖」）。原圖不可修改。
- 永久素材放在圖片旁：`<圖名>.parts.json`、遮罩、人工修補圖 `<圖名>.overrides/`。`output/<圖名>/` 只放可重建的產物。
- 回報狀態只用 PASS／FAIL／BLOCKED／NOT_TESTED，以 `validation_report.json` 的每一項為準，不要看結束碼就說成功。
- `BLOCKED`、`NOT_TESTED` 不是完成。`.spine` 專案需要完整版 Spine，沒有就照實回報 BLOCKED，其餘輸出照常交付。
- 預覽 GIF 是 **Python Simulation Preview**，不是 Spine 算圖，回報時要這樣稱呼。
- 自動補上的區域只是草稿。`needs_manual` 的部件要列給使用者，不能說已修好。
- 只看這張圖本身判斷部件，不要讀專案裡其他角色的 `parts.json` 或輸出。

## 流程

1. **分析**：`c2s analyze <圖片>`。沒有 parts.json 時結束碼 2，工作目錄 `output/<圖名>/` 會有 `grid_overlay.png`（原圖加上每 50px 一條、標了座標的格線）。
2. **寫 parts.json**：先讀 `references/parts-format.md`，再開 `grid_overlay.png` 看圖，寫出圖片旁的 `<圖名>.parts.json`。超出支援範圍時照該文件宣告 `unsupported`。
3. **跑完整流程**：`c2s run <圖片>`（預設產生 Idle 與 Happy）。依序執行切圖、補圖、骨架、動畫、逐格品質檢查與自動修正（最多 3 輪）、Spine JSON 匯出、驗證、預覽、報告。
   - 結束碼：0 完成（仍要看驗證報告）、1 失敗（看 `c2s_error.log`）、2 還缺資料（照 `message` 補上再跑）、3 宣告超出範圍（回報原因，不要宣稱成功）。
4. **檢查切圖**：開 `layer_preview.png`，三欄是原圖、圖層重組（洋紅＝不屬於任何角色部件、已自動收進 `fx` 圖層的像素）、部件外框與 pivot。
   - 貼著部件的細碎邊緣（髮絲、蕾絲、描邊光暈）會自動併入最近的部件，多邊形不必畫到像素級。
   - 散落的特效是洋紅是正確的：它們在 `fx` 圖層，跟著角色跳但不轉動，可在 Spine 內單獨編修。
   - 角色身上有一整塊洋紅（漏畫的頭髮、尾巴、手）：照 `missing_parts.json` 的 `unassigned_regions` 擴大最近的部件或新增部件，否則它會被當成特效、不跟著肢體動。
   - 邊界切錯、pivot 不在關節、前後順序不對：改 parts.json 後重跑 `c2s run`。
5. **檢查骨架與動畫**：開 `report/visual_check.png`（Idle、Happy 關鍵影格與接觸點），對照 `quality/quality_report.json` 的 `unresolved` 與它指出的異常影格（紅色標出問題）。逐項確認：
   - 關節位置合理：肩、脖子、髖部轉動時，肢體沒有繞著手肘、手腕或部件中央轉。
   - 手與道具：拿著的東西跟著手、抱著的樂器帶著雙手，接觸點（實心點在空心圈中央）沒有分開。
   - 前後順序：舉起的手沒有鑽到頭髮、帽子後面消失（z 太小），抬手後原位置沒有露出透明的洞。
   - 沒有明顯破圖：`gap` 擴大兩個部件的重疊；`attach` 檢查 pivot；`exposure` 是草稿露出，已列入補畫清單。
   - 坐姿、躺姿或只剩整體跳動：Happy 模板是站姿跳躍，照實告訴使用者不適用，不要說成功。
   - 開 `preview/*.gif`，用正常速度連續看 3 個循環：循環接起來的地方沒有停頓或跳動、腳沒有沉進地面、頭髮與裙擺比身體晚一點才擺。再慢慢看一次。數值檢查通過不代表畫面合格，兩者在回報中分開寫。
   - `unresolved` 有 `occluded`：舉起的手鑽到頭髮或帽子後面。改 parts.json 的 `z`（手臂放到頭髮前面，或把擋住的髮束拆成獨立部件放到手臂後面），不要縮小動作。
6. **修正**：發現問題就改 parts.json 重跑。同一個問題最多改三輪，仍不行就改用 `mask`，或列為人工修補，並在回報中說明。
7. **回報**：用使用者提問的語言寫（中文提問就整份用中文，包括表格與中途的進度說明，檔名、部件名稱是英文也一樣），固定包含：
   - 整體狀態，以及 `validation_report.json` 每一項的狀態。
   - 輸出位置：`layers/`（分層 PNG）、`spine/character.json`（Spine JSON）、`preview/*_python_simulation_preview.gif`、`validation_report.json`、`report/visual_check.png`。
   - 需要人工補畫的部件，依 `report/repair_priority.md` 的優先順序，附 `report/repair_<部件>.png`（原圖、目前圖層、動畫中露出最多的三格對照）、`repair_masks/`（自動補上的區域）與 `repair_tasks.md`（文字版待修清單）的位置。
   - 修好後的匯回方式：把修好的 PNG 給你，你執行 `c2s prepare --replace <部件>=<修好的.png>` 再 `c2s run <圖片>`。
   - 你在第 5 步看到、但自動檢查沒抓到的問題。

## 生成式補圖（有內建 image_gen 時）

被大面積遮住的部件（`missing_parts.json` 的 `needs_manual`，例如吉他後面的身體、裙子下的腿）可以用 Codex 內建的 `image_gen` 補畫。只有你的工具清單裡真的有內建 `image_gen` 時才做；沒有（例如在 Claude Code）就跳過這一節，照上面的流程回報人工補畫清單。不要改用 CLI、API Key、付費 API 或其他模型，也不要叫使用者選模型。

1. **先問一次**：「要不要讓我把這張角色圖交給 Codex 內建的 image_gen（雲端）補畫被遮住的部分？」使用者明確同意才執行 `c2s consent <圖片>`；不同意就跳過整節。
2. 讀 `references/generative-repair.md`，照裡面的 prompt 範本，對每個要補的部件：用 `view_image` 開 `output/<圖名>/gen_inputs/<部件>.png`（被遮住的區域已塗成洋紅色），以這張圖為編輯目標呼叫 `image_gen`。
3. 把 `image_gen` 的**原始輸出**從 `$CODEX_HOME/generated_images/...` 複製到 `output/<圖名>/incoming/<部件>.png`。不要自己裁切、縮放、對齊、合成或後製，c2s 會處理；先貼回原圖的檔案會被拒絕。
4. 執行 `c2s prepare --generated <部件>=output/<圖名>/incoming/<部件>.png --prompt "<你實際用的 prompt>"`。
   - 結束碼 0：通過，部件狀態 `ai_repaired`，原圖看得見的像素沒有改變。
   - 結束碼 2：沒通過，`message` 說明原因（沒對齊、接縫不連續、沒有移除遮擋者）。只針對那個原因改 prompt 再生成一次。同一部件最多 3 次，第 3 次沒通過會自動列為人工補畫，不要再試。
5. 開 `layers/<部件>.png` 與 `layer_preview.png` 目視：沒有殘留遮擋者（花瓣、吉他）、肢體數量與關節正確、顏色與材質和原圖一致。發現問題就在回報中列出，不要說已補好。
6. 全部部件處理完後執行 `c2s run <圖片>`，照第 4～7 步檢查與回報。回報時列出哪些部件是 AI 補圖（`ai_repaired`）、哪些仍需人工，以及每個部件用了幾次。

## 使用者用一句話修改

- 「只要拆補圖」：`c2s analyze` → 寫 parts.json → `c2s prepare` → 生成式補圖（如上）→ 回報圖層，不建骨架與動畫。
- 「重新補齊某個部件，其他保持不變」：只對那個部件做生成式補圖第 2～5 步，再 `c2s run`。其他部件的圖層不會改變。
- 「動作更活潑」「頭髮多擺一點」「Idle 小一點」：在 parts.json 寫 `motion_overrides`（見 `references/parts-format.md`），再 `c2s run`。回報調整前後的倍率；有破圖時照實說，不要自己把倍率改回去。
- 「輸出 Spine 動畫專案」：`c2s export` 後 `c2s validate`。沒有完整版 Spine 時 `.spine` 為 BLOCKED，只交付 Spine JSON，不要把 JSON 或 GIF 稱為 Spine 原始專案。

分步指令（同一個工作目錄，後面的指令不必再帶圖片）：`c2s analyze <圖片>` → `c2s prepare` → `c2s rig` → `c2s animate --motion happy` → `c2s refine` → `c2s validate` → `c2s preview`。平常直接用 `c2s run`。任何指令都可加 `--workdir <目錄>`。有完整版 Spine 時，設定環境變數 `SPINE_EXE` 指向 `Spine.com`，`c2s run` 會一併建立 `.spine` 專案。
