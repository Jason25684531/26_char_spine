## Context

2026-11-24 審查結果（讀程式與實際輸出，不依賴先前報告）：

| 項目 | 實況 |
|---|---|
| 分支 | `feat/character-to-spine-mvp`，HEAD `00179b0`，未提交：未追蹤的 `ref/`（四支影片與 `video.rar`） |
| 測試 | `.venv\Scripts\python.exe -m pytest --collect-only` 收到 114 個 |
| CLI | `c2s` 有 analyze／prepare／rig／animate／export／refine／validate／preview／run |
| Skill | 正本 `skills/character-to-spine/SKILL.md`，`.claude/skills/character-to-spine/` 有複本，本 session 的技能清單列得到 |
| preset | 只有 `humanoid-chibi`；`rig_builder.build_rig` 缺任一必要部件就 `NeedsInput` |
| pivot 預設 | `PRESETS[...]["anchors"]` 是圖層外框的固定比例，假設手臂下垂、腿在正下方 |
| 語意分析 | 完全由 Agent 看 `grid_overlay.png` 寫多邊形；Python 不做部件辨識 |
| 量測 | `motion_metrics.py` 只量 attach 接觸點相對 `body` 的位移 |
| 真實素材 | `examples/real/` 四張圖都是同一個角色；`ref/` 只有影片 |
| OpenSpec | 三個進行中的 change，`openspec/specs/` 為空 |
| K-19 | 转场2 多餘的接觸限制碰巧壓住身體草稿露出，刻意保留 |

限制：不用付費影像 API、不裝本地生成模型、使用者圖片不外傳、不改既有兩組角色的結果、不合併 `main`。

## Goals / Non-Goals

**Goals:**

- 用五張未參與開發的角色圖，量出系統目前的泛化能力，並留下可重跑的證據。
- 修掉跨角色共通的失敗，不讓既有兩組角色退步。
- 超出能力的圖片得到明確的 UNSUPPORTED 或 PARTIAL，而不是看似成功的錯誤結果。
- 降低人工介入：使用者只需要在「提供真實素材」與「補畫 needs_manual 部件」兩處出手。

**Non-Goals:**

- 讓五張圖全部 PASS。
- 新增非人形骨架、IK、網格變形。
- Skill 重新包裝、references 擴充、Web UI、MCP。
- 用 Python 自動辨識部件（語意判斷仍由 Agent 負責）。

## Decisions

### D1 素材來源：三層備案

| 層 | 來源 | 判定上限 |
|---|---|---|
| 首選 | 使用者放進 `examples/generalization/inbox/` 的自有或已授權角色圖 | 可計入真實角色驗收 |
| 備案一 | 公開授權（CC0 優先，其次 CC-BY）的角色圖，下載後記錄網址、授權、作者、SHA-256 | 可計入真實角色驗收，報告標明來源 |
| 備案二 | 程式生成的合成角色（擴充 `tests/synthetic.py`） | 只能標為 SYNTHETIC 輔助；對應的真實素材格標 BLOCKED |

執行順序：先看 inbox，缺的類型再找公開素材，仍缺才用合成角色。公開素材能否湊齊五種類型是未驗證的猜測，所以第一個任務就是實際去找並記錄結果。

排除清單寫進 manifest：`人.png`、`转场2.png`、`人物 拷贝.png`、`预中奖.png` 以及它們的任何修改版；`ref/` 的影片截圖在使用者確認角色不同之前也不採用。

不選「全部用合成角色」：合成角色是純色塊，測不到真實圖的邊緣、陰影與遮擋，結論不能外推。

### D2 執行前凍結：`examples/generalization/manifest.json`

每個案例一筆：

```json
{"id": "A", "type": "front-chibi", "file": "A/char.png", "sha256": "...",
 "origin": "user|public|synthetic", "source_url": "...", "license": "...",
 "features": {"view": "front", "props": [], "occlusion": "low", "body": "humanoid"},
 "expected_scope": "supported|partial|unsupported",
 "criteria": {...}}
```

`features` 與 `criteria` 在第一次對該圖執行 `c2s` 之前寫好並提交，提交雜湊就是「沒有事後降低門檻」的證據。之後若要改門檻，必須新增一筆 `criteria_changes`（原值、新值、理由），報告同時列出兩個版本的判定。

預先登記的共通門檻（沿用既有校準值，不為新圖另訂）：

