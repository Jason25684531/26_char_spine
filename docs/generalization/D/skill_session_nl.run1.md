# D Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：examples/generalization/D/gen_d.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開：否
- 觸發後執行 c2s：是（4 次）
- 讀取禁止路徑：0 次
- 工具呼叫次數：{'PowerShell': 4, 'Read': 6, 'Skill': 1, 'Write': 1}

## c2s 指令

- `ls examples/generalization/D; .venv\Scripts\c2s.exe analyze examples/generalization/D/gen_d.png; "exit=$LASTEXITCODE"`
- `.venv\Scripts\c2s.exe run examples/generalization/D/gen_d.png --motion happy; "exit=$LASTEXITCODE"`
- `$p='examples/generalization/D/gen_d.parts.json'; $t=Get-Content $p -Raw -Encoding utf8
$t=$t.Replace('[360, 250], [400, 330]','[360, 250], [428, 305], [428, 385], [400, 330]').Replace('[85, 650], [58, 600], [80, 520], [100, 400]','[85, 650], [52, 600], [52, 540], [60, 460], [100, 400]')
$t=$t.Replace('[[105, 990], [192, 990], [186, 1210], [196, 1290]','[[100, 990], [205, 990], [198, 1100], [192, 1210], [200, 1290]')
$t=$t.Replace('[[268, 990], [352, 990], [350, 1100], [360, 1215]','[[262, 990], [358, 990], [372, 1100], [398, 1215]')
$t=$t.Replace('[400, 560], [440, 660], [410, 700], [360, 700], [365, 750], [400, 800], [426, 940], [420, 992], [340, 1012], [250, 1022], [150, 1012], [40, 992], [22, 950], [55, 800]','[400, 560], [442, 660], [415, 740], [365, 748], [372, 760], [400, 800], [428, 940], [424, 996], [400, 1006], [350, 1022], [290, 1045], [250, 1060], [200, 1048], [110, 1024], [60, 1024], [30, 996], [20, 950], [30, 780]')
[IO.File]::WriteAllText((Resolve-Path $p),$t)
.venv\Scripts\c2s.exe run examples/generalization/D/gen_d.png --motion happy | Out-Null; "exit=$LASTEXITCODE"
.venv\Scripts\python.exe -c "import json;d=json.load(open('output/gen_d/missing_parts.json',encoding='utf8'));print(d['unassigned_ratio'],[ (r['bbox'],r['area'],r['nearest_part']) for r in d['unassigned_regions'][:6]],[m['name'] for m in d['needs_manual']])"`
- `$p='examples/generalization/D/gen_d.parts.json'; $t=Get-Content $p -Raw -Encoding utf8
$t=$t.Replace('[428, 385], [400, 330], [440, 420]','[428, 385], [440, 420]')
[IO.File]::WriteAllText((Resolve-Path $p),$t)
.venv\Scripts\c2s.exe run examples/generalization/D/gen_d.png --motion happy | Out-Null; "exit=$LASTEXITCODE"
.venv\Scripts\python.exe -c "import json;d=json.load(open('output/gen_d/missing_parts.json',encoding='utf8'));print(d['unassigned_ratio'],[m['name'] for m in d['needs_manual']]);v=json.load(open('output/gen_d/validation_report.json',encoding='utf8'));[print(c['check'],c['status'],c['detail']) for c in v['checks']];q=json.load(open('output/gen_d/quality/quality_report.json',encoding='utf8'));print('unresolved',q.get('unresolved'))"
.venv\Scripts\python.exe scripts/visual_report.py output/gen_d`

## 禁止路徑

