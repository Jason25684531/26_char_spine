# B Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_b.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（6 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：7 次
- 工具呼叫次數：{'PowerShell': 10, 'Read': 4, 'Skill': 1, 'Write': 2}

## c2s 指令

- `Test-Path D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe; (Get-Command c2s -ErrorAction SilentlyContinue).Source; D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe analyze gen_b.png; "exit=$LASTEXITCODE"`
- `D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_b.png --motion happy | Select-Object -Last 60; "exit=$LASTEXITCODE"`
- `$o = D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_b.png --motion happy | Out-String; $j = $o | ConvertFrom-Json; $j | Select-Object * -ExcludeProperty steps | ConvertTo-Json -Depth 4; Get-Content output\gen_b\missing_parts.json -Raw`
- `$o = D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_b.png --motion happy | Out-String; "exit=$LASTEXITCODE"; $j = $o | ConvertFrom-Json; $j | Select-Object * -ExcludeProperty steps | ConvertTo-Json -Depth 4; $j.steps.prepare | ConvertTo-Json -Depth 3; (Get-Content output\gen_b\missing_parts.json -Raw | ConvertFrom-Json).unassigned_regions | Select-Object -First 8 | ConvertTo-Json -Compress`
- `$p='gen_b.parts.json'; $t=[IO.File]::ReadAllText($p); $t=$t.Replace('[300,705],[400,705],[450,700]','[300,698],[380,686],[450,686]').Replace('[700,225],[722,238],[782,298]','[700,222],[742,236],[762,262],[784,296]').Replace('[440,440],[450,400]]','[440,440],[443,392]]'); [IO.File]::WriteAllText($p,$t,(New-Object Text.UTF8Encoding $false)); $o = D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_b.png --motion happy | Out-String; "exit=$LASTEXITCODE"; ($o|ConvertFrom-Json).steps.prepare | Select-Object status,needs_manual,recompose_mae,unassigned_ratio | ConvertTo-Json; $v = Get-Content output\gen_b\validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json; $v.status; $v.checks | ForEach-Object { "{0}: {1} | {2}" -f $_.check,$_.status,$_.detail }; $q = Get-Content output\gen_b\quality\quality_report.json -Raw -Encoding utf8 | ConvertFrom-Json; "unresolved=" + ($q.unresolved | ConvertTo-Json -Compress); "downgraded=" + ($q.downgraded_to_needs_manual | ConvertTo-Json -Compress); "tuning=" + ($q.tuning | ConvertTo-Json -Compress)`
- `$p='gen_b.parts.json'; $t=[IO.File]::ReadAllText($p); $t=$t.Replace('"pivot": [500,700], "motion": 0.2','"pivot": [500,700], "motion": 0.1').Replace('"pivot": [580,700], "motion": 0.2','"pivot": [580,700], "motion": 0.1'); [IO.File]::WriteAllText($p,$t,(New-Object Text.UTF8Encoding $false)); $o = D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_b.png --motion happy | Out-String; "exit=$LASTEXITCODE"; $v = Get-Content output\gen_b\validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json; $v.status; $v.checks | ForEach-Object { "{0}: {1} | {2}" -f $_.check,$_.status,$_.detail }; $q = Get-Content output\gen_b\quality\quality_report.json -Raw -Encoding utf8 | ConvertFrom-Json; "unresolved=" + ($q.unresolved | ConvertTo-Json -Compress); "downgraded=" + ($q.downgraded_to_needs_manual | ConvertTo-Json -Compress)`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe; (Get-Command c2s -ErrorAction SilentlyContinue).Source; D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe analyze ge
- PowerShell：{"command": "D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_b.png --motion happy | Select-Object -Last 60; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy mot
- PowerShell：{"command": "$o = D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_b.png --motion happy | Out-String; $j = $o | ConvertFrom-Json; $j | Select-Object * -ExcludeProperty steps | ConvertTo-
- PowerShell：{"command": "$o = D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_b.png --motion happy | Out-String; \"exit=$LASTEXITCODE\"; $j = $o | ConvertFrom-Json; $j | Select-Object * -ExcludePro
- PowerShell：{"command": "$p='gen_b.parts.json'; $t=[IO.File]::ReadAllText($p); $t=$t.Replace('[300,705],[400,705],[450,700]','[300,698],[380,686],[450,686]').Replace('[700,225],[722,238],[782,298]','[700,222],[74
- PowerShell：{"command": "$p='gen_b.parts.json'; $t=[IO.File]::ReadAllText($p); $t=$t.Replace('\"pivot\": [500,700], \"motion\": 0.2','\"pivot\": [500,700], \"motion\": 0.1').Replace('\"pivot\": [580,700], \"motio
- PowerShell：{"command": "$s = Get-ChildItem -Recurse -Filter visual_report.py -Path .claude, D:\\01_Project\\26_char_spine\\scripts -ErrorAction SilentlyContinue | Select-Object -First 1; $s.FullName; D:\\01_Proj

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_b.png"}`
2. PowerShell：`{"command": "Get-ChildItem -Force | Select-Object Mode,Length,Name", "description": "List sandbox directory contents"}`
3. PowerShell：`{"command": "Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe; (Get-Command c2s -ErrorAction SilentlyContinue).Source; D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe analyze gen_b.png; \"exit=$LASTEXITCODE\"", "description": "Locate c2s and analyze image"}`
4. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\grid_overlay.png"}`
5. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\parts.template.json"}`
6. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\gen_b.parts.json", "content": "{\n  \"version\": 1,\n  \"image\": \"gen_b.png\",\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"leg_l\", \"polygon\": [[450,690],[545,690],[540,1150],[460,1150]]`
7. PowerShell：`{"command": "D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_b.png --motion happy | Select-Object -Last 60; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 600000}`
8. PowerShell：`{"command": "$o = D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_b.png --motion happy | Out-String; $j = $o | ConvertFrom-Json; $j | Select-Object * -ExcludeProperty steps | ConvertTo-Json -Depth 4; Get-Content output\\gen_b\\missing_parts.json -Raw", "description": "Show run message`
9. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\gen_b.parts.json", "content": "{\n  \"version\": 1,\n  \"image\": \"gen_b.png\",\n  \"preset\": \"humanoid-chibi\",\n  \"_note\": \"長裙完全遮住雙腿：leg_l / leg_r 是裙子的畫面左右兩半（中線重疊 20px），小幅擺動。\",\n  \"parts\": [\n    {\"name\`
10. PowerShell：`{"command": "$o = D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_b.png --motion happy | Out-String; \"exit=$LASTEXITCODE\"; $j = $o | ConvertFrom-Json; $j | Select-Object * -ExcludeProperty steps | ConvertTo-Json -Depth 4; $j.steps.prepare | ConvertTo-Json -Depth 3; (Get-Content outp`
11. PowerShell：`{"command": "Get-Content output\\gen_b\\validation_report.json -Raw; Get-Content output\\gen_b\\quality\\quality_report.json -Raw | Select-Object -First 1 | ForEach-Object { $_.Substring(0, [Math]::Min(4000, $_.Length)) }", "description": "Show validation and quality reports"}`
12. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\layer_preview.png"}`
13. PowerShell：`{"command": "$q = Get-Content output\\gen_b\\quality\\quality_report.json -Raw -Encoding utf8 | ConvertFrom-Json; $q.PSObject.Properties.Name -join ','; $q.unresolved | ConvertTo-Json -Depth 4; Get-ChildItem output\\gen_b\\preview | Select-Object Name", "description": "Show unresolved quality anomal`
14. PowerShell：`{"command": "$p='gen_b.parts.json'; $t=[IO.File]::ReadAllText($p); $t=$t.Replace('[300,705],[400,705],[450,700]','[300,698],[380,686],[450,686]').Replace('[700,225],[722,238],[782,298]','[700,222],[742,236],[762,262],[784,296]').Replace('[440,440],[450,400]]','[440,440],[443,392]]'); [IO.File]::Writ`
15. PowerShell：`{"command": "$p='gen_b.parts.json'; $t=[IO.File]::ReadAllText($p); $t=$t.Replace('\"pivot\": [500,700], \"motion\": 0.2','\"pivot\": [500,700], \"motion\": 0.1').Replace('\"pivot\": [580,700], \"motion\": 0.2','\"pivot\": [580,700], \"motion\": 0.1'); [IO.File]::WriteAllText($p,$t,(New-Object Text.U`
16. PowerShell：`{"command": "$s = Get-ChildItem -Recurse -Filter visual_report.py -Path .claude, D:\\01_Project\\26_char_spine\\scripts -ErrorAction SilentlyContinue | Select-Object -First 1; $s.FullName; D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe $s.FullName output\\gen_b; \"exit=$LASTEXITCODE\"; Ge`
17. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\B\\sandbox_nl\\output\\gen_b\\report\\visual_check.png"}`

## 最後回覆（原文）

`gen_b.png` 已做成 Spine 動畫。Spine JSON 驗證通過，但沒辦法存成 `.spine` 專案，所以整體狀態是 **BLOCKED**（原因：這台機器只有 Spine 試用版）。

## 驗證結果（`output/gen_b/validation_report.json`）

| 檢查項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 10 根骨頭，階層順序正確 |
| slots | PASS | 8 個插槽都對應到骨頭與部件圖 |
| image_references | PASS | 部件圖片都存在，尺寸相符，沒有空白圖 |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢和原圖的差異是 0.0010 |
| manual_repairs | PASS | 沒有部件被標成需要人工修補 |
| animation_quality | PASS | 破洞、關節縫隙、接觸分離、穿插都在門檻內（用的是自我修正第 3 輪的結果） |
| spine_import | **BLOCKED** | 偵測到的是 Spine 試用版，不能存專案也不能匯出，產生不了 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine` 檔，無法往返驗證 |
| spine_editable | NOT_TESTED | 要你在 Spine Editor 裡開專案、改關鍵影格，親自確認 |

## 處理過程
- **腿的做法跟一般角色不同**：長裙把腿完全蓋住，原本把腿畫在裙子底下時，`c2s` 判定腿沒有可見像素，沒辦法綁骨架。所以改成把裙子的畫面左、右兩半當作 `leg_l`／`leg_r`。兩半在中線重疊 20 像素，擺動幅度設為 0.1。
- **拉裙子的左手**：設成跟著 `leg_l` 動，接觸點在每一格都沒有分開。
- **其他部件**：雙馬尾 `hair_l`／`hair_r` 跟著頭動；拼圖髮飾併在 `head` 裡。
- **切圖**：未分配的像素是 0.09%，重組結果和原圖差異 0.0008。
- **調幅度**：第一次幅度設 0.2 時，`leg_l` 的補圖露出超過門檻，被降成需要人工修補。降到 0.1 後就回到門檻內。

## 建議目視確認（自動補圖，不是人工修補任務）
這三個部件被遮住的地方是自動補的，動畫中會露出一點，都在門檻內：
1. `body` 最多露出 1.69%：手臂、頭髮後面的身體輪廓是自動補的，紋理比較糊。
2. `hair_l` 最多露出 1.51%：被臉遮住的髮束根部。
3. `leg_l` 最多露出 1.43%：裙子中線被右半裙擋住的那一段輪廓。

想補畫的話，對照圖和補法在 `report/repair_priority.md`。修好後執行 `c2s prepare --replace <部件>=<修好的.png>`，再執行 `c2s run gen_b.png`。

## 檔案
- 部件設定：`gen_b.parts.json`（放在圖片旁）
- Spine JSON 與部件圖：`output/gen_b/spine/`
- 預覽：`output/gen_b/preview/happy_python_simulation_preview.gif`。這是 Python Simulation Preview，不是 Spine 算圖。
- 關鍵影格總覽：`output/gen_b/report/visual_check.png`

要拿到 `.spine` 專案，得在有完整版 Spine 的電腦上匯入 `spine/` 裡的 JSON。