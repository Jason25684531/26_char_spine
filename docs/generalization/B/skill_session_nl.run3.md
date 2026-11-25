# B Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_b.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（4 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：2 次
- 工具呼叫次數：{'Glob': 2, 'PowerShell': 5, 'Read': 6, 'Skill': 1, 'Write': 2}

## c2s 指令

- `(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path .venv; Test-Path D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe`
- `c2s analyze gen_b.png; "EXIT=$LASTEXITCODE"; Get-ChildItem -Recurse output | Select-Object FullName`
- `c2s run gen_b.png --motion happy; "EXIT=$LASTEXITCODE"`
- `c2s run gen_b.png --motion happy | ConvertFrom-Json | ForEach-Object { "status=$($_.status) unassigned=$($_.steps.prepare.unassigned_ratio) mae=$($_.steps.prepare.recompose_mae) needs_manual=$($_.steps.prepare.needs_manual -join ',')"; $_.steps.refine | ConvertTo-Json -Depth 5 -Compress; $_.steps.validate.checks | ForEach-Object { "$($_.check): $($_.status) — $($_.detail)" } }; "EXIT=$LASTEXITCODE"`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path .venv; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate c2s executable"}
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_b; \"EXIT=$LASTEXITCODE\"; Get-ChildItem output\\gen_b\\re

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_b.png"}`
2. Glob：`{"pattern": "*"}`
3. PowerShell：`{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path .venv; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate c2s executable"}`
4. PowerShell：`{"command": "c2s analyze gen_b.png; \"EXIT=$LASTEXITCODE\"; Get-ChildItem -Recurse output | Select-Object FullName", "description": "Run c2s analyze on the image"}`
5. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\grid_overlay.png"}`
6. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\gen_b.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"absent\": [\"leg_l\", \"leg_r\"],\n  \"parts\": [\n    {\"name\": \"body\", \"polygon\": [[490,365],[595,365],[605,405],[65`
7. PowerShell：`{"command": "c2s run gen_b.png --motion happy; \"EXIT=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
8. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\layer_preview.png"}`
9. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\missing_parts.json"}`
10. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\gen_b.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"absent\": [\"leg_l\", \"leg_r\"],\n  \"parts\": [\n    {\"name\": \"body\", \"polygon\": [[485,358],[600,358],[642,392],[70`
11. PowerShell：`{"command": "c2s run gen_b.png --motion happy | ConvertFrom-Json | ForEach-Object { \"status=$($_.status) unassigned=$($_.steps.prepare.unassigned_ratio) mae=$($_.steps.prepare.recompose_mae) needs_manual=$($_.steps.prepare.needs_manual -join ',')\"; $_.steps.refine | ConvertTo-Json -Depth 5 -Compre`
12. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\layer_preview.png"}`
13. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_b; \"EXIT=$LASTEXITCODE\"; Get-ChildItem output\\gen_b\\report, output\\gen_b\\*.json | Select-Object Name", "description": "Generate visual check report", "t`
14. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\report\\repair_priority.md"}`
15. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\report\\visual_check.png"}`
16. Glob：`{"pattern": "output/gen_b/**/*.{json,atlas}"}`

## 最後回覆（原文）

我已經把 gen_b.png 做成 Spine JSON，裡面有骨架和 idle、happy 兩段動畫。不過整體驗證是 **BLOCKED**：這台電腦只有 Spine 試用版，無法產生 `.spine` 專案檔；另外角色的兩腳被長裙完全蓋住，沒有骨頭也沒有動畫。

- **Spine 檔**：`output\gen_b\spine\character.json`
- **部件定義**：`gen_b.parts.json`，放在圖片旁邊
- **預覽**：`output\gen_b\preview\happy_python_simulation_preview.gif`。這是 Python Simulation Preview，不是 Spine 算圖。

## 拆法
部件有頭、身體、兩隻手、左右兩束雙馬尾和裙子。裙子設成 `role: skirt`。拉著裙擺的左手設了 `attach: "skirt"`，在預覽的關鍵影格裡，手和裙子一直保持接觸，沒有分開。

第一輪有 3.1% 的像素沒分到任何部件，主要是頭髮內側、肩膀、左前臂下緣和裙擺外緣。我擴大了這幾個部件的範圍後重跑，降到 0.2%。重組結果和原圖的差異是 0.001。

## validation_report.json 各項結果
| 項目 | 狀態 |
|---|---|
| bones | PASS（9 根骨頭） |
| slots | PASS |
| image_references | PASS |
| animations | PASS（idle 2.0 秒、happy 2.4 秒） |
| setup_pose | PASS（和原圖差異 0.0020） |
| manual_repairs | PASS |
| absent_parts | **BLOCKED**：`leg_l`、`leg_r` 被長裙完全蓋住，我在 parts.json 宣告為看不到，所以沒建骨頭也沒有動畫 |
| animation_quality | PASS（品質修正跑了 4 輪，採用第 3 輪，沒有未解決的問題） |
| spine_import | **BLOCKED**：只有試用版，無法產生 `.spine` |
| spine_roundtrip | NOT_TESTED：沒有 `.spine`，無法做往返驗證 |
| spine_editable | NOT_TESTED：要有人在 Spine Editor 裡開啟專案、改關鍵影格才能確認 |

為了讓動畫通過品質檢查，系統自動降低了幾個部件的動作幅度：happy 裡頭和裙子降到 0.5，右手和兩束頭髮降到 0.25。

## 待人工處理
沒有部件被列為 `needs_manual`。以下三個部件被擋住的地方是系統自動補的草稿，動畫中會露出一點（都在門檻內）。依露出量排序，都是中優先：
1. `body`：最多露出 1.89%。被擋住的輪廓佔 58%，要照原圖重畫。
2. `hair_l`：最多露出 1.47%。
3. `hair_r`：最多露出 1.39%。

詳細說明和對照圖在 `output\gen_b\report\repair_priority.md`。修好的圖用 `c2s prepare --replace <部件>=<修好的.png>` 匯回，再執行 `c2s run gen_b.png`。

如果要讓腳也能動，可以補畫兩腳；如果要產生 `.spine` 專案檔，需要完整版 Spine。