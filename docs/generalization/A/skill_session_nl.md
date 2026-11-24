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
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：2 次
- 工具呼叫次數：{'Edit': 2, 'Glob': 1, 'PowerShell': 6, 'Read': 9, 'Skill': 1, 'Write': 2}

## c2s 指令

- `Get-Command c2s -ErrorAction SilentlyContinue | Select-Object Source; Test-Path D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe; Test-Path .\.venv`
- `c2s analyze gen_a.png; "exit=$LASTEXITCODE"; Get-ChildItem -Recurse output | Select-Object FullName`
- `c2s run gen_a.png --motion happy; "exit=$LASTEXITCODE"`
- `c2s run gen_a.png --motion happy | Out-Null; "exit=$LASTEXITCODE"; $m = Get-Content output\gen_a\missing_parts.json -Raw | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.unassigned_regions | Select-Object -First 6 | ForEach-Object { "$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)" }; $m.needs_manual | ForEach-Object { "$($_.name): $($_.reason)" }; (Get-Content output\gen_a\validation_report.json -Raw | ConvertFrom-Json).checks | ForEach-Object { "$($_.check) $($_.status) | $($_.detail)" }`
- `c2s run gen_a.png --motion happy | Out-Null; "exit=$LASTEXITCODE"; $r = [IO.File]::ReadAllText("$PWD\output\gen_a\validation_report.json", [Text.Encoding]::UTF8) | ConvertFrom-Json; $r.checks | ForEach-Object { "$($_.check) $($_.status) | $($_.detail)" }; $m = [IO.File]::ReadAllText("$PWD\output\gen_a\missing_parts.json", [Text.Encoding]::UTF8) | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.needs_manual | ForEach-Object { "$($_.name): $($_.reason)" }`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "Get-Command c2s -ErrorAction SilentlyContinue | Select-Object Source; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe; Test-Path .\\.venv", "description": "Locate c2s exe
- PowerShell：{"command": "$py = \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; $s = if (Test-Path scripts\\visual_report.py) { \"scripts\\visual_report.py\" } else { \"D:\\01_Project\\26_char_spine

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_a.png"}`
2. Glob：`{"pattern": "**/*"}`
3. PowerShell：`{"command": "Get-Command c2s -ErrorAction SilentlyContinue | Select-Object Source; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe; Test-Path .\\.venv", "description": "Locate c2s executable"}`
4. PowerShell：`{"command": "c2s analyze gen_a.png; \"exit=$LASTEXITCODE\"; Get-ChildItem -Recurse output | Select-Object FullName", "description": "Run c2s analyze on the image"}`
5. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\grid_overlay.png"}`
6. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\parts.template.json"}`
7. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\gen_a.parts.json", "content": "{\n  \"version\": 1,\n  \"image\": \"gen_a.png\",\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"braid_l\", \"polygon\": [[270,515],[352,520],[348,600],[322,660],`
8. PowerShell：`{"command": "c2s run gen_a.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
9. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\layer_preview.png"}`
10. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\missing_parts.json"}`
11. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\gen_a.parts.json", "content": "{\n  \"version\": 1,\n  \"image\": \"gen_a.png\",\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"braid_l\", \"polygon\": [[262,515],[352,520],[348,600],[322,660],`
12. PowerShell：`{"command": "c2s run gen_a.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; $m = Get-Content output\\gen_a\\missing_parts.json -Raw | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; $m.unassigned_regions | Select-Object -First 6 | ForEach-Object { \"$($_.bbox -join ',') area=$($_.area`
13. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\quality\\round_3\\happy_t0.8_hole_character.png"}`
14. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\quality\\quality_report.json", "limit": 80}`
15. Edit：`{"replace_all": false, "file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\gen_a.parts.json", "old_string": "[565,645],[555,700],[562,735]", "new_string": "[588,645],[588,700],[588,735]"}`
16. Edit：`{"replace_all": false, "file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\gen_a.parts.json", "old_string": "[552,675],[582,738]", "new_string": "[588,675],[598,738]"}`
17. PowerShell：`{"command": "c2s run gen_a.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; $r = [IO.File]::ReadAllText(\"$PWD\\output\\gen_a\\validation_report.json\", [Text.Encoding]::UTF8) | ConvertFrom-Json; $r.checks | ForEach-Object { \"$($_.check) $($_.status) | $($_.detail)\" }; $m = [IO.File]::ReadAl`
18. PowerShell：`{"command": "$py = \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; $s = if (Test-Path scripts\\visual_report.py) { \"scripts\\visual_report.py\" } else { \"D:\\01_Project\\26_char_spine\\scripts\\visual_report.py\" }; & $py $s output\\gen_a; \"exit=$LASTEXITCODE\"; Get-ChildItem outpu`
19. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\layer_preview.png"}`
20. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\report\\repair_priority.md"}`
21. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\report\\visual_check.png"}`

## 最後回覆（原文）

`gen_a.png` 已經做成 Spine JSON 骨架加兩段動畫（idle、happy），可以拿去看了。但還不算完成：有 4 個部件的遮擋處要人工補畫，`.spine` 專案檔也做不出來。

我把部件拆分寫在圖片旁的 `gen_a.parts.json`，共 9 個部件：頭（含帽子）、身體、左右手、左右腿、裙擺、左右辮子。`c2s run` 跑了 3 次：
- **第 1 次**：有 1.18% 的像素沒分到任何部件（帽子上的黃色棒子、臉側頭髮、右手、裙擺下緣等），我把這些部件的範圍擴大。
- **第 2 次**：沒分到的降到 0.1%，但右手擺動時身體側面露出破洞，動畫品質檢查判為 BLOCKED。我把身體和裙擺的右側加寬。
- **第 3 次**：沒分到的只剩 0.02%，切圖重組後和原圖幾乎一樣，動畫品質檢查 PASS。

## 驗證結果（`validation_report.json`）

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 11 根骨頭，階層順序正確 |
| slots | PASS | 9 個插槽 |
| image_references | PASS | 所有部件圖片都在，尺寸正確 |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢和原圖差異 0.0022 |
| animation_quality | PASS | 逐格檢查沒有破洞、縫隙、分離；兩條辮子有少量補圖露出（1.4%／1.7%），在門檻內，建議目視確認 |
| manual_repairs | **BLOCKED** | 等待人工補畫，見下表 |
| spine_import | **BLOCKED** | 這台電腦只有 Spine 試用版，不能存專案也不能匯出，所以做不出 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法往返驗證 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡人工開啟確認 |

## 要人工補畫的部件（依動畫中露出多寡排序）

這幾個部件被遮住的地方目前只是自動填的草稿，還沒修好：

1. **skirt（裙擺）**：被雙手遮住的部分。動畫中最多露出 14.9%，輪廓和皺褶要看原圖重畫。
2. **leg_l（左腿）**：被右腿和裙子遮住約 45%。最多露出 10.8%。
3. **body（身體）**：被裙子、雙手、頭遮住約 60%。最多露出 5.2%，自動填的效果最差。
4. **leg_r（右腿）**：被裙子遮住的大腿上段。最多露出 3.4%。

每個部件的對照圖在 `output/gen_a/report/repair_priority.md`。補好一張後執行 `c2s prepare --replace skirt=<修好的.png>`，再跑一次 `c2s run gen_a.png`。如果暫時不補，也可以在 parts.json 降低遮擋它的部件的 `motion`，動作會變小，但露出也會減少。

## 檔案位置
- Spine JSON 與各部件圖：`output/gen_a/`
- 預覽動畫：`output/gen_a/preview/happy_python_simulation_preview.gif`（這是 Python Simulation Preview，不是 Spine 實際算出來的畫面）
- 關鍵影格總覽：`output/gen_a/report/visual_check.png`