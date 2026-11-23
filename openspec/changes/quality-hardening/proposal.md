## Why

第一版的輸出可以通過結構驗證，但有四個缺口：

- 正式的 `parts.json` 與人工修補圖放在可刪除的 `output/` 裡。
- 補圖是否可靠只看被遮擋面積。
- 動畫過程中是否露出破洞、補圖或道具分離，只靠人工看 GIF。
- 動作幅度要人工反覆調整。

這個 change 把這些都變成可量測、可自動重試的品質條件。

## What Changes

- 永久素材（圖片、`parts.json`、遮罩、人工修補圖）一律放在圖片旁邊（如 `examples/real/`）。`output/` 只放可重建的產物，刪除後重跑即可完整重建。
- 補圖可靠度改為三個實測值：被遮擋面積（保留 35% 門檻）、留出驗證誤差（挖掉一圈看得見的像素再補回、和真值比較）、被遮住的輪廓比例。再加上動畫中補圖實際露出的面積。
- 新增動畫品質檢查：逐格模擬，檢查新出現的透明破洞、關節縫隙、指定接觸的部件分離或過度穿插、補圖區域露出。異常影格輸出成圖片。
- `parts.json` 新增 `attach`，宣告兩個部件必須保持接觸（例如手與吉他）。
- 新增 `c2s refine` 自我修正：檢查失敗時，依原因降低相關骨頭的動作幅度後重新產生動畫，最多三輪。仍不通過的部件標為 `needs_manual`，其餘異常為 BLOCKED，並保留證據影格。
- `c2s run` 在 export 之後自動執行 refine；驗證報告新增 `animation_quality` 檢查。

## Capabilities

### New Capabilities

- `asset-persistence`：永久素材的位置與 output 可重建性。
- `repair-risk`：補圖可靠度的量測與判定。
- `animation-quality`：動畫逐格品質檢查與異常影格。
- `motion-constraints`：部件接觸約束（`attach`）。
- `self-correction`：品質失敗時的自動修正迴圈。

### Modified Capabilities

（無。基礎規格仍在 `character-to-spine-mvp` change 內、尚未封存；這裡以新 capability 補充，不修改既有 requirement。）

## Impact

- 程式：
  - `analyzer.py`：parts 來源優先順序。
  - `image_processor.py`：修補圖位置、可靠度量測、補圖遮罩。
  - `preview.py`：抽出逐 slot 變換供共用。
  - 新增 `quality.py`。
  - `pipeline.py`、`cli.py`：新增 refine。
  - `validator.py`：新增檢查項目。
  - `animation_builder.py`：讀取 tuning。
- 資料：`examples/real/*.parts.json` 加上 `attach`；開發用暫存腳本移出 `output/`。
- 文件：Skill 說明、README、`docs/`。
- 相依套件：無新增。
