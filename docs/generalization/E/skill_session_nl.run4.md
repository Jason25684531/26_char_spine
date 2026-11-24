# E Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_e.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（7 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：9 次
- 工具呼叫次數：{'PowerShell': 12, 'Read': 5, 'Skill': 1, 'Write': 2}

## c2s 指令

- `(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe`
- `& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe analyze gen_e.png; "EXIT=$LASTEXITCODE"`
- `& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_e.png --motion happy 2>&1 | Select-Object -Last 60; "EXIT=$LASTEXITCODE"`
- `& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_e.png --motion happy *> output_run.log; "EXIT=$LASTEXITCODE"; $m = Get-Content output\gen_e\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.needs_manual | % { "$($_.name) $($_.hidden_ratio)" }; $m.unassigned_regions | % { "$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)" }`
- `$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8
$t=$t.Replace('[300, 58], [312, 90], [380, 0]','[300, 50], [330, 40], [345, 60], [380, 0]')
$t=$t.Replace('[[255, 305], [300, 312], [380, 340], [455, 370]','[[255, 300], [300, 300], [360, 292], [425, 340], [458, 370]')
$t=$t.Replace('[385, 517], [362, 560], [352, 612]','[415, 505], [415, 590], [352, 612]')
$t=$t.Replace('[150, 605], [100, 560]','[150, 605], [205, 628], [100, 560]')
[IO.File]::WriteAllText((Resolve-Path $p), $t)
& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_e.png --motion happy *> output_run.log; "EXIT=$LASTEXITCODE"; $m = Get-Content output\gen_e\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.needs_manual | % { "$($_.name) $($_.hidden_ratio)" }; $m.unassigned_regions | select -First 5 | % { "$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)" }`
- `$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8
$t=$t.Replace('[240, 618], [150, 605], [205, 628], [100, 560]','[240, 618], [205, 630], [150, 605], [100, 560]')
[IO.File]::WriteAllText((Resolve-Path $p), $t)
& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_e.png --motion happy *> output_run.log; "EXIT=$LASTEXITCODE"; $m = Get-Content output\gen_e\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.needs_manual | % { "$($_.name) $($_.hidden_ratio)" }
$v = Get-Content output\gen_e\validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json; $v | ConvertTo-Json -Depth 6
Get-Content output\gen_e\quality\quality_report.json -Raw -Encoding utf8`
- `$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8
$t=$t.Replace('"z": 0, "parent": "body", "role": "accessory", "motion": 0','"z": 0, "parent": "root", "role": "accessory", "motion": 0')
[IO.File]::WriteAllText((Resolve-Path $p), $t)
& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_e.png --motion happy *> output_run.log; "EXIT=$LASTEXITCODE"; Get-Content output_run.log -Tail 5 -Encoding utf8
$v = Get-Content output\gen_e\validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json; $v.checks | % { "$($_.check): $($_.status) - $($_.detail)" }`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate c2s executable"}
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe analyze gen_e.png; \"EXIT=$LASTEXITCODE\"", "description": "Run c2s analyze on the image"}
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_e.png --motion happy 2>&1 | Select-Object -Last 60; \"EXIT=$LASTEXITCODE\"", "description": "Run full c2s pipeline with ha
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_e.png --motion happy *> output_run.log; \"EXIT=$LASTEXITCODE\"; $m = Get-Content output\\gen_e\\missing_parts.json -Raw -E
- PowerShell：{"command": "$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[300, 58], [312, 90], [380, 0]','[300, 50], [330, 40], [345, 60], [380, 0]')\n$t=$t.Replace('[[255, 305], [300
- PowerShell：{"command": "$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[240, 618], [150, 605], [205, 628], [100, 560]','[240, 618], [205, 630], [150, 605], [100, 560]')\n[IO.File]::
- PowerShell：{"command": "$s = Get-ChildItem -Recurse -Filter visual_report.py -Path .claude, D:\\01_Project\\26_char_spine\\scripts -ErrorAction SilentlyContinue | select -First 1; $s.FullName; & D:\\01_Project\\
- PowerShell：{"command": "$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('\"z\": 0, \"parent\": \"body\", \"role\": \"accessory\", \"motion\": 0','\"z\": 0, \"parent\": \"root\", \"rol
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_e | Out-Null; Get-Content output\\gen_e\\report\\repair_pr

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_e.png"}`
2. PowerShell：`{"command": "Get-ChildItem -Force | Select-Object Mode,Length,Name", "description": "List sandbox directory contents"}`
3. PowerShell：`{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate c2s executable"}`
4. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe analyze gen_e.png; \"EXIT=$LASTEXITCODE\"", "description": "Run c2s analyze on the image"}`
5. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\E\\sandbox_nl\\output\\gen_e\\grid_overlay.png"}`
6. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\E\\sandbox_nl\\gen_e.png"}`
7. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\E\\sandbox_nl\\gen_e.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"cape\", \"polygon\": [[235, 300], [300, 315], [380, 345], [450, 372], [420, 395], [380, 405], `
8. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_e.png --motion happy 2>&1 | Select-Object -Last 60; \"EXIT=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 600000}`
9. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\E\\sandbox_nl\\output\\gen_e\\layer_preview.png"}`
10. PowerShell：`{"command": "Get-Content output\\gen_e\\missing_parts.json -Raw", "description": "Show unassigned regions report"}`
11. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\E\\sandbox_nl\\gen_e.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[15, 628], [300, 625], [485, 632], [490, 660], [400, 672], [340, 700],`
12. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_e.png --motion happy *> output_run.log; \"EXIT=$LASTEXITCODE\"; $m = Get-Content output\\gen_e\\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; $m.needs_manual | % { \"$($_`
13. PowerShell：`{"command": "$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[300, 58], [312, 90], [380, 0]','[300, 50], [330, 40], [345, 60], [380, 0]')\n$t=$t.Replace('[[255, 305], [300, 312], [380, 340], [455, 370]','[[255, 300], [300, 300], [360, 292], [425, 340], [458, 370]')\n$t=$`
14. PowerShell：`{"command": "$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[240, 618], [150, 605], [205, 628], [100, 560]','[240, 618], [205, 630], [150, 605], [100, 560]')\n[IO.File]::WriteAllText((Resolve-Path $p), $t)\n& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run ge`
15. PowerShell：`{"command": "$s = Get-ChildItem -Recurse -Filter visual_report.py -Path .claude, D:\\01_Project\\26_char_spine\\scripts -ErrorAction SilentlyContinue | select -First 1; $s.FullName; & D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe $s.FullName output\\gen_e; \"EXIT=$LASTEXITCODE\"", "descr`
16. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\E\\sandbox_nl\\output\\gen_e\\layer_preview.png"}`
17. PowerShell：`{"command": "Get-Content output\\gen_e\\report\\repair_priority.md -Encoding utf8", "description": "Show repair priority report"}`
18. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\E\\sandbox_nl\\output\\gen_e\\report\\visual_check.png"}`
19. PowerShell：`{"command": "$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('\"z\": 0, \"parent\": \"body\", \"role\": \"accessory\", \"motion\": 0','\"z\": 0, \"parent\": \"root\", \"role\": \"accessory\", \"motion\": 0')\n[IO.File]::WriteAllText((Resolve-Path $p), $t)\n& D:\\01_Projec`
20. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_e | Out-Null; Get-Content output\\gen_e\\report\\repair_priority.md -Encoding utf8 | Select-String '^\\| \\d'; Get-Content output\\gen_e\\skeleton*.json,outpu`

## 最後回覆（原文）

我把 gen_e.png 做成了 Spine JSON 和兩段動畫（idle 2.0 秒、happy 2.4 秒），但還不算完成。驗證報告的總狀態是 **BLOCKED**：有 4 個部件要人工補畫，而且這台只有 Spine 試用版，做不出 `.spine` 專案檔。

部件拆成 12 個：頭、身體、兩手、兩腳，另外加上鹿角、小角、尾巴、紅領巾、背後披風、地面影子。拆分寫在圖片旁的 `gen_e.parts.json`。我照切圖結果修了三輪，未分配到部件的像素從 13% 降到 0.5%。地面影子原本跟著身體一起跳離地面，我把它改掛到不會動的根骨頭，讓它留在原地。

## 驗證報告（`validation_report.json`）

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 14 根骨頭，階層順序正確 |
| slots | PASS | 12 個插槽都對應到骨頭與部件圖 |
| image_references | PASS | 部件圖都存在、尺寸正確、不是空白 |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢和原圖差異 0.0032 |
| manual_repairs | **BLOCKED** | 等待人工補畫：shadow、cape、horn_small、leg_l |
| animation_quality | PASS | 破洞、關節縫隙、接觸分離都在門檻內。為了做到這點，系統自動調小了右手、頭、身體的動作幅度，所以 happy 的動作偏小 |
| spine_import | **BLOCKED** | 只有 Spine 試用版，不能存專案也不能匯出，無法產生 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法驗證匯入後再匯出是否一致 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡手動開啟確認 |

## 需要人工補畫（依優先順序）

1. **shadow（高）**：影子約 67% 被雙腳擋住，角色跳起來時這塊會露出來。被擋住的部分是系統自動補的灰色，誤差很小，看起來可能還過得去，但要用眼睛確認。
2. **cape（高）**：披風約 60% 被身體、手臂、尾巴擋住，動畫中最多露出 6%。紋理要手繪，自動補色會糊掉。
3. **leg_l（高）**：左腳上緣被身體擋住，動畫中最多露出 3.9%。
4. **horn_small（低）**：只露出約 8 像素，可以先保留草稿。

另外 scarf、body、leg_r、tail、head 也是系統自動補的，但不可靠。它們的露出都在 1% 左右或以下，建議看一下就好。每個部件的對照圖在 `output/gen_e/report/repair_priority.md`。

畫好之後執行：
```
c2s prepare --replace cape=<修好的.png>
c2s run gen_e.png --motion happy
```

主要檔案都在 `output/gen_e/` 底下：
- Spine JSON：`spine/character.json`
- 動畫預覽：`preview/happy_python_simulation_preview.gif`（Python 模擬的預覽，不是 Spine 算圖）
- 總覽：`report/visual_check.png`