- 無

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "examples/generalization/D/gen_d.png"}`
2. PowerShell：`{"command": "ls examples/generalization/D; .venv\\Scripts\\c2s.exe analyze examples/generalization/D/gen_d.png; \"exit=$LASTEXITCODE\"", "description": "Analyze image D with c2s"}`
3. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\grid_overlay.png"}`
4. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\C\\gen_c.parts.json"}`
5. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\D\\gen_d.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"hair_back\", \"polygon\": [[100, 130], [150, 90], [300, 70], [350, 150], [360, 250], [400, 330], [440, 4`
6. PowerShell：`{"command": ".venv\\Scripts\\c2s.exe run examples/generalization/D/gen_d.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline on image D", "timeout": 600000}`
7. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\layer_preview.png"}`
8. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\missing_parts.json"}`
9. PowerShell：`{"command": "$p='examples/generalization/D/gen_d.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[360, 250], [400, 330]','[360, 250], [428, 305], [428, 385], [400, 330]').Replace('[85, 650], [58, 600], [80, 520], [100, 400]','[85, 650], [52, 600], [52, 540], [60, 460], [100, 400]'`
10. PowerShell：`{"command": "$p='examples/generalization/D/gen_d.parts.json'; $t=Get-Content $p -Raw -Encoding utf8\n$t=$t.Replace('[428, 385], [400, 330], [440, 420]','[428, 385], [440, 420]')\n[IO.File]::WriteAllText((Resolve-Path $p),$t)\n.venv\\Scripts\\c2s.exe run examples/generalization/D/gen_d.png --motion h`
11. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\report\\visual_check.png"}`
12. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\report\\repair_priority.md"}`

## 最後回覆（原文）

`gen_d.png` 的 Spine 動畫做好了，有 idle 和 happy 兩段。不過還不能算完成：髮後層和身體兩個部件要等人工補畫，`.spine` 專案也因為只有 Spine 試用版而做不出來。

## 驗證結果（`output/gen_d/validation_report.json`）

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 11 根骨頭，階層順序正確 |
| slots | PASS | 9 個插槽都對應到骨頭和附件 |
| image_references | PASS | 附件圖片都在，尺寸相符，不是空白 |
| animations | PASS | idle 2.0 秒、26 個關鍵影格；happy 2.4 秒、101 個關鍵影格 |
| setup_pose | PASS | 初始姿勢和原圖差 0.0016 |
| manual_repairs | **BLOCKED** | 等人工補畫：`hair_back`、`body` |
| animation_quality | PASS | 破洞、關節縫隙、接觸分離、穿插都在門檻內，沒有未解決的項目 |
| spine_import | **BLOCKED** | 偵測到的是 Spine 試用版，不能產生 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法往返驗證 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡人工開檔確認 |

## 這次做了什麼
- 在圖片旁寫了 `examples/generalization/D/gen_d.parts.json`，共 9 個部件：head、body、arm_l、arm_r、leg_l、leg_r、hair_back、skirt（含圍裙和蝴蝶結）、camera。
- 相機設成道具，兩隻手都宣告跟它接觸，拍照時手不會和相機分開。
- 照漏切區域報告修了兩輪：加大右腿、裙擺下緣和兩側頭髮的範圍，沒分到部件的像素從 2.69% 降到 0.34%。
- 自動品質修正跑了 3 輪，採用第 3 輪。happy 裡手臂幅度降到 0.125，頭髮降到 0.25。

## 待人工補畫（依優先順序，詳見 `output/gen_d/report/repair_priority.md`）
1. **`hair_back`（高）**：約 75% 被遮住，動畫中最多露出 2.71%（happy t=0.4s），被遮住的輪廓要對照原圖重畫。
2. **`body`（中）**：約 47% 被遮住，最多露出 1.72%（happy t=1.8s）。

另外有幾個部件是自動補的，但結果不可靠，建議目視確認：head 1.9%、camera 1.9%、arm_r 1.0%、skirt 0.2%。

補好後執行 `c2s prepare --replace <部件>=<修好的.png>`，再執行 `c2s run examples/generalization/D/gen_d.png`。

預覽在 `output/gen_d/preview/*_python_simulation_preview.gif`。這是 Python Simulation Preview，不是 Spine 算圖。總覽圖是 `output/gen_d/report/visual_check.png`。

`gen_d.parts.json` 還沒 commit，要的話告訴我。