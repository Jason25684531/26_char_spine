# C Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_c.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（5 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：7 次
- 工具呼叫次數：{'Glob': 2, 'PowerShell': 7, 'Read': 11, 'Skill': 1, 'Write': 2}

## c2s 指令

- `Get-Command c2s -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source; Test-Path .venv\Scripts\c2s.exe; Test-Path D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe`
- `& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe analyze gen_c.png; "exit=$LASTEXITCODE"; Get-ChildItem -Recurse output | Select-Object FullName`
- `New-Item -ItemType Directory -Force $env:TEMP\c2s_view | Out-Null; & D:\01_Project\26_char_spine\.venv\Scripts\python.exe -c "from PIL import Image; im=Image.open(r'output\gen_c\grid_overlay.png'); im.crop((0,40,450,480)).resize((900,880)).save(r'$env:TEMP\c2s_view\top.png'); im.crop((0,450,500,843)).save(r'$env:TEMP\c2s_view\bottom.png')"; "$env:TEMP\c2s_view"`
- `& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_c.png --motion happy; "exit=$LASTEXITCODE"`
- `& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_c.png --motion happy | ConvertFrom-Json | ForEach-Object { $_.steps.prepare | Select-Object needs_manual,recompose_mae,unassigned_ratio | ConvertTo-Json -Compress; $_.steps.refine | ConvertTo-Json -Compress -Depth 5; $_.steps.validate.checks | ForEach-Object { "$($_.check): $($_.status) - $($_.detail)" } }; "exit=$LASTEXITCODE"`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "Get-Command c2s -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source; Test-Path .venv\\Scripts\\c2s.exe; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe",
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe analyze gen_c.png; \"exit=$LASTEXITCODE\"; Get-ChildItem -Recurse output | Select-Object FullName", "description": "Analyze the ch
- PowerShell：{"command": "New-Item -ItemType Directory -Force $env:TEMP\\c2s_view | Out-Null; & D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe -c \"from PIL import Image; im=Image.open(r'output\\gen_c\\
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_c.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 600000
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_c.png --motion happy | ConvertFrom-Json | ForEach-Object { $_.steps.prepare | Select-Object needs_manual,recompose_mae,una
- Glob：{"pattern": "**/visual_report.py", "path": "D:\\01_Project\\26_char_spine"}
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_c; \"exit=$LASTEXITCODE\"", "description": "Generate visua

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_c.png"}`
2. Glob：`{"pattern": "*"}`
3. PowerShell：`{"command": "Get-Command c2s -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source; Test-Path .venv\\Scripts\\c2s.exe; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate the c2s executable"}`
4. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe analyze gen_c.png; \"exit=$LASTEXITCODE\"; Get-ChildItem -Recurse output | Select-Object FullName", "description": "Analyze the character image"}`
5. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\grid_overlay.png"}`
6. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\parts.template.json"}`
7. PowerShell：`{"command": "New-Item -ItemType Directory -Force $env:TEMP\\c2s_view | Out-Null; & D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe -c \"from PIL import Image; im=Image.open(r'output\\gen_c\\grid_overlay.png'); im.crop((0,40,450,480)).resize((900,880)).save(r'$env:TEMP\\c2s_view\\top.png');`
8. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_view\\top.png"}`
9. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_view\\bottom.png"}`
10. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\gen_c.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"absent\": [\"leg_l\", \"leg_r\"],\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[30, 785], [450, 785], [450, 84`
11. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_c.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 600000}`
12. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\layer_preview.png"}`
13. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\quality\\round_2\\happy_t0.6_hole_character.png"}`
14. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\missing_parts.json"}`
15. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\gen_c.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"absent\": [\"leg_l\", \"leg_r\"],\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[30, 785], [450, 785], [450, 84`
16. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_c.png --motion happy | ConvertFrom-Json | ForEach-Object { $_.steps.prepare | Select-Object needs_manual,recompose_mae,unassigned_ratio | ConvertTo-Json -Compress; $_.steps.refine | ConvertTo-Json -Compress -Depth 5; $_.st`
17. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\quality\\round_3\\happy_t1.8_hole_character.png"}`
18. PowerShell：`{"command": "Get-Content output\\gen_c\\quality\\quality_report.json -TotalCount 80", "description": "Show quality report head"}`
19. Glob：`{"pattern": "**/visual_report.py", "path": "D:\\01_Project\\26_char_spine"}`
20. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\preview\\happy_python_simulation_preview.gif"}`
21. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_c; \"exit=$LASTEXITCODE\"", "description": "Generate visual repair report", "timeout": 300000}`
22. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\report\\repair_priority.md"}`
23. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\C\\sandbox_nl\\output\\gen_c\\report\\visual_check.png"}`

