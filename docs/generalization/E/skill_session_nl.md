# E Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_e.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（5 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：0 次
- 工具呼叫次數：{'Glob': 1, 'PowerShell': 8, 'Read': 5, 'Skill': 1, 'Write': 1}

## c2s 指令

- `ls; $c = if (Test-Path .venv\Scripts\c2s.exe) { '.venv\Scripts\c2s.exe' } else { 'c2s' }; & $c analyze gen_e.png; "EXIT=$LASTEXITCODE"`
- `$c = if (Test-Path .venv\Scripts\c2s.exe) { '.venv\Scripts\c2s.exe' } else { 'c2s' }; & $c run gen_e.png --motion happy; "EXIT=$LASTEXITCODE"`
- `$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8
$t=$t.Replace('[[0,250],[15,200],[55,155],[58,118],[90,125],[110,140],[160,140],[215,148],[258,168],[283,210],[285,265],[270,300],[240,325],[205,340],[160,360],[110,385],[60,382],[25,345],[5,300]]','[[0,240],[10,200],[50,155],[55,118],[95,122],[115,132],[160,126],[215,132],[260,158],[285,205],[290,265],[272,300],[240,325],[205,340],[160,360],[110,392],[60,402],[25,408],[0,385]]')
$t=$t.Replace('[[205,335],[260,290],[305,255],[325,200],[330,150],[355,135],[378,160],[410,125],[440,92],[472,90],[478,110],[455,150],[440,185],[442,235],[415,262],[380,280],[330,325],[285,370],[245,392],[220,375]]','[[205,335],[255,290],[266,250],[270,190],[300,170],[330,140],[355,135],[378,155],[405,118],[430,84],[472,80],[482,105],[462,150],[452,175],[454,235],[442,265],[400,295],[355,320],[300,360],[255,395],[220,378]]')
$t=$t.Replace('[[245,175],[265,125],[285,105],[270,80],[300,60]','[[245,175],[262,125],[264,84],[285,70],[300,60]').Replace('[400,100],[405,130],[355,135]','[400,100],[408,130],[406,162],[380,162],[355,135]')
$t=$t.Replace('[[95,530],[140,545]','[[95,498],[140,545]').Replace('[38,660],[42,635],[70,605],[88,565]]','[38,660],[44,625],[50,580],[66,530]]')
$t=$t.Replace('[450,495],[390,520],[350,570],[320,590],[295,530]]','[450,495],[412,520],[410,580],[390,634],[340,636],[320,590],[295,530]]')
Set-Content $p $t -Encoding utf8 -NoNewline
$c = if (Test-Path .venv\Scripts\c2s.exe) { '.venv\Scripts\c2s.exe' } else { 'c2s' }; & $c run gen_e.png --motion happy | ConvertFrom-Json | % { $_.steps.prepare | ConvertTo-Json -Compress; $_.steps.refine | ConvertTo-Json -Compress -Depth 5; $_.steps.validate.checks | % { "$($_.check): $($_.status) - $($_.detail)" } }; "EXIT=$LASTEXITCODE"; (Get-Content output\gen_e\missing_parts.json -Raw | ConvertFrom-Json).unassigned_regions | select -First 6 | ConvertTo-Json -Compress`
- `$c = if (Test-Path .venv\Scripts\c2s.exe) { '.venv\Scripts\c2s.exe' } else { 'c2s' }; & $c run gen_e.png --motion happy | Select-Object -Last 60; "EXIT=$LASTEXITCODE"`
- `$p=(Resolve-Path gen_e.parts.json).Path; $t=[IO.File]::ReadAllText($p).TrimStart([char]0xFEFF); [IO.File]::WriteAllText($p,$t,(New-Object Text.UTF8Encoding $false))
$c = if (Test-Path .venv\Scripts\c2s.exe) { '.venv\Scripts\c2s.exe' } else { 'c2s' }; $o = (& $c run gen_e.png --motion happy) -join "`n"; "EXIT=$LASTEXITCODE"; $j=$o|ConvertFrom-Json; $j.status; $j.steps.prepare | ConvertTo-Json -Compress; $j.steps.refine | ConvertTo-Json -Compress -Depth 5; $j.steps.validate.checks | % { "$($_.check): $($_.status) - $($_.detail)" }; (Get-Content output\gen_e\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json).unassigned_regions | select -First 6 | ConvertTo-Json -Compress`

## 讀到答案

- 無

## 使用沙盒外的工具