| 項目 | 門檻 | 來源 |
|---|---|---|
| 重組與原圖差異 | `setup_pose` MAE ≤ 0.02 | `validator.SETUP_POSE_MAX_MAE` |
| 未分配前景像素 | ≤ 1% 前景面積 | 新增，本次登記 |
| 逐格品質 | `quality.THRESHOLDS`（hole 0.003、gap 0.1、attach 0.6、intrude 0.02、exposure 0.02） | D-31、D-32 |
| 循環 | 首尾影格所有骨頭的值相同 | 新增 |
| 未持物手臂的動作量 | happy 中肢端相對身體的最大位移 ≥ 角色高度的 2% | 新增，本次登記 |
| 只剩整體跳動 | 所有肢體相對位移都 < 0.5% 高度即判定 | 新增 |
| 過度縮小 | 任一手臂的自我修正係數 < 0.25 即標記，並說明是素材限制或演算法限制 | 新增 |

持物手臂（有 attach）只報告數值，不設下限：既有角色實測 5.1px（K-18），設下限等於預先判既有角色失敗。

### D3 `parts.json` 來源驗證與 Skill 實測（同一次執行）

每張新圖開一個全新的 Claude Code headless session：

```
claude -p "幫我把這張角色圖做成 Spine 動畫：<圖片路徑>" --output-format stream-json --verbose
```

工作目錄是本專案，所以 session 看得到 `.claude/skills/character-to-spine/`。提示不提 `SKILL.md`、`c2s`、`parts.json`。案例 A 另跑一次 `/character-to-spine <圖片路徑>`。

證據是 stream-json 的工具呼叫：

- Skill 觸發：有 `Skill` 工具呼叫，參數 `skill` 為 `character-to-spine`。只用 Read 讀 `SKILL.md` 不算。
- CLI 執行：之後有含 `c2s` 的 Bash／PowerShell 呼叫。
- 來源：沒有讀取 `examples/real/`、`examples/synthetic/`、`tests/` 或其他案例的 `parts.json`。
- 失敗回報：最後一則回覆的內容與 `validation_report.json` 一致。

程式查核另外比對多邊形雷同（逐點相同，或平移縮放後殘差低於 3px）與座標是否落在前景外框內。

這仍是同一家模型，報告寫成「同模型的獨立 Claude Code session」。不選 Agent 工具的子代理：子代理沒有自然語言觸發 Skill 的路徑，測不到使用者實際的入口。

### D3b 視覺品質驗收

`scripts/generalization.py sheet <id>` 為每個案例產生一張 `visual_sheet.png`：原圖、圖層重組、骨架圖（骨頭線段、pivot 圓點、父子連線疊在半透明原圖上）、Idle 三格與 Happy 四格關鍵影格。算圖沿用 `preview.render_setup_pose` 與 `quality._frame` 的同一套算圖器，不另寫。

目視紀錄放在 `examples/generalization/visual_review.json`，與自動量測分開：

```json
{"A": {"reviewer": "agent", "layers": ["OK|ISSUE|UNKNOWN", "依據"],
       "joints": [...], "motion": [...], "occlusion": [...]}}
```

`reviewer` 只有 `agent` 與 `user` 兩種值。使用者尚未看過的案例，`user` 欄位整個缺席，報告顯示 NOT_TESTED。判定規則：任一項 ISSUE 時不得 PASS；沒有目視紀錄時上限 NOT_TESTED。

### D4 執行器：一支腳本、一份結果

`scripts/generalization.py`，子命令 `run`、`provenance`、`snapshot`、`report`。

資料形狀（`output/generalization/results.json`，每個案例一筆）：

```json
{"id": "A", "label": "baseline|round1|...", "exit_code": 0,
 "validator": {"layers": "PASS", "...": "..."},
 "recompose": {"mae": 0.004, "unassigned_ratio": 0.002},
 "quality": {"unresolved": [], "tuning": {"arm_l": 0.6}},
 "motion": {"arm_l": {"travel_ratio": 0.031}, "bounce_only": false},
 "exposure": {"body": 0.012},
 "manual": ["body"], "grade": "PARTIAL", "grade_reasons": ["..."]}
```

判定用一張表，不散落在條件式裡：

