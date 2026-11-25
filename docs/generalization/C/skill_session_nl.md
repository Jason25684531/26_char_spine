# C Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_c.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（6 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：1 次
- 工具呼叫次數：{'PowerShell': 6, 'Read': 6, 'Skill': 1, 'Write': 2}

## c2s 指令

- `ls; ls .venv\Scripts\c2s.exe; .venv\Scripts\c2s.exe analyze gen_c.png; "exit=$LASTEXITCODE"`
- `(Get-Command c2s -ErrorAction SilentlyContinue).Source; Get-ChildItem -Recurse -Force .claude | Select-Object -ExpandProperty FullName`
- `c2s analyze gen_c.png; "exit=$LASTEXITCODE"; Get-ChildItem -Recurse output | Select-Object -ExpandProperty FullName`
- `c2s run gen_c.png --motion happy; "exit=$LASTEXITCODE"`
- `c2s run gen_c.png --motion happy | Out-Null; "exit=$LASTEXITCODE"; Get-Content output\gen_c\validation_report.json -Raw -Encoding utf8; Get-Content output\gen_c\missing_parts.json -Raw -Encoding utf8`
- `$s = Get-ChildItem -Recurse -Filter visual_report.py -Path .claude, (Split-Path (Split-Path (Get-Command c2s).Source)) -ErrorAction SilentlyContinue | Select-Object -First 1; if (-not $s) { $s = Get-ChildItem -Recurse -Filter visual_report.py D:\01_Project\26_char_spine\scripts -ErrorAction SilentlyContinue | Select-Object -First 1 }; $s.FullName; & D:\01_Project\26_char_spine\.venv\Scripts\python.exe $s.FullName output\gen_c; "exit=$LASTEXITCODE"; Get-Content output\gen_c\report\repair_priority.md -Encoding utf8`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "$s = Get-ChildItem -Recurse -Filter visual_report.py -Path .claude, (Split-Path (Split-Path (Get-Command c2s).Source)) -ErrorAction SilentlyContinue | Select-Object -First 1; if (-not $s)

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_c.png"}`
2. PowerShell：`{"command": "ls; ls .venv\\Scripts\\c2s.exe; .venv\\Scripts\\c2s.exe analyze gen_c.png; \"exit=$LASTEXITCODE\"", "description": "List files and run c2s analyze"}`
3. PowerShell：`{"command": "(Get-Command c2s -ErrorAction SilentlyContinue).Source; Get-ChildItem -Recurse -Force .claude | Select-Object -ExpandProperty FullName", "description": "Locate c2s on PATH and list skill files"}`
4. PowerShell：`{"command": "c2s analyze gen_c.png; \"exit=$LASTEXITCODE\"; Get-ChildItem -Recurse output | Select-Object -ExpandProperty FullName", "description": "Run c2s analyze on the image"}`
5. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\C\\sandbox_nl\\output\\gen_c\\grid_overlay.png"}`
6. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\C\\sandbox_nl\\output\\gen_c\\parts.template.json"}`
7. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\C\\sandbox_nl\\gen_c.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"absent\": [\"leg_l\", \"leg_r\"],\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[40,790],[100,775],[250,770],[40`
8. PowerShell：`{"command": "c2s run gen_c.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 600000}`
9. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\C\\sandbox_nl\\output\\gen_c\\layer_preview.png"}`
10. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\C\\sandbox_nl\\output\\gen_c\\quality\\round_1\\happy_t2.0_hole_character.png"}`
11. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\C\\sandbox_nl\\output\\gen_c\\missing_parts.json"}`
12. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\C\\sandbox_nl\\gen_c.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"absent\": [\"leg_l\", \"leg_r\"],\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[34,792],[100,772],[250,766],[40`
13. PowerShell：`{"command": "c2s run gen_c.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; Get-Content output\\gen_c\\validation_report.json -Raw -Encoding utf8; Get-Content output\\gen_c\\missing_parts.json -Raw -Encoding utf8", "description": "Rerun pipeline and show validation report", "timeout": 600000}`
14. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\C\\sandbox_nl\\output\\gen_c\\quality\\round_1\\idle_t0.7_hole_character.png"}`
15. PowerShell：`{"command": "$s = Get-ChildItem -Recurse -Filter visual_report.py -Path .claude, (Split-Path (Split-Path (Get-Command c2s).Source)) -ErrorAction SilentlyContinue | Select-Object -First 1; if (-not $s) { $s = Get-ChildItem -Recurse -Filter visual_report.py D:\\01_Project\\26_char_spine\\scripts -Erro`

## 最後回覆（原文）

我已經把 `gen_c.png` 的骨架和 idle／happy 動畫做出來並輸出成 Spine JSON，但驗證**整體狀態是 BLOCKED，還不能算完成**：有 3 個部件要人工補畫，而且這台電腦裝的是 Spine 試用版，產生不了 `.spine` 專案檔。

## 拆件
看圖寫好了 `gen_c.parts.json`（放在圖片旁邊），共 9 個部件：頭、身體、左右手、帽子、後髮、法杖、裙子和地面影子。
- **雙腳**：被長裙完全蓋住，宣告為看不到的部件（`absent`），所以沒有腳的骨頭和動畫。
- **畫面左邊的手**：設成握住法杖（`attach`），擺動時手和杖會一起動。
- 修正一輪後，沒被分到任何部件的像素從 2.5% 降到 0.18%。

## 驗證結果（`validation_report.json`）
| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 11 根骨頭，階層正確 |
| slots | PASS | 9 個插槽都有對應 |
| image_references | PASS | 圖片都在，尺寸也對 |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢和原圖的差異 0.0174 |
| manual_repairs | BLOCKED | shadow、hair_back、body 要人工補畫 |
| absent_parts | BLOCKED | leg_l、leg_r 被裙子蓋住，可以選擇補畫 |
| animation_quality | BLOCKED | 偵測到 hole（破洞）0.108，見下方說明 |
| spine_import | BLOCKED | 只有 Spine 試用版，不能存專案或匯出，所以沒有 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法做往返測試 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡人工確認 |

**關於 hole：** 標成破洞的地方，是法杖、手臂和裙襬圍住的那一塊背景，原圖那裡本來就是透明的。所以很可能是檢查誤判，不是真的穿幫。不過工具自動修正 3 輪都沒消掉，還是列為 BLOCKED，請在預覽裡看一下確認。

## 要人工補畫的部件（依動畫中露出的多寡排序）
1. **shadow（高）**：角色跳起來時，裙子底下的影子會露出最多 59%。目前是自動填的草稿，要補完整的橢圓影子。
2. **hair_back（高）**：後髮 90% 被擋住，動畫中最多露出 3.9%。
3. **body（高）**：被頭和手臂擋住的身體，動畫中露出 2.1%。
4. **head（中，自動填補但不可靠）**：帽子底下的頭頂，露出 0.8%。

補好後先執行 `c2s prepare --replace <部件>=<修好的.png>`，再執行 `c2s run gen_c.png`。

## 檔案
都在 `output/gen_c/`：
- 預覽：`preview/happy_python_simulation_preview.gif`（這是 Python Simulation Preview，不是 Spine 算出來的畫面）
- 補畫清單：`report/repair_priority.md`，附三格對照圖

要產生 `.spine` 專案，需要完整版的 Spine。