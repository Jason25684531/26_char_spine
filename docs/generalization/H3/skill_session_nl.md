# H3 Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`我想讓這張圖裡的角色在遊戲裡動起來：gen_h3.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（7 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：8 次
- 工具呼叫次數：{'Glob': 1, 'PowerShell': 12, 'Read': 8, 'Skill': 1, 'Write': 1}

## c2s 指令

- `$c = if (Test-Path .venv\Scripts\c2s.exe) { ".venv\Scripts\c2s.exe" } else { (Get-Command c2s -ErrorAction SilentlyContinue).Source }; "c2s=$c"; if ($c) { & $c analyze gen_h3.png; "exit=$LASTEXITCODE" }; Get-ChildItem -Recurse output -ErrorAction SilentlyContinue | Select-Object FullName`
- `& "D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe" run gen_h3.png --motion happy; "exit=$LASTEXITCODE"`
- `$f='gen_h3.parts.json'; $t=Get-Content $f -Raw -Encoding utf8
$t=$t.Replace('[[150,45],[230,30],[320,40],[345,110],[365,160],[350,200],[375,280],[395,360],[395,435],[370,440],[340,400],[150,400],[130,425],[110,420],[105,330],[118,250],[130,180],[125,160],[150,110]]','[[150,45],[230,30],[320,40],[345,100],[370,160],[360,200],[400,260],[420,330],[426,430],[400,440],[370,445],[340,400],[150,400],[130,430],[100,425],[96,330],[110,250],[118,180],[112,160],[140,100]]')
$t=$t.Replace('[[254,455],[324,455],[320,560],[316,640],[336,700],[355,760],[352,805],[298,808],[298,760],[288,700],[268,640],[256,560]]','[[254,455],[326,455],[330,560],[340,620],[350,680],[360,740],[358,812],[298,812],[298,760],[288,700],[268,640],[256,560]]')
$t=$t.Replace('[[195,455],[252,455],[250,560],[235,640],[215,700],[214,760],[212,812],[166,812],[166,760],[175,700],[180,640],[190,560]]','[[190,455],[252,455],[250,560],[235,640],[215,700],[214,760],[212,812],[164,812],[164,760],[166,700],[172,640],[184,560]]')
$t=$t.Replace('[[182,335],[302,335],[340,350],[380,400],[396,455],[376,474],[300,472],[250,482],[200,480],[150,472],[113,462],[122,420],[160,365]]','[[182,335],[302,335],[340,350],[380,400],[396,455],[394,502],[322,502],[300,476],[250,484],[200,484],[196,498],[150,498],[113,462],[122,420],[160,365]]')
Set-Content $f $t -Encoding utf8 -NoNewline
& "D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe" run gen_h3.png --motion happy | Out-File output\_run.json -Encoding utf8; "exit=$LASTEXITCODE"
$j=Get-Content output\_run.json -Raw -Encoding utf8 | ConvertFrom-Json; $j.steps.prepare | Select needs_manual,recompose_mae,unassigned_ratio | fl; $j.steps.refine | Select status,unresolved,downgraded_to_needs_manual | fl; $j.steps.validate.checks | ft check,status,detail -Wrap
(Get-Content output\gen_h3\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json).unassigned_regions | Select -First 6 | ft`
- `Get-Content output\_run.json -Encoding utf8 | Select-Object -First 60; Get-Content output\gen_h3\c2s_error.log -Tail 20 -ErrorAction SilentlyContinue`
- `$f=(Resolve-Path gen_h3.parts.json).Path; [IO.File]::WriteAllText($f, [IO.File]::ReadAllText($f).TrimStart([char]0xFEFF), (New-Object Text.UTF8Encoding $false))
& "D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe" run gen_h3.png --motion happy | Out-File output\_run.json -Encoding utf8; "exit=$LASTEXITCODE"
$j=Get-Content output\_run.json -Raw -Encoding utf8 | ConvertFrom-Json; $j.status; $j.steps.prepare | Select needs_manual,recompose_mae,unassigned_ratio | fl; $j.steps.refine | Select status,chosen_round,unresolved,downgraded_to_needs_manual | fl; $j.steps.validate.checks | ft check,status,detail -Wrap
(Get-Content output\gen_h3\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json).unassigned_regions | Select -First 6 | ft`
- `$f=(Resolve-Path gen_h3.parts.json).Path; $t=[IO.File]::ReadAllText($f)
$t=$t.Replace('"pivot": [228,80], "motion": 0.6','"pivot": [228,80], "motion": 0.35').Replace('[[190,455],[252,455],[250,560]','[[190,455],[257,455],[257,580]')
[IO.File]::WriteAllText($f,$t,(New-Object Text.UTF8Encoding $false))
& "D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe" run gen_h3.png --motion happy | Out-File output\_run.json -Encoding utf8; "exit=$LASTEXITCODE"
$j=Get-Content output\_run.json -Raw -Encoding utf8 | ConvertFrom-Json; $j.steps.prepare | Select needs_manual,unassigned_ratio | fl; $j.steps.refine | Select status,chosen_round,unresolved | fl; $j.steps.validate.checks | ft check,status,detail -Wrap`
- `$f=(Resolve-Path gen_h3.parts.json).Path; $t=[IO.File]::ReadAllText($f)
$t=$t.Replace('[400,440],[370,445],[340,400],[150,400],[130,430],[100,425]','[400,445],[370,455],[300,455],[180,455],[130,445],[100,430]')
[IO.File]::WriteAllText($f,$t,(New-Object Text.UTF8Encoding $false))
& "D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe" run gen_h3.png --motion happy | Out-File output\_run.json -Encoding utf8; "exit=$LASTEXITCODE"
$j=Get-Content output\_run.json -Raw -Encoding utf8 | ConvertFrom-Json; $j.steps.prepare | Select needs_manual,unassigned_ratio | fl; $j.steps.refine | Select status,chosen_round,unresolved,tuning | fl; $j.steps.validate.checks | ft check,status,detail -Wrap`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "Get-Content output\\gen_h3\\parts.template.json; $py=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; & $py -I -c \"from PIL import Image; im=Image.open(r'output\\gen_h3\\gr
- PowerShell：{"command": "& \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\" run gen_h3.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 6
- PowerShell：{"command": "$f='gen_h3.parts.json'; $t=Get-Content $f -Raw -Encoding utf8\n$t=$t.Replace('[[150,45],[230,30],[320,40],[345,110],[365,160],[350,200],[375,280],[395,360],[395,435],[370,440],[340,400],[
- PowerShell：{"command": "$f=(Resolve-Path gen_h3.parts.json).Path; [IO.File]::WriteAllText($f, [IO.File]::ReadAllText($f).TrimStart([char]0xFEFF), (New-Object Text.UTF8Encoding $false))\n& \"D:\\01_Project\\26_ch
- PowerShell：{"command": "$f=(Resolve-Path gen_h3.parts.json).Path; $t=[IO.File]::ReadAllText($f)\n$t=$t.Replace('\"pivot\": [228,80], \"motion\": 0.6','\"pivot\": [228,80], \"motion\": 0.35').Replace('[[190,455],
- PowerShell：{"command": "& \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\" -I -c \"from PIL import Image; im=Image.open(r'output\\gen_h3\\quality\\round_3\\happy_t2.2_hole_character.png'); print(im.
- PowerShell：{"command": "$f=(Resolve-Path gen_h3.parts.json).Path; $t=[IO.File]::ReadAllText($f)\n$t=$t.Replace('[400,440],[370,445],[340,400],[150,400],[130,430],[100,425]','[400,445],[370,455],[300,455],[180,45
- PowerShell：{"command": "$py=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; $s=Get-ChildItem -Recurse -Filter visual_report.py -Path .claude,\"D:\\01_Project\\26_char_spine\\scripts\" -ErrorAction

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_h3.png"}`
2. Glob：`{"pattern": "*"}`
3. PowerShell：`{"command": "$c = if (Test-Path .venv\\Scripts\\c2s.exe) { \".venv\\Scripts\\c2s.exe\" } else { (Get-Command c2s -ErrorAction SilentlyContinue).Source }; \"c2s=$c\"; if ($c) { & $c analyze gen_h3.png; \"exit=$LASTEXITCODE\" }; Get-ChildItem -Recurse output -ErrorAction SilentlyContinue | Select-Obje`
4. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\output\\gen_h3\\grid_overlay.png"}`
5. PowerShell：`{"command": "Get-Content output\\gen_h3\\parts.template.json; $py=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; & $py -I -c \"from PIL import Image; im=Image.open(r'output\\gen_h3\\grid_overlay.png'); im.crop((80,100,380,500)).resize((600,800)).save(r'output\\gen_h3\\_crop_upper.png`
6. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\output\\gen_h3\\_crop_upper.png"}`
7. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\output\\gen_h3\\_crop_head.png"}`
8. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\gen_h3.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"hair_back\", \"polygon\": [[150,45],[230,30],[320,40],[345,110],[365,160],[350,200],[375,280]`
9. PowerShell：`{"command": "& \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\" run gen_h3.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 600000}`
10. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\output\\gen_h3\\layer_preview.png"}`
11. PowerShell：`{"command": "Get-Content output\\gen_h3\\missing_parts.json -Encoding utf8 | Select-Object -First 80", "description": "Show unassigned regions report"}`
12. PowerShell：`{"command": "$f='gen_h3.parts.json'; $t=Get-Content $f -Raw -Encoding utf8\n$t=$t.Replace('[[150,45],[230,30],[320,40],[345,110],[365,160],[350,200],[375,280],[395,360],[395,435],[370,440],[340,400],[150,400],[130,425],[110,420],[105,330],[118,250],[130,180],[125,160],[150,110]]','[[150,45],[230,30]`
13. PowerShell：`{"command": "Get-Content output\\_run.json -Encoding utf8 | Select-Object -First 60; Get-Content output\\gen_h3\\c2s_error.log -Tail 20 -ErrorAction SilentlyContinue", "description": "Show why the rerun stopped"}`
14. PowerShell：`{"command": "$f=(Resolve-Path gen_h3.parts.json).Path; [IO.File]::WriteAllText($f, [IO.File]::ReadAllText($f).TrimStart([char]0xFEFF), (New-Object Text.UTF8Encoding $false))\n& \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\" run gen_h3.png --motion happy | Out-File output\\_run.json -Enco`
15. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\output\\gen_h3\\quality\\round_3\\happy_t2.1_hole_character.png"}`
16. PowerShell：`{"command": "$f=(Resolve-Path gen_h3.parts.json).Path; $t=[IO.File]::ReadAllText($f)\n$t=$t.Replace('\"pivot\": [228,80], \"motion\": 0.6','\"pivot\": [228,80], \"motion\": 0.35').Replace('[[190,455],[252,455],[250,560]','[[190,455],[257,455],[257,580]')\n[IO.File]::WriteAllText($f,$t,(New-Object Te`
17. PowerShell：`{"command": "& \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\" -I -c \"from PIL import Image; im=Image.open(r'output\\gen_h3\\quality\\round_3\\happy_t2.2_hole_character.png'); print(im.size); im.crop((80,60,230,300)).resize((450,720),Image.NEAREST).save(r'output\\gen_h3\\_hole_zoom.pn`
18. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\output\\gen_h3\\_hole_zoom.png"}`
19. PowerShell：`{"command": "$f=(Resolve-Path gen_h3.parts.json).Path; $t=[IO.File]::ReadAllText($f)\n$t=$t.Replace('[400,440],[370,445],[340,400],[150,400],[130,430],[100,425]','[400,445],[370,455],[300,455],[180,455],[130,445],[100,430]')\n[IO.File]::WriteAllText($f,$t,(New-Object Text.UTF8Encoding $false))\n& \"`
20. PowerShell：`{"command": "$py=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; $s=Get-ChildItem -Recurse -Filter visual_report.py -Path .claude,\"D:\\01_Project\\26_char_spine\\scripts\" -ErrorAction SilentlyContinue | Select -First 1; \"script=$($s.FullName)\"; if ($s) { & $py $s.FullName output\\`
21. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\output\\gen_h3\\_gif_strip.png"}`
22. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H3\\sandbox_nl\\output\\gen_h3\\report\\repair_priority.md"}`
23. PowerShell：`{"command": "Remove-Item output\\gen_h3\\_*.png, output\\_run.json -Confirm:$false; Get-ChildItem output\\gen_h3\\spine -Name", "description": "Remove scratch files, list Spine output"}`

## 最後回覆（原文）

角色已拆好骨架，也做了 idle（待機 2.0 秒）和 happy（2.4 秒）兩段動畫，輸出成 Spine JSON。但還**不能算完成**：有 3 個部件被遮住的部分需要人工補畫，而且這台電腦裝的是 Spine 試用版，沒辦法產生 `.spine` 專案檔。

## 驗證結果（依 `validation_report.json`）

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 11 根骨頭，階層順序正確 |
| slots | PASS | 9 個插槽都對應到骨頭和圖片 |
| image_references | PASS | 圖片都存在，尺寸相符 |
| animations | PASS | idle 有 26 個關鍵影格，happy 有 99 個 |
| setup_pose | PASS | 初始姿勢和原圖差異 0.0049 |
| animation_quality | PASS | 逐格檢查破洞、關節縫隙、接觸分離都在門檻內 |
| manual_repairs | **BLOCKED** | 等待人工補畫 hair_back、body、book |
| spine_import | **BLOCKED** | 試用版不能存專案、不能匯出，需要完整版 Spine |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine` 檔，無法驗證匯入後再匯出 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡手動打開確認 |

## 拆成的部件
共 9 個：head、body、arm_l（扶眼鏡的手）、arm_r（抱書的手，設定成和書保持接觸）、leg_l、leg_r，另外拆出 hair_back（後髮）、skirt（裙子）和 book（書）。設定存在圖片旁的 `gen_h3.parts.json`。

我修了三輪：
- 擴大頭髮和雙腿的範圍，沒分到部件的像素從 5.6% 降到 0.03%。
- 把後髮往下延伸到裙子後面，修掉裙擺晃動時出現的破洞。

## 需要人工補畫（依動畫中露出的多寡排序）
1. **hair_back**（高）：76% 被遮住，動畫中最多露出 4.1%，要手繪頭髮紋理。
2. **body**（高）：71% 被遮住，最多露出 2.4%，被手臂、書擋住的身體輪廓要照原圖重畫。
3. **book**（中）：被手擋住 36%，最多露出 1.8%。

另外 leg_l、leg_r、head 是自動補的，各露出 1–2%，建議看一下就好。

補好後執行：
```
c2s prepare --replace hair_back=<修好的.png>
c2s run gen_h3.png
```
每張圖的三格對照在 `output/gen_h3/report/repair_priority.md`。

## 檔案
- Spine JSON：`output/gen_h3/spine/character.json` 和 `images/`
- 預覽：`output/gen_h3/preview/happy_python_simulation_preview.gif`。這是 Python Simulation Preview，不是 Spine 算圖。我看過，動作正常，手和書沒有分開。