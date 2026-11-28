# Changelog

## 1.2.0（2026-11-27）— Codex-first / Quality First

### 新增
- **生成式補圖**：`c2s prepare --generated <部件>=<PNG> --prompt "..."`。Codex 內建 `image_gen` 生成，Python 對齊、只取被遮住的像素、原圖看得見的像素不變，並判定可見區誤差、接縫、遮擋者複製、覆蓋率；連續 3 次未通過 → needs_manual（D-60）。
- `c2s consent <圖片>`：記錄使用者對雲端處理的明確許可；沒有許可時拒絕匯入雲端生成圖。
- `prepare` 為需要補圖的部件輸出 `gen_inputs/<部件>.png`（被遮區塗洋紅色），直接交給 image_gen 編輯。
- 來源紀錄 `<圖名>.overrides/provenance.json`：原圖、部件、prompt、工具、每次量測與判定、許可；未通過的融合結果也保留供人工判斷。
- parts.json 選填 `motion_overrides`：自然語言「更活潑」「頭髮多擺」轉成倍率，接觸約束仍優先。
- 品質檢查 `occluded`：舉起的手被頭髮、帽子蓋住（K-39），不觸發縮幅。
- Skill：Codex 用法（`$character-to-spine`、專案 `.agents/skills/`）、生成式補圖流程、一句話修改、`references/generative-repair.md`。
- 工具：`scripts/video_motion.py`（參考影片動作分析）、`scripts/repair_experiment.py`、`scripts/rejudge.py`、`scripts/v12_compare.py`。

### 變更
- Idle／Happy 模板依四支參考影片重寫（D-61）：Idle 1.3 秒、頭部起伏約 2.4%；Happy 蹲→起跳→落地緩衝→小彈跳，單手舉到水平以上 45° 左右交替。
- 曲線切線改單調插值，循環接縫與穿越點保留速度；預覽解真正的 bezier（D-63）。
- 蹲下、落地時腳不沉進地面（v1.1 下沉 4% 角色高度 → 0）。
- 非必要部件預設樞軸改在與父部件相接處。
- 自動縮幅下限 ×0.5 套用到所有異常（D-62，取代 D-53）。

### 未變
- OpenCV 補圖、`--replace` 人工匯回、Claude Code 用法與 v1.1 相同；沒有 image_gen 時流程與 v1.1 一致。

## 1.1.0（2026-11-27）
- 特效收進 `fx` 圖層、邊緣細節自動併入部件（D-51）；Happy 舉手依初始姿勢（D-52）；露出縮幅下限（D-53）；回報語言提醒。

## 1.0.0（2026-11-24）
- 第一個可安裝的 Character-to-Spine Skill：分析、拆圖、OpenCV 補圖、骨架、Idle／Happy、逐格品質檢查、Spine JSON、Python 模擬預覽。
