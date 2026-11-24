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
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：6 次
- 工具呼叫次數：{'Glob': 1, 'PowerShell': 7, 'Read': 6, 'Skill': 1, 'Write': 1}

## c2s 指令

- `ls; ls .venv\Scripts\c2s.exe; .venv\Scripts\c2s.exe analyze gen_a.png; "exit=$LASTEXITCODE"`
- `(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe`
- `$c="D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe"; & $c analyze gen_a.png; "exit=$LASTEXITCODE"; ls output\gen_a.png -ErrorAction SilentlyContinue; ls output`
- `$c="D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe"; & $c run gen_a.png --motion happy | Select-Object -Last 40; "exit=$LASTEXITCODE"`
- `$f="gen_a.parts.json"; $t=[IO.File]::ReadAllText($f)
$t=$t.Replace('[[615,495],[700,505],[732,620],[738,758],[678,758],[660,640],[628,560]]','[[615,495],[700,505],[732,620],[738,758],[678,758],[662,655],[616,655],[616,560]]')
$t=$t.Replace('[[395,778],[492,778],[487,860],[472,932],[412,932],[402,860]]','[[388,778],[492,778],[488,860],[486,940],[412,940],[392,860]]')
$t=$t.Replace('[388,802],[343,762]]','[388,802],[348,795],[340,762]]')
$t=$t.Replace('[[165,58],[802,58]','[[165,50],[802,50]').Replace('[300,560],[240,500],[200,400],[165,300]]','[300,560],[226,522],[222,470],[166,385],[162,300]]')
[IO.File]::WriteAllText($f,$t)
$c="D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe"; & $c run gen_a.png --motion happy | Out-Null; "exit=$LASTEXITCODE"`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate c2s executable"}
- PowerShell：{"command": "$c=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\"; & $c analyze gen_a.png; \"exit=$LASTEXITCODE\"; ls output\\gen_a.png -ErrorAction SilentlyContinue; ls output", "description
- PowerShell：{"command": "$c=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\"; & $c run gen_a.png --motion happy | Select-Object -Last 40; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline",
- PowerShell：{"command": "$f=\"gen_a.parts.json\"; $t=[IO.File]::ReadAllText($f)\n$t=$t.Replace('[[615,495],[700,505],[732,620],[738,758],[678,758],[660,640],[628,560]]','[[615,495],[700,505],[732,620],[738,758],[
- Glob：{"pattern": "**/visual_report.py", "path": "D:\\01_Project\\26_char_spine"}
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe D:\\01_Project\\26_char_spine\\scripts\\visual_report.py . | Out-Null; \"exit=$LASTEXITCODE\"; Get-Content report\\repair_prior

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_a.png"}`
2. PowerShell：`{"command": "ls; ls .venv\\Scripts\\c2s.exe; .venv\\Scripts\\c2s.exe analyze gen_a.png; \"exit=$LASTEXITCODE\"", "description": "List files and run c2s analyze"}`
3. PowerShell：`{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate c2s executable"}`
4. PowerShell：`{"command": "$c=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\"; & $c analyze gen_a.png; \"exit=$LASTEXITCODE\"; ls output\\gen_a.png -ErrorAction SilentlyContinue; ls output", "description": "Run c2s analyze on gen_a.png"}`
5. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\grid_overlay.png"}`
6. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\parts.template.json"}`
7. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\gen_a.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"braid_l\", \"polygon\": [[240,515],[350,515],[345,620],[305,700],[298,758],[248,758],[258,640]`
8. PowerShell：`{"command": "$c=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\"; & $c run gen_a.png --motion happy | Select-Object -Last 40; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
9. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\layer_preview.png"}`
10. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\validation_report.json"}`
11. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\missing_parts.json"}`
12. PowerShell：`{"command": "$f=\"gen_a.parts.json\"; $t=[IO.File]::ReadAllText($f)\n$t=$t.Replace('[[615,495],[700,505],[732,620],[738,758],[678,758],[660,640],[628,560]]','[[615,495],[700,505],[732,620],[738,758],[678,758],[662,655],[616,655],[616,560]]')\n$t=$t.Replace('[[395,778],[492,778],[487,860],[472,932],[`
13. PowerShell：`{"command": "cd output\\gen_a; (Get-Content validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json).checks | ft check,status,detail -Wrap; $m=Get-Content missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; $m.unassigned_regions | % { \"$($_.neares`
14. Glob：`{"pattern": "**/visual_report.py", "path": "D:\\01_Project\\26_char_spine"}`
15. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_nl\\output\\gen_a\\preview\\happy_python_simulation_preview.gif"}`
16. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe D:\\01_Project\\26_char_spine\\scripts\\visual_report.py . | Out-Null; \"exit=$LASTEXITCODE\"; Get-Content report\\repair_priority.md -Encoding utf8 -TotalCount 40", "description": "Generate visual repair report"}`

## 最後回覆（原文）

`gen_a.png` 已經做成 Spine JSON，有 Idle 和 Happy 兩段動畫，但還沒完成：驗證總狀態是 **BLOCKED**。有 4 個部件要人工補畫，而且這台電腦只有 Spine 試用版，做不出 `.spine` 專案檔。

**切圖**：我依圖寫了 `gen_a.parts.json`（放在圖片旁），拆成 9 個部件：頭（含帽子）、身體、裙子、左右手、左右腳、左右辮子。修過一輪邊界後，沒分配到部件的像素從 0.49% 降到 0.01%。

**驗證結果（`validation_report.json`）**

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 11 根骨頭，階層順序正確 |
| slots | PASS | 9 個插槽 |
| image_references | PASS | 圖片都在，尺寸也對 |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢和原圖的差異 0.0020 |
| animation_quality | PASS | 逐格檢查破洞、縫隙、接觸分離都在門檻內；兩條辮子有少量補圖露出（約 0.9%），還在門檻內，建議目視 |
| manual_repairs | **BLOCKED** | body、leg_l、leg_r、skirt 要人工補畫 |
| spine_import | **BLOCKED** | 偵測到的是 Spine 試用版，不能存檔或匯出，所以做不出 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法驗證 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡手動開啟確認 |

**要人工補畫的部件（依動畫中露出量排序）**

1. `skirt`：被兩隻手擋住的地方，動畫中最多露出 10.0%
2. `leg_l`：被右腳和裙子擋住，最多露出 7.4%
3. `body`：55% 被擋住，最多露出 5.9%
4. `leg_r`：被裙子擋住，最多露出 2.3%

這些地方目前是自動填補的草稿，在動畫裡會看到模糊的補色。每個部件的三格對照圖在 `output/gen_a/report/repair_priority.md`。補好後執行：
`c2s prepare --replace skirt=<修好的.png>`，再執行 `c2s run gen_a.png`。

如果暫時不補，可以把雙手、裙子的 `motion` 調低，讓擋住的地方少露出一點，代價是動作會變小。

預覽動畫 `preview/happy_python_simulation_preview.gif` 是 Python Simulation Preview，不是 Spine 算圖。我只看了它的第一格，整段動作還沒目視過，請你播放確認一下。