- 無

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_e.png"}`
2. PowerShell：`{"command": "ls; $c = if (Test-Path .venv\\Scripts\\c2s.exe) { '.venv\\Scripts\\c2s.exe' } else { 'c2s' }; & $c analyze gen_e.png; \"EXIT=$LASTEXITCODE\"", "description": "List files and run c2s analyze"}`
3. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\E\\sandbox_nl\\output\\gen_e\\grid_overlay.png"}`
4. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\E\\sandbox_nl\\gen_e.png"}`
5. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\E\\sandbox_nl\\gen_e.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[15,640],[200,635],[480,628],[495,650],[420,670],[385,720],[300,720],[2`
6. PowerShell：`{"command": "$c = if (Test-Path .venv\\Scripts\\c2s.exe) { '.venv\\Scripts\\c2s.exe' } else { 'c2s' }; & $c run gen_e.png --motion happy; \"EXIT=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 600000}`
7. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\E\\sandbox_nl\\output\\gen_e\\layer_preview.png"}`
8. PowerShell：`{"command": "Get-Content output\\gen_e\\missing_parts.json -Raw", "description": "Show unassigned regions report"}`
9. PowerShell：`{"command": "$p='gen_e.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[[0,250],[15,200],[55,155],[58,118],[90,125],[110,140],[160,140],[215,148],[258,168],[283,210],[285,265],[270,300],[240,325],[205,340],[160,360],[110,385],[60,382],[25,345],[5,300]]','[[0,240],[10,200],[50,155]`
10. PowerShell：`{"command": "$c = if (Test-Path .venv\\Scripts\\c2s.exe) { '.venv\\Scripts\\c2s.exe' } else { 'c2s' }; & $c run gen_e.png --motion happy | Select-Object -Last 60; \"EXIT=$LASTEXITCODE\"", "description": "Rerun pipeline showing raw output", "timeout": 600000}`
11. PowerShell：`{"command": "$p=(Resolve-Path gen_e.parts.json).Path; $t=[IO.File]::ReadAllText($p).TrimStart([char]0xFEFF); [IO.File]::WriteAllText($p,$t,(New-Object Text.UTF8Encoding $false))\n$c = if (Test-Path .venv\\Scripts\\c2s.exe) { '.venv\\Scripts\\c2s.exe' } else { 'c2s' }; $o = (& $c run gen_e.png --moti`
12. PowerShell：`{"command": "python scripts/visual_report.py output\\gen_e; if (-not $?) { python .claude\\skills\\character-to-spine\\scripts\\visual_report.py output\\gen_e }; \"EXIT=$LASTEXITCODE\"; Get-Content output\\gen_e\\report\\repair_priority.md -Encoding utf8 -TotalCount 60", "description": "Generate vis`
13. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\E\\sandbox_nl\\output\\gen_e\\layer_preview.png"}`
14. Glob：`{"pattern": "**/visual_report.py", "path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\E"}`
15. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\E\\sandbox_nl\\output\\gen_e\\preview\\happy_python_simulation_preview.gif"}`
16. PowerShell：`{"command": "Get-Content output\\gen_e\\repair_tasks.md -Encoding utf8; ls output\\gen_e | select Name", "description": "Show repair task list and output files"}`

## 最後回覆（原文）

我已經把 gen_e.png 拆好骨架、做好動畫，也輸出了 Spine JSON。但整體驗證狀態是 **BLOCKED**，還不算完成：有 6 個部件需要人工補畫，而且這台電腦只有 Spine 試用版，沒辦法產生 `.spine` 專案檔。

**拆件結果**

我把圖拆成 11 個部件（左右是指畫面的左右）：
- 6 個必要部件：頭、身體、左右手、左右腳。
- 另外拆出披風、尾巴、頭上的角、胸前圍巾和地面影子。

第一次切圖有 5.7% 的像素沒分到任何部件，我調整了 `gen_e.parts.json` 的範圍後重跑，降到 0.4%。從 `layer_preview.png` 看，拆好的圖層組回去跟原圖幾乎一樣。

產生了兩段動畫：idle（2.0 秒）和 happy（2.4 秒）。程式自動檢查了 4 輪，採用第 3 輪的結果，並自動調低了右手、頭、身體和雙腳的擺動幅度。

**驗證報告（`validation_report.json`）**

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 13 根骨頭，階層正確 |
| slots | PASS | 11 個插槽 |
| image_references | PASS | 所有部件圖片都存在，也不是空白 |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢與原圖差異 0.0019 |
| manual_repairs | **BLOCKED** | 有 6 個部件等待人工修補 |
| animation_quality | PASS | 破洞、關節縫隙、接觸分離都在門檻內；`arm_l`、`horn` 的補圖露出超過門檻，已改列為需人工修補 |
| spine_import | **BLOCKED** | 只偵測到 Spine 試用版，不能存檔也不能匯出，所以做不出 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine` 檔，無法驗證匯入匯出 |
| spine_editable | NOT_TESTED | 需要你在 Spine Editor 裡打開確認 |

**需要人工補畫的部件**

下面依清單順序排列，不是依重要程度：被擋住的區域目前只是自動補的草稿。

1. `shadow`：49% 被擋住。
2. `cape`：58% 被擋住。
3. `horn`：自動補圖不可靠，動畫中會露出 2.9%。
4. `leg_l`：39% 被擋住。
5. `leg_r`：45% 被擋住。
6. `arm_l`：自動補圖不可靠，動畫中會露出 2.1%。

另外 `body`、`head`、`scarf` 的補圖也不太可靠，雖然露出量在門檻內，還是建議你自己看一下動畫。

補好任一部件後執行下面兩行，就會存進 `gen_e.overrides/` 並重新產生動畫：
```
c2s prepare --replace <部件>=<修好的.png>
c2s run gen_e.png
```
每一項的草稿圖層路徑寫在 `output/gen_e/repair_tasks.md`。

**沒做到的地方**

- 技能文件要求用 `scripts/visual_report.py` 依「動畫實際露出量」排出修補優先順序並附對照圖，但專案裡找不到這支程式，所以這份報告沒有產生。上面的清單是 `repair_tasks.md` 的內容，沒有排序。
- 預覽動畫 `output/gen_e/preview/happy_python_simulation_preview.gif` 是 Python Simulation Preview，不是 Spine 算圖。我只能看到第一格，所以實際動作沒有用眼睛檢查過，建議你自己播放看看。