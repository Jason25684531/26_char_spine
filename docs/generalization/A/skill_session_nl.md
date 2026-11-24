# A Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_a.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（5 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：1 次
- 工具呼叫次數：{'PowerShell': 7, 'Read': 7, 'Skill': 1, 'Write': 2}

## c2s 指令

- `ls; ls .venv\Scripts\c2s.exe; .venv\Scripts\c2s.exe analyze gen_a.png; "exit=$LASTEXITCODE"`
- `(Get-Command c2s -ErrorAction SilentlyContinue).Source; Get-ChildItem -Recurse -Force .claude | Select-Object -ExpandProperty FullName; Get-ChildItem .. -Force | Select-Object -ExpandProperty FullName`
- `c2s analyze gen_a.png; "exit=$LASTEXITCODE"; Get-ChildItem -Recurse output | Select-Object -ExpandProperty FullName`
- `c2s run gen_a.png --motion happy; "exit=$LASTEXITCODE"`
- `c2s run gen_a.png --motion happy | ConvertFrom-Json | ForEach-Object { $_.steps.prepare | ConvertTo-Json -Compress; $_.steps.refine | ConvertTo-Json -Compress -Depth 5; $_.steps.validate.checks | ForEach-Object { "$($_.check): $($_.status) - $($_.detail)" } }; "exit=$LASTEXITCODE"`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "$s='D:\\01_Project\\26_char_spine\\scripts\\visual_report.py'; if (Test-Path $s) { & D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe $s output\\gen_a; \"exit=$LASTEXITCODE\"; ls

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_a.png"}`
2. PowerShell：`{"command": "ls; ls .venv\\Scripts\\c2s.exe; .venv\\Scripts\\c2s.exe analyze gen_a.png; \"exit=$LASTEXITCODE\"", "description": "List files and run c2s analyze"}`
3. PowerShell：`{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Get-ChildItem -Recurse -Force .claude | Select-Object -ExpandProperty FullName; Get-ChildItem .. -Force | Select-Object -ExpandProperty FullName", "description": "Locate c2s and skill files"}`
4. PowerShell：`{"command": "c2s analyze gen_a.png; \"exit=$LASTEXITCODE\"; Get-ChildItem -Recurse output | Select-Object -ExpandProperty FullName", "description": "Run c2s analyze on the image"}`
5. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\output\\gen_a\\grid_overlay.png"}`
6. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\output\\gen_a\\parts.template.json"}`
7. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\gen_a.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"braid_l\", \"polygon\": [[250,505],[352,505],[348,600],[315,690],[300,758],[252,758],[258,680],`
8. PowerShell：`{"command": "c2s run gen_a.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
9. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\output\\gen_a\\layer_preview.png"}`
10. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\output\\gen_a\\missing_parts.json"}`
11. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\gen_a.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"braid_l\", \"polygon\": [[250,505],[352,505],[390,548],[390,580],[348,600],[315,690],[300,758],`
12. PowerShell：`{"command": "c2s run gen_a.png --motion happy | ConvertFrom-Json | ForEach-Object { $_.steps.prepare | ConvertTo-Json -Compress; $_.steps.refine | ConvertTo-Json -Compress -Depth 5; $_.steps.validate.checks | ForEach-Object { \"$($_.check): $($_.status) - $($_.detail)\" } }; \"exit=$LASTEXITCODE\"",`
13. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\output\\gen_a\\layer_preview.png"}`
14. PowerShell：`{"command": "python scripts/visual_report.py output/gen_a; \"exit=$LASTEXITCODE\"; ls output/gen_a/report, output/gen_a/layers -Name", "description": "Generate visual repair report", "timeout": 300000}`
15. PowerShell：`{"command": "$s='D:\\01_Project\\26_char_spine\\scripts\\visual_report.py'; if (Test-Path $s) { & D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe $s output\\gen_a; \"exit=$LASTEXITCODE\"; ls output\\gen_a\\report -Name } else { 'not found' }", "description": "Run the visual report script f`
16. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\output\\gen_a\\report\\repair_priority.md"}`
17. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\A\\sandbox_nl\\output\\gen_a\\report\\visual_check.png"}`

## 最後回覆（原文）

`gen_a.png` 已經做成骨架與 Idle、Happy 兩段動畫，但還不能算完成：有 4 個部件要人工補畫，而且這台機器上的 Spine 是試用版，產生不了 `.spine` 專案檔。

切圖重組和原圖的差異是 0.0015，沒有漏掉任何像素。我把角色拆成 9 個部件：頭（含帽子）、身體、裙子、左右手、左右腳、左右辮子。第一次跑時 `arm_l` 整隻被身體蓋住，我把它的前後順序往前調，也擴大了幾個邊緣漏畫的區域，第二次就正常了。

### 驗證報告（`validation_report.json`）
| 項目 | 狀態 |
|---|---|
| bones | PASS |
| slots | PASS |
| image_references | PASS |
| animations | PASS（idle 2.0 秒、happy 2.4 秒） |
| setup_pose | PASS（和原圖差異 0.0017） |
| animation_quality | PASS（第 3 輪，已自動降低手、身體、頭、腳的擺動幅度） |
| manual_repairs | **BLOCKED**：等待人工補畫 |
| spine_import | **BLOCKED**：偵測到 Spine 試用版，它不能儲存專案也不能匯出 |
| spine_roundtrip | NOT_TESTED（沒有 `.spine` 檔可以測） |
| spine_editable | NOT_TESTED（要有人在 Spine Editor 裡實際開啟並修改才算數） |

### 待人工補畫（依動畫中實際露出量排序）
1. **skirt**（高）：被雙手擋住的地方，Happy 在 0.5 秒時露出 9.3%。
2. **leg_l**（高）：被右腳和裙子擋住的地方，露出 9.1%。
3. **body**（高）：大約一半被擋住，自動補圖不可靠，露出 2.7%。
4. **leg_r**（高）：裙子底下的地方，露出 2.6%。
5. braid_l、braid_r（中）：自動補圖露出 1.9% 和 1.3%，在門檻內，看過沒問題可以先保留。

目前這些區域只是自動填的草稿，不算修好。每個部件的三格對照圖在 `output/gen_a/report/repair_priority.md`。補好後執行 `c2s prepare --replace <部件>=<修好的.png>`，再跑 `c2s run gen_a.png`。如果暫時不想補，也可以在 `gen_a.parts.json` 把擋住它的部件 `motion` 調低。

### 產出檔案
- 部件設定：`gen_a.parts.json`，放在原圖旁邊，原圖沒有改動。
- 動畫預覽：`output/gen_a/preview/happy_python_simulation_preview.gif`、`idle_python_simulation_preview.gif`。這是 Python Simulation Preview，不是 Spine 算圖。
- 關鍵影格總覽：`output/gen_a/report/visual_check.png`。

技能說明裡的 `scripts/visual_report.py` 不在這個資料夾，我改跑 `D:\01_Project\26_char_spine\scripts\` 底下那一份。