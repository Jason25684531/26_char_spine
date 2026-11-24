# A Skill 實測（/character-to-spine）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`/character-to-spine gen_a.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：否
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：是
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（4 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：5 次
- 工具呼叫次數：{'Bash': 2, 'PowerShell': 6, 'Read': 7}

## c2s 指令

- `ls; Get-Command c2s -ErrorAction SilentlyContinue | Select-Object Source; Test-Path ..\..\..\..\.venv\Scripts\c2s.exe`
- `c2s analyze gen_a.png; "EXIT=$LASTEXITCODE"; ls; ls output -Recurse -Depth 1`
- `cat > "D:/01_Project/26_char_spine/output/generalization/A/sandbox_slash/gen_a.parts.json" <<'EOF'
{
  "version": 1,
  "preset": "humanoid-chibi",
  "parts": [
    {"name": "braid_l", "polygon": [[240,470],[352,470],[352,560],[335,640],[310,700],[302,765],[248,765],[252,680],[262,600],[245,540]], "z": 0, "parent": "head", "role": "hair", "pivot": [300,500], "motion": 0.6},
    {"name": "braid_r", "polygon": [[615,460],[722,460],[718,560],[738,680],[738,765],[675,765],[668,680],[642,600],[625,540]], "z": 1, "parent": "head", "role": "hair", "pivot": [670,500], "motion": 0.6},
    {"name": "leg_l", "polygon": [[392,765],[478,765],[492,830],[492,890],[475,935],[415,935],[405,880],[398,830]], "z": 2, "pivot": [440,790]},
    {"name": "leg_r", "polygon": [[476,770],[585,770],[588,840],[582,890],[578,945],[485,950],[476,885],[482,830]], "z": 3, "pivot": [530,795]},
    {"name": "body", "polygon": [[392,540],[480,540],[548,555],[582,598],[565,650],[560,690],[592,728],[618,792],[562,808],[450,815],[350,798],[350,740],[372,690],[382,640],[370,602]], "z": 4, "pivot": [440,700]},
    {"name": "head", "polygon": [[165,140],[230,78],[330,52],[640,52],[805,118],[810,330],[752,420],[705,500],[645,548],[560,562],[480,570],[400,570],[330,548],[270,530],[232,470],[200,380],[163,300]], "z": 5, "pivot": [437,558]},
    {"name": "arm_l", "polygon": [[368,585],[410,585],[408,640],[400,700],[392,742],[378,762],[342,752],[348,700],[362,650]], "z": 6, "pivot": [392,600]},
    {"name": "arm_r", "polygon": [[535,560],[578,575],[595,610],[612,650],[628,700],[648,740],[642,770],[602,772],[582,730],[562,700],[548,660],[536,620]], "z": 7, "pivot": [552,585]}
  ]
}
EOF
cd "D:/01_Project/26_char_spine/output/generalization/A/sandbox_slash" && c2s run gen_a.png --motion happy > output/run1.log 2>&1; echo EXIT=$?; tail -c 3000 output/run1.log`
- `cd "D:/01_Project/26_char_spine/output/generalization/A/sandbox_slash" && cp gen_a.parts.json output/gen_a.parts.run1.json && cat > gen_a.parts.json <<'EOF'
{
  "version": 1,
  "preset": "humanoid-chibi",
  "parts": [
    {"name": "braid_l", "polygon": [[240,470],[352,470],[368,555],[365,580],[335,640],[310,700],[302,765],[248,765],[252,680],[262,600],[245,540]], "z": 0, "parent": "head", "role": "hair", "pivot": [300,500], "motion": 0.6},
    {"name": "braid_r", "polygon": [[615,460],[722,460],[718,560],[738,680],[738,765],[675,765],[668,680],[642,655],[608,650],[608,548]], "z": 1, "parent": "head", "role": "hair", "pivot": [670,500], "motion": 0.6},
    {"name": "leg_l", "polygon": [[392,765],[478,765],[492,830],[492,890],[488,945],[415,940],[405,880],[398,830]], "z": 2, "pivot": [440,790]},
    {"name": "leg_r", "polygon": [[476,770],[585,770],[588,840],[582,890],[578,945],[485,950],[476,885],[482,830]], "z": 3, "pivot": [530,795]},
    {"name": "body", "polygon": [[392,540],[480,540],[572,556],[582,598],[565,650],[560,690],[592,728],[632,782],[598,826],[562,812],[450,815],[350,798],[350,740],[372,690],[382,640],[370,602]], "z": 4, "pivot": [440,700]},
    {"name": "head", "polygon": [[165,140],[230,78],[330,52],[640,52],[700,58],[772,64],[805,118],[810,330],[752,420],[705,500],[645,548],[560,562],[480,570],[400,570],[330,548],[270,535],[222,528],[198,420],[160,385],[160,300]], "z": 5, "pivot": [437,558]},
    {"name": "arm_l", "polygon": [[368,585],[410,585],[408,640],[400,700],[392,742],[378,762],[342,752],[348,700],[362,650]], "z": 6, "pivot": [392,600]},
    {"name": "arm_r", "polygon": [[535,560],[578,575],[595,610],[612,650],[628,700],[648,740],[642,770],[602,772],[582,730],[562,700],[548,660],[536,620]], "z": 7, "pivot": [552,585]}
  ]
}
EOF
c2s run gen_a.png --motion happy > output/run2.log 2>&1; echo EXIT=$?; .venv=; "D:/01_Project/26_char_spine/.venv/Scripts/python.exe" -c "
import json;m=json.load(open('output/gen_a/missing_parts.json',encoding='utf-8'));print(m['unassigned_ratio'],[(r['bbox'],r['area'],r['nearest_part']) for r in m['unassigned_regions']]);print([n['name'] for n in m['needs_manual']])
v=json.load(open('output/gen_a/validation_report.json',encoding='utf-8'));[print(c['check'],c['status'],c['detail']) for c in v['checks']]
q=json.load(open('output/gen_a/quality/quality_report.json',encoding='utf-8'));print('unresolved',q.get('unresolved'))"`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "ls; Get-Command c2s -ErrorAction SilentlyContinue | Select-Object Source; Test-Path ..\\..\\..\\..\\.venv\\Scripts\\c2s.exe", "description": "List sandbox and locate c2s"}
- PowerShell：{"command": "$py='D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe'; & $py -c \"from PIL import Image; im=Image.open(r'output\\gen_a\\grid_overlay.png'); im.crop((300,520,700,950)).resize((80
- Bash：{"command": "cd \"D:/01_Project/26_char_spine/output/generalization/A/sandbox_slash\" && cp gen_a.parts.json output/gen_a.parts.run1.json && cat > gen_a.parts.json <<'EOF'\n{\n  \"version\": 1,\n  \"p
- PowerShell：{"command": "& 'D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe' -c \"from PIL import Image,ImageSequence; g=Image.open(r'output\\gen_a\\preview\\happy_python_simulation_preview.gif'); fr=[f
- PowerShell：{"command": "& 'D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe' D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_a; Get-Content output\\gen_a\\report\\repair_priority.md

## 全部工具呼叫

1. PowerShell：`{"command": "ls; Get-Command c2s -ErrorAction SilentlyContinue | Select-Object Source; Test-Path ..\\..\\..\\..\\.venv\\Scripts\\c2s.exe", "description": "List sandbox and locate c2s"}`
2. PowerShell：`{"command": "c2s analyze gen_a.png; \"EXIT=$LASTEXITCODE\"; ls; ls output -Recurse -Depth 1", "description": "Run c2s analyze on the image"}`
3. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_slash\\output\\gen_a\\grid_overlay.png"}`
4. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_slash\\output\\gen_a\\parts.template.json"}`
5. PowerShell：`{"command": "$py='D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe'; & $py -c \"from PIL import Image; im=Image.open(r'output\\gen_a\\grid_overlay.png'); im.crop((300,520,700,950)).resize((800,860)).save(r'$env:TEMP\\a_low.png'); im.crop((150,50,820,560)).save(r'$env:TEMP\\a_up.png')\"; \"$`
6. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\a_low.png"}`
7. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\a_up.png"}`
8. Bash：`{"command": "cat > \"D:/01_Project/26_char_spine/output/generalization/A/sandbox_slash/gen_a.parts.json\" <<'EOF'\n{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"braid_l\", \"polygon\": [[240,470],[352,470],[352,560],[335,640],[310,700],[302,765],[248,765],`
9. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_slash\\output\\gen_a\\layer_preview.png"}`
10. PowerShell：`{"command": "Get-Content output\\gen_a\\missing_parts.json -Raw", "description": "Show missing parts report"}`
11. Bash：`{"command": "cd \"D:/01_Project/26_char_spine/output/generalization/A/sandbox_slash\" && cp gen_a.parts.json output/gen_a.parts.run1.json && cat > gen_a.parts.json <<'EOF'\n{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"braid_l\", \"polygon\": [[240,470],[3`
12. PowerShell：`{"command": "& 'D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe' -c \"from PIL import Image,ImageSequence; g=Image.open(r'output\\gen_a\\preview\\happy_python_simulation_preview.gif'); fr=[f.convert('RGB') for f in ImageSequence.Iterator(g)]; n=len(fr); pick=[fr[i*n//6] for i in range(6)];`
13. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\generalization\\A\\sandbox_slash\\output\\gen_a\\layer_preview.png"}`
14. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\a_gif.png"}`
15. PowerShell：`{"command": "& 'D:\\01_Project\\26_char_spine\\.venv\\Scripts\\python.exe' D:\\01_Project\\26_char_spine\\scripts\\visual_report.py output\\gen_a; Get-Content output\\gen_a\\report\\repair_priority.md -Encoding utf8", "description": "Generate repair priority report"}`

## 最後回覆（原文）

`gen_a.png` 的流程跑完了，但**還不算完成**：有 4 個部件要人工補畫，`.spine` 專案也做不出來，因為這台只有 Spine 試用版。

## 做了什麼
- 依格線圖寫了 `gen_a.parts.json`（放在圖片旁），共 8 個部件：必要的 6 個，加上兩條辮子 `braid_l`、`braid_r`（跟著頭動，擺幅 0.6）。帽子和帽上的裝飾都併在 `head` 裡。
- 第一輪跑完有 0.67% 的像素沒分配到部件（帽子上的棒子、左邊的毛球、右邊辮子根部、裙擺邊緣）。擴大多邊形後重跑，降到 0.01%。從 `layer_preview.png` 看，拼回去的圖和原圖一致。
- 動畫品質自我修正採用第 3 輪：自動把 `arm_l` 調到 0.125、`body` 調到 0.25，沒有未解決的影格。
- 我從 Python Simulation Preview（不是 Spine 算圖）抽了 6 格目視：右手揮動、身體跳動、辮子跟著擺，沒看到肢體轉錯方向。

## validation_report.json
| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 10 根骨頭，階層正確 |
| slots | PASS | 8 個插槽 |
| image_references | PASS | |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢和原圖差 0.0020 |
| manual_repairs | **BLOCKED** | braid_l、braid_r、leg_l、body 等待人工補畫 |
| animation_quality | PASS | 有附註：leg_r 的自動補圖露出 1.9%（在門檻內），建議目視確認 |
| spine_import | **BLOCKED** | 偵測到的是 Spine 試用版，不能產生 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine` 可以驗 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡人工確認 |

## 待人工補畫（依動畫露出量排序）
1. **`body`（高，最多露出 12.58%）**：被頭和兩手擋住的身體要補畫。被擋住的輪廓佔 56%，自動補圖補不出外形，要對照原圖重畫。
2. **`braid_l`（中，1.21%）**：被頭擋住的辮子根部。
3. **`leg_l`（中，1.17%）**：被右腿和裙子擋住的部分。
4. **`braid_r`（中，0.89%）**：被頭擋住的辮子根部。
5. `leg_r` 沒有列入必修，但它的自動補圖不可靠（露出 1.87%），建議順便補。

目前這些區域的自動填補都只是草稿，不能當作已修好。每個部件的三格對照圖在 `output/gen_a/report/repair_priority.md`。

補好一個部件後，執行 `c2s prepare --replace <部件>=<修好的.png>`，再執行 `c2s run gen_a.png`。要拿到 `.spine` 專案，得有完整版 Spine。

`output/` 裡另外有兩輪的執行紀錄和第一輪 parts.json 的備份 `gen_a.parts.run1.json`，可以刪除。