| 條件（由上往下，第一個符合者） | 等級 |
|---|---|
| manifest 沒有圖片，或缺 Spine 授權才能驗的項目 | BLOCKED（只針對該項） |
| 尚未執行 | NOT_TESTED |
| `parts.json` 宣告超出範圍，且 manifest 的 `expected_scope` 是 unsupported | UNSUPPORTED |
| 結束碼 1，或驗證器有 FAIL，或任一登記門檻未達且不是素材限制 | FAIL |
| 有 `needs_manual` 部件，或有標記為素材限制的未解問題 | PARTIAL |
| 其餘 | PASS |

「宣告超出範圍但 manifest 預期是 supported」判 FAIL：這代表分析或系統在本應支援的圖上放棄。驗證器原有的 PASS／FAIL／BLOCKED／NOT_TESTED 原樣放在 `validator` 欄位，與六級判定並列。

`snapshot <label>` 把 `results.json`、每張圖的 `layer_preview.png`、關鍵影格與異常影格複製到 `output/generalization/_snapshots/<label>/`，前後比較就是兩個 label 的差異表。既有兩組角色（`人`、`转场2`）也在執行清單裡，每次都一起跑。

`output/` 被 `.gitignore` 排除，所以報告引用的圖與數據複製到 `docs/generalization/`。使用者提供的圖片預設不進版控，只留雜湊；公開授權素材連同授權檔進版控。

### D5 動作量測擴充

`motion_metrics.py` 目前只走 `rig["contacts"]`。改成對每個 role 為 arm、leg、hair、skirt、prop 的骨頭取「圖層上離 pivot 最遠的點」當肢端，量它扣掉 `body` 骨頭移動後的最大位移，除以角色高度。attach 接觸點的既有量測保留，數值必須與修改前相同（回歸測試）。

### D6 範圍處理：兩個宣告，不加 preset

`parts.json` 新增兩個選填欄位：

- 頂層 `"unsupported": "<原因>"`：Agent 判斷圖片超出 MVP 範圍（非人形、多角色、嚴重透視）。`c2s analyze`／`run` 以新狀態 `unsupported` 結束，結束碼 3，`analysis.json` 與 `validation_report.json` 記錄原因，不產生骨架與動畫。
- 頂層 `"absent": ["arm_r"]`：必要部件在畫面上完全看不到（3/4 側面的遠側手）。該部件不建骨頭、不出動畫，`repair_tasks.md` 列為「可選擇補畫」，判定上限為 PARTIAL。`head`、`body` 不可列入。

語意判斷仍由 Agent 做，Python 只負責記錄與一致性檢查。

不選「新增 3/4、非人形 preset」：沒有失敗證據前不知道需要哪些骨頭；`absent` 用既有 preset 就能涵蓋最常見的缺肢情況。E 類若連 `absent` 都救不了，結論就是 UNSUPPORTED，並寫進報告第 8 節，留給下一階段。

這兩個欄位是本次唯一預先決定要做的核心修改，因為沒有它們，B、E 兩類在執行前就已知只能卡在結束碼 2，測不出任何東西。先用現況跑一次留下基準，再加欄位。

### D7 核心演算法改善：由失敗證據驅動

候選假設（依 P0、P1 排序，**沒有對應的失敗案例就不做**）：

| 代號 | 症狀 | 假設 | 最小修改 | 備案 |
|---|---|---|---|---|
| H1 | 舉手或側身的手臂繞錯點轉 | 外框比例的預設 pivot 只適用下垂手臂 | 預設 pivot 改取該部件與 parent 圖層重疊區的重心（`_contacts` 已有同樣算法） | 維持比例，SKILL.md 要求這類部件必填 pivot |
| H2 | 部件邊緣帶到相鄰部件或背景 | 目測多邊形不貼邊 | 多邊形邊界在窄帶內吸附到顏色邊緣（OpenCV GrabCut 或分水嶺，只動邊界帶） | SKILL.md 引導改用 mask，列為修補任務 |
| H3 | 未分配像素多 | 多邊形之間留縫 | 未分配的前景像素歸給最近的部件（`_unassigned_regions` 已算出最近部件） | 維持現狀，由 Agent 依 `missing_parts.json` 修正 |
| H4 | 自我修正把手臂壓到幾乎不動 | 草稿露出門檻對小面積部件過嚴，或降幅是整根骨頭一起降 | 只降造成露出的方向或時段；露出量改看絕對像素與比例的較大者 | 維持現狀並標 PARTIAL，交人工補畫（K-17、K-19 的處理方式） |
| H5 | 頭髮、裙擺、道具不跟隨或亂甩 | role／parent 預設不適合該身形 | 預設 parent 依部件與 head／body 的重疊量決定 | SKILL.md 要求明寫 parent |
| H6 | 不同身形的動作不合適 | 模板幅度以 Q 版比例校準 | 幅度依肢體長度對角色高度的比例縮放 | 留到下一階段 |

