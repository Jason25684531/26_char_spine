# D Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_d.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（3 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：5 次
- 工具呼叫次數：{'PowerShell': 7, 'Read': 9, 'Skill': 1, 'Write': 1}

## c2s 指令

- `$c = "D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe"; Test-Path $c; (Get-Command c2s -ErrorAction SilentlyContinue).Source; & $c analyze gen_d.png; "exit=$LASTEXITCODE"`
- `& "D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe" run gen_d.png --motion happy; "exit=$LASTEXITCODE"`
- `$f="gen_d.parts.json"; $t=[IO.File]::ReadAllText($f)
$t=$t.Replace('[[100,160],[150,120],[300,120],[360,180],[400,300],[410,330],[430,420],[460,480],[472,560],[462,645],[420,645],[380,560],[300,500],[150,500],[115,560],[95,655],[58,625],[68,540],[100,450],[108,330]]','[[100,160],[150,120],[300,120],[360,180],[405,292],[428,350],[442,420],[476,515],[476,560],[464,648],[420,652],[392,602],[335,602],[300,500],[150,500],[115,560],[95,655],[54,628],[52,540],[100,450],[100,330]]')
$t=$t.Replace('[442,668],[412,705],[360,705],[372,800],[402,880],[430,950],[420,1002]','[442,668],[412,708],[400,740],[412,790],[424,860],[436,945],[422,1004]')
$t=$t.Replace('[[262,985],[352,985],[357,1100],[352,1208],[402,1238],[442,1280],[432,1308],[370,1312],[318,1292],[313,1220],[288,1100]]','[[262,985],[360,985],[378,1050],[398,1150],[404,1215],[424,1240],[446,1282],[434,1316],[370,1316],[318,1292],[313,1220],[288,1100]]')
[IO.File]::WriteAllText($f,$t); & "D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe" run gen_d.png --motion happy | Out-Null; "exit=$LASTEXITCODE"
Get-Content output\gen_d\validation_report.json -Raw; Get-Content output\gen_d\missing_parts.json -Raw | ConvertFrom-Json | % { $_.unassigned_ratio; $_.unassigned_regions | select -First 4 | ConvertTo-Json -Compress }`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "$c = \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\"; Test-Path $c; (Get-Command c2s -ErrorAction SilentlyContinue).Source; & $c analyze gen_d.png; \"exit=$LASTEXITCODE\"", "de
- PowerShell：{"command": "$py=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; & $py -I -c \"from PIL import Image; im=Image.open(r'output\\gen_d\\grid_overlay.png'); im.crop((0,200,500,600)).resize(
- PowerShell：{"command": "& \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\" run gen_d.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run the full c2s pipeline", "timeout": 600000}
- PowerShell：{"command": "$f=\"gen_d.parts.json\"; $t=[IO.File]::ReadAllText($f)\n$t=$t.Replace('[[100,160],[150,120],[300,120],[360,180],[400,300],[410,330],[430,420],[460,480],[472,560],[462,645],[420,645],[380,
- PowerShell：{"command": "$py=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; & $py \"D:\\01_Project\\26_char_spine\\scripts\\visual_report.py\" output\\gen_d | Out-Null; \"exit=$LASTEXITCODE\"; & $

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_d.png"}`
2. PowerShell：`{"command": "Get-ChildItem -Force | Select-Object Mode,Length,Name", "description": "List sandbox directory contents"}`
3. PowerShell：`{"command": "$c = \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\"; Test-Path $c; (Get-Command c2s -ErrorAction SilentlyContinue).Source; & $c analyze gen_d.png; \"exit=$LASTEXITCODE\"", "description": "Locate c2s and analyze the image"}`
4. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\grid_overlay.png"}`
5. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\parts.template.json"}`
6. PowerShell：`{"command": "$py=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; & $py -I -c \"from PIL import Image; im=Image.open(r'output\\gen_d\\grid_overlay.png'); im.crop((0,200,500,600)).resize((1000,800)).save(r'output\\gen_d\\_zoom_top.png'); im.crop((0,500,500,1100)).save(r'output\\gen_d\\_`
7. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\_zoom_top.png"}`
8. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\_zoom_mid.png"}`
9. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\gen_d.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"hair_back\", \"z\": 0, \"parent\": \"head\", \"role\": \"hair\", \"pivot\": [240, 190], \"moti`
10. PowerShell：`{"command": "& \"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe\" run gen_d.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run the full c2s pipeline", "timeout": 600000}`
11. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\layer_preview.png"}`
12. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\quality\\round_3\\happy_t0.4_hole_character.png"}`
13. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\missing_parts.json"}`
14. PowerShell：`{"command": "$f=\"gen_d.parts.json\"; $t=[IO.File]::ReadAllText($f)\n$t=$t.Replace('[[100,160],[150,120],[300,120],[360,180],[400,300],[410,330],[430,420],[460,480],[472,560],[462,645],[420,645],[380,560],[300,500],[150,500],[115,560],[95,655],[58,625],[68,540],[100,450],[108,330]]','[[100,160],[150`
15. PowerShell：`{"command": "$py=\"D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe\"; & $py \"D:\\01_Project\\26_char_spine\\scripts\\visual_report.py\" output\\gen_d | Out-Null; \"exit=$LASTEXITCODE\"; & $py -I -c \"from PIL import Image; g=Image.open(r'output\\gen_d\\preview\\happy_python_simulation_pre`
16. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\_gif_strip.png"}`
17. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\report\\repair_priority.md"}`
18. PowerShell：`{"command": "Remove-Item output\\gen_d\\_zoom_top.png,output\\gen_d\\_zoom_mid.png,output\\gen_d\\_gif_strip.png -Confirm:$false; Get-ChildItem output\\gen_d -Name | Select-String \"spine|json$|atlas\"", "description": "Remove temp images and list outputs"}`

## 最後回覆（原文）

gen_d.png 已經做成 Spine JSON 骨架動畫（idle 與 happy 兩段），但整體狀態還是 **BLOCKED**，還不算完成：有兩個部件要人工補畫，`.spine` 專案檔也做不出來。

**我做了什麼**
- 看圖寫好 `gen_d.parts.json`，放在原圖旁，共 9 個部件：必要的 head、body、arm_l、arm_r、leg_l、leg_r，加上 hair_back（後髮）、skirt（裙擺連圍裙蝴蝶結）、camera（相機，跟著左手動）。
- 跑完整流程兩次。第二次把右腿外側、右側後髮、裙擺右緣補進部件範圍，沒分到部件的像素從 1.74% 降到 0.05%。自動修正把動作幅度調小了（右手 0.125、左手 0.25、頭／頭髮／裙擺 0.5）。
- 產出放在 `output/gen_d/`：Spine JSON 在 `spine/`；動態預覽在 `preview/happy_python_simulation_preview.gif`，這是 Python Simulation Preview，不是 Spine 算圖。我看了預覽的幾格，沒看到肢體轉錯方向或部件分離。

**驗證結果（validation_report.json）**

| 檢查項目 | 狀態 |
|---|---|
| bones | PASS |
| slots | PASS |
| image_references | PASS |
| animations | PASS |
| setup_pose | PASS（和原圖差異 0.0017） |
| animation_quality | PASS（第一次有破洞，修正後通過） |
| manual_repairs | BLOCKED：等待補畫 body、hair_back |
| spine_import | BLOCKED：這台只有 Spine 試用版，不能存檔也不能匯出，做不出 `.spine` |
| spine_roundtrip | NOT_TESTED（沒有 `.spine`） |
| spine_editable | NOT_TESTED（要在 Spine Editor 裡人工確認） |

**需要人工補畫的部件**（詳見 `output/gen_d/report/repair_priority.md`，附對照圖）
1. **body（高）**：約 67% 被裙擺、頭、雙手、相機擋住，動畫中最多露出 3.53%。被擋住的輪廓要照原圖重畫。
2. **hair_back（高）**：約 79% 被擋住，動畫中最多露出 2.88%。

下面三個自動補得不太可靠，但露出量都低於品質檢查的門檻，建議看一下就好：head 1.53%（相機和右手後面的臉）、camera 0.81%、arm_l 0.32%。

補好之後，把圖匯回再重跑：
```
c2s prepare --replace body=<修好的.png>
c2s run gen_d.png
```

要拿到 `.spine` 專案檔，得在裝有完整版 Spine 的機器上匯入 `spine/` 裡的 JSON。