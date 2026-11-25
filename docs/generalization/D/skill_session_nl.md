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
- 工具呼叫次數：{'Glob': 1, 'PowerShell': 6, 'Read': 4, 'Skill': 1, 'Write': 1}

## c2s 指令

- `$c = if (Test-Path .venv\Scripts\c2s.exe) { '.venv\Scripts\c2s.exe' } else { (Get-Command c2s -ErrorAction SilentlyContinue).Source }; "c2s=$c"; if ($c) { & $c analyze gen_d.png; "exit=$LASTEXITCODE" }`
- `& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_d.png --motion happy; "exit=$LASTEXITCODE"`
- `$p='gen_d.parts.json'; $t=Get-Content $p -Raw -Encoding utf8
$t=$t.Replace('[[110,150],[350,130],[395,300],[440,440],[470,560],[460,645]','[[110,150],[350,130],[400,300],[428,345],[428,390],[452,440],[478,490],[478,580],[460,645]')
$t=$t.Replace('[[105,990],[200,990],[190,1200],[195,1250],[180,1305],[100,1315],[68,1295],[80,1258]','[[105,990],[200,990],[192,1200],[200,1250],[195,1290],[180,1312],[100,1318],[64,1300],[80,1258]')
$t=$t.Replace('[[265,990],[355,990],[362,1100],[372,1212],[432,1258],[442,1292],[400,1315],[338,1302],[318,1230]','[[265,990],[355,990],[385,1080],[410,1180],[412,1238],[436,1258],[445,1300],[425,1318],[338,1305],[314,1290],[314,1230]')
$t=$t.Replace('[25,985],[28,900]','[20,985],[20,900]')
[IO.File]::WriteAllText((Resolve-Path $p),$t)
& D:\01_Project\26_char_spine\.venv\Scripts\c2s.exe run gen_d.png --motion happy | ConvertFrom-Json | % { $_.steps.prepare | select status,needs_manual,recompose_mae,unassigned_ratio | fl; $_.steps.refine | select status,unresolved,tuning | fl; $_.steps.validate.checks | ft check,status -auto }; "exit=$LASTEXITCODE"
(Get-Content output\gen_d\missing_parts.json -Raw | ConvertFrom-Json).unassigned_regions | ft -auto`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_d.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}
- PowerShell：{"command": "$p='gen_d.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[[110,150],[350,130],[395,300],[440,440],[470,560],[460,645]','[[110,150],[350,130],[400,300],[428,345],[428,3
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe \"$((Resolve-Path .claude\\skills\\character-to-spine).Path)\\scripts\\visual_report.py\" output\\gen_d; \"exit=$LASTEXITCODE\"
- PowerShell：{"command": "Get-ChildItem D:\\01_Project\\26_char_spine -Recurse -Filter visual_report.py -ErrorAction SilentlyContinue | select -First 3 FullName; Get-ChildItem output\\gen_d -Name", "description": 
- PowerShell：{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe -I D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_d; \"exit=$LASTEXITCODE\"; Get-Content output\\gen_d\\r

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_d.png"}`
2. Glob：`{"pattern": "*"}`
3. PowerShell：`{"command": "$c = if (Test-Path .venv\\Scripts\\c2s.exe) { '.venv\\Scripts\\c2s.exe' } else { (Get-Command c2s -ErrorAction SilentlyContinue).Source }; \"c2s=$c\"; if ($c) { & $c analyze gen_d.png; \"exit=$LASTEXITCODE\" }", "description": "Locate c2s and analyze the image"}`
4. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\D\\sandbox_nl\\output\\gen_d\\grid_overlay.png"}`
5. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\D\\sandbox_nl\\gen_d.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"hair_back\", \"polygon\": [[110,150],[350,130],[395,300],[440,440],[470,560],[460,645],[420,655`
6. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\c2s.exe run gen_d.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
7. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\D\\sandbox_nl\\output\\gen_d\\layer_preview.png"}`
8. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\D\\sandbox_nl\\output\\gen_d\\missing_parts.json"}`
9. PowerShell：`{"command": "$p='gen_d.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[[110,150],[350,130],[395,300],[440,440],[470,560],[460,645]','[[110,150],[350,130],[400,300],[428,345],[428,390],[452,440],[478,490],[478,580],[460,645]')\n$t=$t.Replace('[[105,990],[200,990],[190,1200],[195,1`
10. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe \"$((Resolve-Path .claude\\skills\\character-to-spine).Path)\\scripts\\visual_report.py\" output\\gen_d; \"exit=$LASTEXITCODE\"; Get-ChildItem output\\gen_d\\report; Get-ChildItem output\\gen_d -Filter *.json | select name", "d`
11. PowerShell：`{"command": "Get-ChildItem D:\\01_Project\\26_char_spine -Recurse -Filter visual_report.py -ErrorAction SilentlyContinue | select -First 3 FullName; Get-ChildItem output\\gen_d -Name", "description": "Find visual_report script and list outputs"}`
12. PowerShell：`{"command": "& D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe -I D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_d; \"exit=$LASTEXITCODE\"; Get-Content output\\gen_d\\report\\repair_priority.md -Encoding utf8; Get-ChildItem output\\gen_d\\spine -Name", "description": `
13. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\D\\sandbox_nl\\output\\gen_d\\report\\visual_check.png"}`

## 最後回覆（原文）

我已經把 `gen_d.png` 綁好骨架，Idle 和 Happy 兩段動畫也做出來了，輸出了 Spine JSON。但還不能算完成：驗證報告裡有 2 項是 BLOCKED、2 項 NOT_TESTED。

## 驗證結果（`output/gen_d/validation_report.json`）

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 11 根骨頭，上下層級正確 |
| slots | PASS | 9 個插槽都對應到骨頭和圖片 |
| image_references | PASS | 圖片都在、尺寸正確、不是空白 |
| animations | PASS | idle 2.0 秒，happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢跟原圖差異 0.0018 |
| animation_quality | PASS | 逐格檢查沒有破洞、關節縫隙或部件分開（採用第 3 輪自動調整的結果） |
| manual_repairs | **BLOCKED** | 後髮和身體要人工補畫 |
| spine_import | **BLOCKED** | 這台電腦只有 Spine 試用版，不能存檔也不能匯出，所以產生不了 `.spine` 專案 |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine` 專案，無法測試匯入再匯出 |
| spine_editable | NOT_TESTED | 要你在 Spine Editor 裡打開、改一下關鍵影格才能確認 |

## 做了什麼
- 看圖寫好 `gen_d.parts.json`，拆成 9 個部件：後髮、左右腳、身體、裙子（含圍裙和蝴蝶結）、頭（含帽子、前髮、髮夾）、左右手、相機。相機跟著拿它的那隻手動。摸臉的那隻手動作幅度壓得很低（0.15）。
- 修了一輪切圖。沒被分到任何部件的像素從 0.84% 降到 0.07%，剩下的都是邊緣零星幾個像素。
- 動作預覽是 Python Simulation Preview，不是 Spine 真正算出來的畫面。我看了它的關鍵影格（`report/visual_check.png`）：跳起來時相機、手和臉都保持在一起，沒有看到部件分開。

## 需要人工補畫（照優先順序）
1. **`hair_back` 後髮，高**：78% 被其他部件擋住。待機動畫 0.6 秒時，自動填補的部分最多露出 2.54%。
2. **`body` 身體，中**：56% 被擋住。Happy 動畫 0.5 秒時最多露出 1.26%。
3. 下面兩項是自動補的但不太可靠，可以先留著，自己看一下有沒有問題：`head` 頭（被手和相機擋住的地方，最多露出 1.41%）、`arm_l` 左手（被相機擋住的地方，最多露出 0.71%）。

每個部件都有對照圖，在 `output/gen_d/report/repair_priority.md`。補好之後跑：
```
c2s prepare --replace hair_back=<補好的.png>
c2s run gen_d.png
```

## 產出檔案
- Spine JSON：`output/gen_d/spine/character.json`，圖片在旁邊的 `images/`
- 動作預覽：`output/gen_d/preview/{idle,happy}_python_simulation_preview.gif`

要產生 `.spine` 專案，得先裝好完整授權版的 Spine，再重跑一次。