每個假設的流程固定：

1. `snapshot baseline` 保留修改前結果。
2. 寫下失敗原因與假設，加一個會失敗的測試（合成角色重現，不用測試圖的座標）。
3. 只改必要模組。
4. 跑全部案例加既有兩組角色，`snapshot roundN`。
5. 既有角色任何登記指標變差超過量測雜訊，或新案例整體等級下降，就 `git revert` 該提交。
6. 同一問題最多三輪有實質差異的嘗試，之後採用表中的備案並記錄。

禁止事項以測試守住：擴充既有的 `test_no_character_specific_code`，把 `examples/generalization/` 的檔名與 manifest id 加入禁用字串；座標寫死仍需人工審查（K-11 的限制不變）。

### D8 技術審查

改核心之前，把本設計與 `results.json` 的基準交給一個獨立子代理做對抗式審查（重點：判定表是否有漏洞、門檻是否能事後操弄、D6 是否會讓本應支援的圖被輕易宣告 UNSUPPORTED）。完成後再由另一個子代理做最終 QA，重跑 `scripts/generalization.py run` 比對報告數字。兩者都如實標為同模型子代理。

### D9 Skill：只驗證入口

D3 的 headless session 就是 Skill 實測。只有入口壞掉或 D6 的新欄位需要說明時才改 `SKILL.md`，並同步到 `.claude/`、`.codex/` 複本。

### D10 成功率的計法

| 類別 | 等級 | 計入成功率 | 計入可處理率 |
|---|---|---|---|
| 支援並完成 | PASS | 是 | 是 |
| 部分完成，需人工修補 | PARTIAL | 否 | 是 |
| 超出目前支援範圍 | UNSUPPORTED | 否 | 否 |
| 技術失敗 | FAIL | 否 | 否 |
| 缺少測試素材 | BLOCKED | 不計入分母 | 不計入分母 |

分母是實際執行的真實陌生角色。合成角色另列，不進任何比率。

## Risks / Trade-offs

- [公開素材湊不齊五類] → 缺的類型用合成角色輔助並標 BLOCKED；報告明寫真實驗收涵蓋幾張。
- [公開素材風格偏離使用者的實際專案（3D 算圖風 Q 版）] → 報告列出風格差異；使用者隨時可放圖到 inbox 重跑，執行器不需修改。
- [Agent 寫的多邊形每次不同，結果不可重現] → `parts.json` 寫出後即凍結進版控，之後的前後比較都用同一份；分析品質另外單獨評分，不與演算法修改混在一起。
- [`unsupported` 變成逃生門] → 判定表規定「預期支援卻宣告超出範圍」是 FAIL；`expected_scope` 在執行前凍結。
- [新門檻（2%、0.5%、0.25）沒有校準依據] → 先在既有兩組角色與合成角色上量一次，數值寫進 manifest 的 `criteria_basis`，在跑新圖之前定案。
- [修某張圖讓既有角色退步] → 既有兩組角色每輪必跑，退步即回退。
- [量測本身有錯] → 擴充後的量測在既有 attach 接觸點上必須與舊值一致；最終 QA 子代理獨立重算。
- [同模型審查的盲點相同] → 報告如實標示，不宣稱跨模型獨立；關鍵數字都可由腳本重算。
- [下載的素材是不可信資料] → 放在各自的資料夾，只用 Pillow 讀取，不執行其中任何內容。

## Migration Plan

全部在功能分支上以小提交進行：manifest 凍結 → 執行器 → 基準 → 每個假設一個提交 → 報告。回退單位是提交。`parts.json` 的兩個新欄位都是選填，既有檔案不需修改。

## Open Questions

1. 使用者是否有其他已授權的專案角色圖可放進 inbox？有的話優先採用，沒有就走備案一。
2. `ref/` 影片裡是否有不同角色、且允許擷取影格當測試素材？未確認前不採用。
3. 使用者提供的圖片是否要進版控？預設不進，只記雜湊。
