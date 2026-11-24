# D Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_d.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（5 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：2 次
- 工具呼叫次數：{'PowerShell': 6, 'Read': 7, 'Skill': 1, 'Write': 1}

## c2s 指令

- `ls; ls .venv\Scripts\c2s.exe; .\.venv\Scripts\c2s.exe analyze gen_d.png; "exit=$LASTEXITCODE"`
- `(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe`
- `c2s analyze gen_d.png; "exit=$LASTEXITCODE"; ls output -Recurse | select FullName`
- `c2s run gen_d.png --motion happy; "exit=$LASTEXITCODE"`
- `$f='gen_d.parts.json'; $t=[IO.File]::ReadAllText($f)
$r=@{
'[400,300],[420,400]'='[418,300],[432,400]';
'[150,1312],[78,1306],[68,1280]'='[150,1320],[68,1318],[64,1280]';
'[378,1208],[432,1258],[442,1292],[400,1312],[328,1302]'='[404,1200],[434,1256],[446,1300],[440,1318],[400,1320],[326,1316]';
'[298,1100]]'='[266,1100]]';
'[442,650],[405,705],[362,705]'='[452,650],[450,705],[406,738],[362,738]';
'[68,762],[52,700]'='[22,880],[40,762],[48,700]';
'[22,960],[38,880],'='[16,962],';
'[108,150],[150,58]'='[104,150],[104,104],[150,58]'}
foreach($k in $r.Keys){ if(-not $t.Contains($k)){"MISS $k"}; $t=$t.Replace($k,$r[$k]) }
[IO.File]::WriteAllText($f,$t,(New-Object Text.UTF8Encoding $false))
c2s run gen_d.png --motion happy | ConvertFrom-Json | % { $_.steps.prepare | select status,needs_manual,unassigned_ratio,recompose_mae; $_.steps.refine | select status,unresolved,downgraded_to_needs_manual; $_.steps.validate.checks | ft check,status,detail -Wrap }; "exit=$LASTEXITCODE"`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate c2s executable"}
- PowerShell：{"command": "$s=(Get-ChildItem -Recurse -Filter visual_report.py D:\\01_Project\\26_char_spine\\scripts,.claude -ErrorAction SilentlyContinue | select -First 1).FullName; $s; D:\\01_Project\\26_char_s

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_d.png"}`
2. PowerShell：`{"command": "ls; ls .venv\\Scripts\\c2s.exe; .\\.venv\\Scripts\\c2s.exe analyze gen_d.png; \"exit=$LASTEXITCODE\"", "description": "List files and run c2s analyze"}`
3. PowerShell：`{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Test-Path D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe", "description": "Locate c2s executable"}`
4. PowerShell：`{"command": "c2s analyze gen_d.png; \"exit=$LASTEXITCODE\"; ls output -Recurse | select FullName", "description": "Run c2s analyze on the image"}`
5. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\grid_overlay.png"}`
6. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\parts.template.json"}`
7. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\gen_d.parts.json", "content": "{\n  \"version\": 1,\n  \"image\": \"gen_d.png\",\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"hair_back\", \"z\": 0, \"parent\": \"head\", \"role\": \"hair\", `
8. PowerShell：`{"command": "c2s run gen_d.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
9. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\layer_preview.png"}`
10. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\missing_parts.json"}`
11. PowerShell：`{"command": "$f='gen_d.parts.json'; $t=[IO.File]::ReadAllText($f)\n$r=@{\n'[400,300],[420,400]'='[418,300],[432,400]';\n'[150,1312],[78,1306],[68,1280]'='[150,1320],[68,1318],[64,1280]';\n'[378,1208],[432,1258],[442,1292],[400,1312],[328,1302]'='[404,1200],[434,1256],[446,1300],[440,1318],[400,1320]`
12. PowerShell：`{"command": "$s=(Get-ChildItem -Recurse -Filter visual_report.py D:\\01_Project\\26_char_spine\\scripts,.claude -ErrorAction SilentlyContinue | select -First 1).FullName; $s; D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe $s output\\gen_d; \"exit=$LASTEXITCODE\"; ls output\\gen_d\\report,`
13. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\layer_preview.png"}`
14. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\report\\repair_priority.md"}`
15. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\D\\sandbox_nl\\output\\gen_d\\report\\visual_check.png"}`

## 最後回覆（原文）

`gen_d.png` 已轉成 Spine JSON 骨架加上 Idle／Happy 兩段動畫，但**還不算完成**：有一個部件要人工補畫，`.spine` 專案檔也做不出來（偵測到的是 Spine 試用版）。

## 驗證報告（`validation_report.json`）

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 10 根骨頭，上下層順序正確 |
| slots | PASS | 8 個插槽都對應到骨頭與圖片 |
| image_references | PASS | 圖片都存在、尺寸正確、不是空白 |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢與原圖的差異是 0.0025 |
| manual_repairs | **BLOCKED** | `hair_back` 要人工補畫 |
| animation_quality | PASS | 逐格檢查破洞、關節縫隙、手和相機分開等問題，都在門檻內 |
| spine_import | **BLOCKED** | 偵測到的是 Spine 試用版，不能存專案也不能匯出，產生不了 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法驗證匯入再匯出 |
| spine_editable | NOT_TESTED | 要你在 Spine Editor 裡打開並改一個關鍵影格才能確認 |

## 部件拆法
- **必要部件：** 頭、身體（含圍裙、背後的蝴蝶結、裙子）、兩隻手臂、兩條腿。
- **額外部件：** 背後的長髮 `hair_back`、相機 `camera`。
- 兩隻手都設定成要一直碰著相機，動起來手不會離開相機。

切圖修了一輪：照 `missing_parts.json` 列出的位置，把裙子左邊、蝴蝶結、右腿內側、鞋底、頭頂和右側頭髮的範圍加大。修完後沒被分到任何部件的像素從 1.19% 降到 0.12%。

## 要人工補畫的部件（依優先順序）
1. **`hair_back`（高）**：背後長髮有 77% 被身體、頭、手臂擋住，自動補出來的只是草稿。happy 動畫裡最多露出 2.75%（在 t=1.8 秒）。被擋住的頭髮外形要照原圖重畫，紋理也要手繪。
2. 下面四個是自動補的，露出量在門檻內，但建議你自己看一下：`camera` 1.97%、`head` 1.86%、`body` 1.37%、`arm_l` 1.21%。

補畫完成後執行：
```
c2s prepare --replace hair_back=<修好的.png>
c2s run gen_d.png --motion happy
```

預覽 GIF 是 Python Simulation Preview，不是 Spine 算圖。我看了關鍵影格的總覽圖，雙手一直抓著相機，沒看到肢體轉錯方向或頭髮亂甩。GIF 本身沒有開來看。

文件都在 `output\gen_d\`：
- 補畫清單和三格對照圖：`report\repair_priority.md`
- 預覽 GIF：`preview\happy_python_simulation_preview.gif`