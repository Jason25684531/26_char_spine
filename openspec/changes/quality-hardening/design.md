## Context

既有流程：analyze → prepare → rig → animate → export → validate（83 個測試通過）。

這次的限制條件：

- 不重寫已通過測試的模組，只做加法或局部修改。
- 品質門檻必須綁在實測值上。
- Spine Essential 不支援 IK 與 transform constraint，所以約束不能依賴 Spine 的約束功能。

## Goals / Non-Goals

**Goals**

- 刪除 `output/` 後，一個指令重建出相同成果（含人工修補圖）。
- 每個品質條件都有量測值、門檻與證據檔。
- 失敗時能自動找出原因、調整參數、重試三輪，最後如實標記。

**Non-Goals**

- 自動修正多邊形。部件範圍仍由 Agent 依診斷資訊修改。
- Spine 端的約束（IK、transform constraint）。
- 改變 draw order 的動畫。

## Decisions

### 1. 永久素材跟著圖片走，`output/` 只放產物

部件描述的來源優先順序：

1. `--parts` 明確指定的檔案。
2. 圖片旁的 `<圖名>.parts.json`。
3. 工作目錄內的 `parts.json`（僅為相容舊流程）。

工作目錄內的 `parts.json` 改成「正規化複本」，記錄 `source`（來源絕對路徑），每次 analyze 重寫。

人工修補圖存在來源 parts.json 旁的 `<圖名>.overrides/<部件>.png`，`--replace` 也寫到那裡。來源本身就在工作目錄內時，才退回 `工作目錄/overrides/`。

> 取代先前的決策「工作目錄內的 parts.json 優先」：那個做法讓正式資料只存在可刪除的目錄。

### 2. 補圖可靠度用實測值判定

prepare 對每個有被遮擋區域的部件量測：

| 量測值 | 意義 | 算法 |
|---|---|---|
| `hidden_ratio` | 被遮擋面積（既有） | 被遮像素 ÷ 部件像素 |
| `holdout_error` | 這個部件的紋理能不能被邊緣延伸補出來 | 在破洞外圍挖掉一圈寬度等於破洞厚度的可見像素，連同破洞一起補，計算該圈與真值的平均誤差（0～1） |
| `contour_hidden` | 被遮住的輪廓比例 | 部件範圍的輪廓線落在被遮擋區的比例。這部分形狀是 Agent 猜的，補不出來 |

另記錄 `occluders`：蓋住它的部件，供自我修正使用。補上的像素另存為 `repair_masks/<部件>.png`。

判定規則：

- `hidden_ratio > 35%` → `needs_manual`（保留原規則作為參考上限）。
- 其餘：`holdout_error ≤ E` 且 `contour_hidden ≤ C` → `auto_repaired`（可靠）；否則 `auto_repaired` 但標記 `repair_reliable: false`。
- 不可靠的部件，若在 refine 階段被量到動畫中露出超過門檻，改為 `needs_manual`。不露出的不影響畫面，維持草稿。

### 3. 動畫品質檢查（`quality.py`）

重用 `preview.py` 的骨架求值：抽出 `slot_transforms()`，讓預覽與品質檢查使用同一套矩陣。

以 10 fps、最長邊約 480px，逐格算出每個 slot 變換後的 alpha 與補圖遮罩，再計算：

| 檢查 | 量測 | 歸因到 |
|---|---|---|
| 透明破洞 | 角色內部（不連到畫面邊界）的透明區域，比初始姿勢多出的面積 | 離破洞最近的關節所屬骨頭 |
| 關節縫隙 | 子骨頭關節周圍小圓內的不透明比例，比初始姿勢下降的幅度 | 該子骨頭 |
| 接觸分離／穿插 | `attach` 宣告的兩個部件重疊像素數 ÷ 初始姿勢的重疊像素數，超出 [下限, 上限] | 兩個部件 |
| 補圖露出 | 最上層像素屬於某部件補圖區的像素數 ÷ 該部件像素數 | 該部件，以及蓋住它的部件 |

圖層順序：動畫不改 draw order，所以順序錯誤只可能出在初始姿勢，由既有的 `setup_pose`（與原圖比對）負責。

輸出：

- `quality/quality_report.json`：每一輪、每一類的最大值、所在影格、歸因。
- `quality/<動畫>_<時間>_<類別>.png`：異常影格，紅色標出問題區域，給 Agent 自我檢查。

### 4. 接觸約束 `attach`

`parts.json` 的部件可寫 `"attach": "guitar"` 或清單。這只是品質條件，不是 Spine 約束。違反時由自我修正降低相關骨頭的幅度。

