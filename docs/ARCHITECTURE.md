# 架構

完整設計與決策理由見 `openspec/changes/character-to-spine-mvp/design.md`。這份是摘要。

## 分工

```
Agent（Skill）          看圖 → 寫 parts.json → 檢視 layer_preview / 預覽 GIF → 修正
                                     │
                                     ▼
Python Core（c2s）  analyze → prepare → rig → animate → export → validate → preview
                                     │
                                     ▼
Spine CLI（完整版）            JSON → .spine → 匯出回 JSON 比對
```

語意判斷（哪裡是頭、手）只發生在 Agent 層；Python 只處理資料，可以獨立執行。Claude Code 與 Codex 使用同一份 Skill。

## 模組

| 檔案 | 職責 |
|---|---|
| `cli.py` | 指令解析、結束碼（0 完成／1 失敗／2 需補資料）、錯誤紀錄 `c2s_error.log` |
| `pipeline.py` | 工作目錄解析、`run` 串接全部步驟 |
| `analyzer.py` | 讀圖、去背、座標格線圖、`parts.json` 檢查 |
| `image_processor.py` | 切圖、遮擋分級修補、單一部件重做與替換、修補任務、檢查圖 |
| `providers/` | 修補函式介面 `repair(rgb, unknown) -> rgb`，目前只有 OpenCV 實作 |
| `rig_builder.py` | preset、由 metadata 推算骨頭與附件 |
| `animation_builder.py` | Idle／Happy 模板（依 role 查表、乘上 motion） |
| `spine_exporter.py` | Spine JSON 組裝、Spine CLI 匯入與往返驗證 |
| `preview.py` | 骨架求值器：驗證用的初始姿勢算圖、Python Simulation Preview |
| `validator.py` | 檢查實際輸出，產生 `validation_report.json` |

## 工作目錄

每個角色一個目錄，每一步讀前一步的檔案、寫自己的檔案，可以從任何一步接續：

`source_rgba.png`、`grid_overlay.png`、`analysis.json`、`parts.json` → `layers/`、`metadata.json`、`missing_parts.json`、`repair_tasks.md`、`layer_preview.png`、`overrides/` → `rig.json` → `animations.json` → `spine/character.json`、`spine/images/`、`spine/character.spine`（完整版）、`export_report.json` → `validation_report.json` → `preview/*_python_simulation_preview.gif`