## 最後回覆（原文）

`gen_c.png` 已經拆成 8 個部件，Spine JSON、Idle/Happy 兩段動畫和預覽都產生了，但**還不算完成**：驗證報告裡有 5 項 BLOCKED、2 項 NOT_TESTED，也沒有產生 `.spine` 專案檔。

## 我怎麼拆這張圖
這是穿長裙的魔女，雙腳被裙子蓋住，所以我在 `gen_c.parts.json` 把 `leg_l`、`leg_r` 宣告為看不到的部件（absent），不建腳骨。拆出來的 8 個部件是：
- **head**：頭，含帽子。
- **hair**：長髮。
- **body**：身體，含披肩。
- **skirt**：長裙。
- **arm_l**：拿法杖的手，設定為必須和法杖保持接觸。
- **arm_r**：叉腰的手。
- **staff**：法杖。
- **shadow**：地面陰影。

第一次跑完後，我補大了漏掉的區域，沒被任何部件涵蓋的像素從 1.03% 降到 0.05%。法杖和兩隻手的擺動幅度也調低了。

## 驗證報告（validation_report.json）
| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 10 根骨頭，階層正確 |
| slots | PASS | 8 個插槽 |
| image_references | PASS | 所有部件圖片都在，也不是空白 |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢和原圖差異 0.0189 |
| manual_repairs | **BLOCKED** | shadow、hair 要人工補畫 |
| absent_parts | **BLOCKED** | leg_l、leg_r 沒有骨頭也沒有動畫，要不要補畫由你決定 |
| animation_quality | **BLOCKED** | 自動修正 3 輪後還有一處破洞：0.0108，門檻是 0.003，在 happy 第 1.8 秒 |
| spine_import | **BLOCKED** | 這台只有 Spine 試用版，不能存專案，所以做不出 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法驗證 |
| spine_editable | NOT_TESTED | 要你在 Spine Editor 裡開啟確認 |

**破洞那一項我的判斷（沒有驗證）**：紅框標出的區域是法杖和裙子之間、叉腰手臂圍出的空隙，以及月牙的鏤空。原圖裡這些地方本來就是背景。我認為是裙子擺動時碰到法杖，把背景圍成封閉區域，被檢查當成破洞。目視預覽看不出透明破洞，但還是需要你在 Spine 裡確認。

## 需要人工補畫（依 `report/repair_priority.md` 的順序）
1. **shadow（高）**：陰影有 77% 被裙子擋住，自動補的只是草稿，裙子擺動時最多露出 5.38%。圖層重組時裙襬下緣有一條偏深的補色。如果暫時不補，可以把裙子的擺動幅度再調低。
2. **hair（中）**：頭髮有 76% 被身體、手臂、頭擋住，最多露出 1.60%。
3. **body（中，自動補了但不可靠）**：身體被手臂和頭擋住的部分，最多露出 1.52%，請目視確認。
4. **leg_l／leg_r（看你需要）**：被長裙完全蓋住；要讓腳動，就得另外補畫。

補好後執行：
```
c2s prepare --replace <部件>=<修好的.png>
c2s run gen_c.png --motion happy
```

## 檔案
都在 `output\gen_c\`：
- 預覽：`preview\happy_python_simulation_preview.gif`（這是 Python Simulation Preview，不是 Spine 算圖）
- 總覽：`report\visual_check.png`。happy 和 idle 的影格裡，手都一直握著法杖。
- 修補清單：`repair_tasks.md`，裡面附匯回指令