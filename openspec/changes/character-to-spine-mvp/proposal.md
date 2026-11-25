## Why

把一張 2D 角色圖做成 Spine 專案，目前要人工拆圖、補圖、擺骨頭、打關鍵影格，每換一個角色就重來一次。這個 change 建立一套可重複使用的工具，把其中能自動化的部分交給 Python 核心，需要看圖判斷的部分交給已登入的 Claude Code／Codex，並且如實標出仍然需要人工或正式版 Spine 的地方。

## What Changes

- 新增 Python 套件 `character_to_spine` 與 CLI `c2s`：`analyze`、`prepare`、`rig`、`animate`、`export`、`validate`、`preview`、`run`。
- 新增 `parts.json` 交換格式：由 Agent 或人工描述每個部件的範圍、前後順序、關節、父骨頭、角色（role）與動作幅度。
- 新增切圖流程：去背、依 `parts.json` 切出透明分層 PNG、小面積遮擋自動填補、大面積遮擋轉成人工修補任務、單一部件重做與替換。
- 新增人形／Q 版骨架 preset：6 個必要部件，可加頭髮、裙擺、道具等任意部件。
- 新增 Idle、Happy 動畫模板，輸出可編輯的骨架關鍵影格；幅度依角色尺寸與部件的 role／motion 設定換算。
- 新增 Spine JSON 匯出（目標 4.3，可用 `--spine-version` 切換），偵測到完整版 Spine CLI 時匯入成 `.spine` 並往返驗證；只有試用版或沒安裝時標記 BLOCKED。
- 新增輸出驗證器：檢查骨架、插槽、圖片引用、動畫結構，並用骨架資料重新算圖和圖層重組比對。狀態只有 PASS／FAIL／BLOCKED／NOT_TESTED。
- 新增 Python Simulation Preview（GIF），明確標示不是 Spine 算圖。
- 新增 Claude Code 與 Codex 共用的 Skill，兩邊都只呼叫 `c2s`。
- 新增交付打包腳本與由實際輸出產生的 PPTX 簡報。
- 已存在的程式草稿（2026-11-23 寫成、從未執行）視為未驗證初稿，本 change 的 tasks 會逐一測試並修正，不直接當成完成品。

## Capabilities

### New Capabilities

- `character-analyzer`: 讀圖、去背、`parts.json` 格式與檢查、缺少部件時的回報與接續方式。
- `image-processor`: 依 `parts.json` 切出分層 PNG 與 metadata、遮擋修補與修補任務、外部遮罩、單一部件重做與替換、切圖檢查圖。
- `auto-rigging`: 由圖層 metadata 建立骨架、插槽與附件；必要部件與額外部件的規則。
- `animation-builder`: Idle 與 Happy 動畫模板、role／motion 設定、關鍵影格格式。
- `spine-exporter`: Spine JSON 組裝、圖片輸出、Spine CLI 匯入與往返驗證、沒有完整版時的 BLOCKED 行為、Python Simulation Preview。
- `skill-cli-integration`: `c2s` 指令、工作目錄、結束碼、錯誤診斷紀錄、Claude／Codex 共用 Skill。
- `delivery-validation`: 輸出驗證器、狀態定義與證據、兩組真實角色的通用性驗收、交付打包與簡報。

### Modified Capabilities

（無，`openspec/specs/` 目前是空的。）

## Impact

- 新增程式碼：`src/character_to_spine/`、`tests/`、`scripts/`、`skills/character-to-spine/`、`.claude/skills/`、`.codex/skills/` 內的 Skill 入口。
- 相依套件：numpy、Pillow、opencv-python、pytest（都已安裝）；簡報需要新安裝 python-pptx。
- 素材：`src/` 下四張 PNG 原檔不動，複製到 `examples/real/`。原本規劃的 `src/` 同時放了圖片與 Python 套件，原始圖檔用 `.gitignore` 排除以免重複追蹤。
- 外部條件：`.spine` 的建立、往返驗證、可編輯性驗證需要完整版 Spine 授權，目前只有試用版，這三項在授權到位前維持 BLOCKED。
- 不影響任何既有規格或程式（專案原本沒有程式碼）。