不用 Spine IK 的原因：Essential 版不支援，而且模板動畫是逐骨頭的關鍵影格，降低幅度就能保住接觸，又能在 Spine 內編輯。

### 5. 自我修正迴圈（`c2s refine`）

```
assess → 有可修正的異常？ → 依歸因把相關骨頭的 tuning ×0.5 → 重新 animate＋export → assess
                └─ 沒有 → 結束
最多 3 次修正；動作幅度最低降到原本的 1/8
```

- 修正量存在 `tuning.json`（工作目錄內）。流程是確定性的，刪除 output 重跑會得到同樣結果。
- 修正後仍露出的不可靠補圖 → 改為 `needs_manual`，並重寫 `missing_parts.json`、`repair_tasks.md`。
- 其餘仍存在的異常 → 驗證報告的 `animation_quality` 為 BLOCKED（需人工在 Spine 調整），保留異常影格。
- 每輪的量測值與調整內容都寫進 `quality_report.json`。

### 6. 各階段品質條件

| 階段 | 條件 | 失敗時 |
|---|---|---|
| analyze | parts.json 合法 | 結束碼 2，逐條錯誤 |
| prepare | `recompose_mae ≤ 0.02`；列出未分配區塊並指出最近的部件 | Agent 修改 parts.json |
| rig／export | `setup_pose ≤ 0.02` | FAIL |
| animate | 品質檢查 | refine 自動修正 → BLOCKED／needs_manual |

### 7. 門檻校準

門檻先用合成角色與兩組真實角色的實測分布決定，數值與依據寫進 `docs/DECISIONS.md`。合成測試案例刻意製造破洞、分離與露出，確認門檻能抓到。

### 8. 設計審查後的修正（2026-11-23，獨立子代理）

- **接觸在產生動畫時就保證**，不只是事後檢查。
  - rig 計算每個 `attach` 組合在初始姿勢的接觸點（兩者 alpha 膨脹 3px 後的重疊重心）與重疊面積；重疊太小就要求修正 parts.json（結束碼 2）。
  - animate 對組合中的每根骨頭，限制幅度讓「模板最大轉角 × 關節到接觸點的距離 ≤ 容許位移」。這個值是封閉解，不需要算圖。
  - 迴圈只處理剩下的問題。
- **反事實歸因**：在異常最嚴重的影格，逐一凍結每根有動畫的骨頭（hip 除外，它讓全身一起移動，不會造成相對縫隙）重算該指標，降低「凍結後改善最多」的那根。
  - 修正若沒有改善總異常量，就還原並停止。
  - 平手時依名稱排序，保持確定性。
- **tuning 每次 refine 從 1 開始**，以動畫名稱分開記錄（修 happy 不影響 idle）。1/8 的下限即 0.5³，不另外設定。
- **過期狀態**：animate 與 export 會刪除舊的 `quality_report.json`。
- **量測修正**：
  - holdout 的圈限縮在可見區內縮 2px，寬度不超過部件短邊的 1/4；可用來源太少時視為不可靠。
  - contour 只計算確實落在被遮擋區內 4px 以上的輪廓（2px 會把部件之間刻意重疊幾個像素的接縫算進去，合成角色實測誤判）。
  - 破洞改為「形態學閉運算後的內部透明面積」，與初始姿勢比較面積。
  - 關節縫隙只看子部件與父部件兩層的 alpha。
  - attach 重疊先膨脹再比，取消上限：多重疊不是 2D 瑕疵；2D 的「穿插」就是圖層順序錯誤，已由 `setup_pose` 檢查。
  - 補圖露出以和顏色相同的合成公式計算，並扣除初始姿勢的值。
- **效能**：算圖時快取圖片；refine 用記憶體中的骨架檢查，結束時才 export 一次。
- **人工修補圖**：覆蓋既有的修補圖前先備份成 `.bak`。parts.json 來源比正規化複本新時，prepare 要求重新 analyze。

## Risks / Trade-offs

- [降低幅度讓動畫變得不活潑] → 最低 1/8；仍不通過就標 BLOCKED 交給人，不無限降低。
- [歸因不精準，降錯骨頭] → 每輪記錄量測值變化；若修正沒有改善，下一輪不再重複同一個修正。
- [10 fps 抽樣漏掉瞬間異常] → 關鍵影格本身一定會被抽到（時間點都是 0.1 的倍數）。
- [留出驗證只能近似真正破洞內部的難度] → 只用來判定「可不可靠」，再配合實際露出量才降級為 `needs_manual`。

## Migration

- 主要角色的 `parts.json` 已在 `examples/real/`。
- 舊工作目錄內若有 `overrides/`，需要人工搬到 `<圖名>.overrides/`。目前沒有任何人工修補圖，不需搬移。
