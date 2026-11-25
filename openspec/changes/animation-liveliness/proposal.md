## Why

quality-hardening 讓手不會離開吉他，代價是撥弦的手只動 4.4px（轉 2°）。原因是接觸約束用固定的 9px 容許位移限制每根骨頭的旋轉。同時，需人工的部件沒有優先順序，視覺驗收也沒有固定的產出。這個 change 讓動畫在不破圖的前提下更生動，並把素材修補與視覺驗收變成可重跑的產出。

## What Changes

- 手臂動作的爬坡實驗，每個調整都量前後，品質變差就回退。假設包括：
  - 容許位移改看道具內部空間。
  - 道具帶動抱著它的手（FK 父子關係）。
  - 撥弦節奏。
- 修補優先順序：依動畫實際露出量排序所有需人工的部件，輸出三格對照圖與修補建議。
- 視覺驗收總覽：每個角色一張圖，含關鍵影格、接觸點、拆補對照。
- Spine 匯入準備：每個角色一份匯入說明（版本、檔案、雜湊、指令）。`.spine` 驗收維持 BLOCKED。
- 交付更新：預覽、15 頁簡報、測試報告，分出已完成、半自動、人工修補、尚未驗證。

## Capabilities

### New Capabilities

- `motion-liveliness`：在品質閘門內增加抱物手臂的動作量。
- `repair-priority`：需人工部件的優先順序與對照圖。
- `visual-acceptance`：視覺驗收總覽。
- `spine-import-pack`：Spine 匯入準備。

### Modified Capabilities

（無。）

## Impact

- `animation_builder.py`、`rig_builder.py`：接觸約束、父子關係。
- 新增：`scripts/motion_metrics.py`、報告腳本。
- `scripts/package_deliverables.py`、`scripts/make_slides.py`。
- 不改核心流程與資料格式。