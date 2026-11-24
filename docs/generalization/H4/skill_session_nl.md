# H4 Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：gen_h4.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（6 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：4 次
- 工具呼叫次數：{'Edit': 3, 'Glob': 2, 'PowerShell': 7, 'Read': 7, 'Skill': 1, 'Write': 2}

## c2s 指令

- `$c = (Get-Command c2s -ErrorAction SilentlyContinue).Source; if (-not $c) { Get-ChildItem -Path . , .. , ..\.. -Filter c2s.exe -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 3 -ExpandProperty FullName } else { $c }`
- `c2s analyze gen_h4.png; "exit=$LASTEXITCODE"; Get-ChildItem -Recurse output | Select-Object -ExpandProperty FullName`
- `c2s run gen_h4.png --motion happy; "exit=$LASTEXITCODE"`
- `c2s run gen_h4.png --motion happy | Out-Null; "exit=$LASTEXITCODE"; $m = Get-Content output\gen_h4\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.needs_manual | ForEach-Object { "$($_.name) $($_.hidden_ratio)" }; $m.unassigned_regions | Select-Object -First 6 | ForEach-Object { "$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)" }; (Get-Content output\gen_h4\validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json).checks | ForEach-Object { "$($_.check): $($_.status) - $($_.detail)" }`
- `c2s run gen_h4.png --motion happy | Out-Null; "exit=$LASTEXITCODE"; $m = Get-Content output\gen_h4\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.needs_manual | ForEach-Object { "$($_.name) $($_.hidden_ratio)" }; $q = Get-Content output\gen_h4\quality\quality_report.json -Raw -Encoding utf8 | ConvertFrom-Json; "unresolved=$($q.unresolved.Count) downgraded=$($q.downgraded_to_needs_manual -join ',')"; (Get-Content output\gen_h4\validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json).checks | ForEach-Object { "$($_.check): $($_.status) - $($_.detail)" }; & D:\01_Project\26_char_spine\.venv\Scripts\python.exe D:\01_Project\26_char_spine\scripts\visual_report.py output\gen_h4; "vr_exit=$LASTEXITCODE"`
- `c2s run gen_h4.png --motion happy | Out-Null; "exit=$LASTEXITCODE"; $m = Get-Content output\gen_h4\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.needs_manual | ForEach-Object { "$($_.name) $($_.hidden_ratio)" }; $q = Get-Content output\gen_h4\quality\quality_report.json -Raw -Encoding utf8 | ConvertFrom-Json; "unresolved=$($q.unresolved.Count) downgraded=$($q.downgraded_to_needs_manual -join ',')"; (Get-Content output\gen_h4\validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json).checks | ForEach-Object { "$($_.check): $($_.status) - $($_.detail)" }; & D:\01_Project\26_char_spine\.venv\Scripts\python.exe D:\01_Project\26_char_spine\scripts\visual_report.py output\gen_h4 | Out-Null; "vr_exit=$LASTEXITCODE"; Get-Content output\gen_h4\report\repair_priority.md -Encoding utf8`

## 讀到答案

- 無

## 使用沙盒外的工具

- PowerShell：{"command": "$c = (Get-Command c2s -ErrorAction SilentlyContinue).Source; if (-not $c) { Get-ChildItem -Path . , .. , ..\\.. -Filter c2s.exe -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Ob
- Glob：{"pattern": "**/visual_report.py", "path": "D:\\01_Project\\26_char_spine"}
- PowerShell：{"command": "c2s run gen_h4.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; $m = Get-Content output\\gen_h4\\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassig
- PowerShell：{"command": "c2s run gen_h4.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; $m = Get-Content output\\gen_h4\\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassig

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_h4.png"}`
2. Glob：`{"pattern": "**/*"}`
3. PowerShell：`{"command": "$c = (Get-Command c2s -ErrorAction SilentlyContinue).Source; if (-not $c) { Get-ChildItem -Path . , .. , ..\\.. -Filter c2s.exe -Recurse -Depth 4 -ErrorAction SilentlyContinue | Select-Object -First 3 -ExpandProperty FullName } else { $c }", "description": "Locate the c2s executable"}`
4. PowerShell：`{"command": "c2s analyze gen_h4.png; \"exit=$LASTEXITCODE\"; Get-ChildItem -Recurse output | Select-Object -ExpandProperty FullName", "description": "Analyze the character image"}`
5. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\output\\gen_h4\\grid_overlay.png"}`
6. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\output\\gen_h4\\parts.template.json"}`
7. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\gen_h4.png"}`
8. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\gen_h4.parts.json", "content": "{\n  \"version\": 1,\n  \"image\": \"gen_h4.png\",\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"tail\", \"polygon\": [[345,372],[395,362],[415,325],[425,290],[`
9. PowerShell：`{"command": "c2s run gen_h4.png --motion happy; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
10. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\output\\gen_h4\\layer_preview.png"}`
11. PowerShell：`{"command": "Get-Content output\\gen_h4\\missing_parts.json -Raw", "description": "Show unassigned regions report"}`
12. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\gen_h4.parts.json", "content": "{\n  \"version\": 1,\n  \"image\": \"gen_h4.png\",\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"tail\", \"polygon\": [[345,368],[395,358],[412,322],[422,285],[`
13. PowerShell：`{"command": "c2s run gen_h4.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; $m = Get-Content output\\gen_h4\\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; $m.needs_manual | ForEach-Object { \"$($_.name) $($_.hidden_ratio)\" }; $m.unassigned_`
14. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\output\\gen_h4\\layer_preview.png"}`
15. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\output\\gen_h4\\quality\\quality_report.json"}`
16. Edit：`{"replace_all": false, "file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\gen_h4.parts.json", "old_string": "[478,395],[455,410],[420,412]", "new_string": "[478,395],[456,412],[450,436],[416,436],[414,412]"}`
17. Glob：`{"pattern": "**/visual_report.py", "path": "D:\\01_Project\\26_char_spine"}`
18. PowerShell：`{"command": "c2s run gen_h4.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; $m = Get-Content output\\gen_h4\\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; $m.needs_manual | ForEach-Object { \"$($_.name) $($_.hidden_ratio)\" }; $q = Get-Conte`
19. Edit：`{"replace_all": false, "file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\gen_h4.parts.json", "old_string": "[478,395],[456,412],[450,436],[416,436],[414,412]", "new_string": "[478,395],[455,410],[420,412]"}`
20. Edit：`{"replace_all": false, "file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\gen_h4.parts.json", "old_string": "[400,396],[424,420],[430,470]", "new_string": "[400,396],[416,408],[452,410],[452,436],[430,440],[430,470]"}`
21. PowerShell：`{"command": "c2s run gen_h4.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; $m = Get-Content output\\gen_h4\\missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; $m.needs_manual | ForEach-Object { \"$($_.name) $($_.hidden_ratio)\" }; $q = Get-Conte`
22. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\H4\\sandbox_nl\\output\\gen_h4\\report\\visual_check.png"}`

## 最後回覆（原文）

Spine 動畫已經做好，但還沒完全完成：有 3 個部件要人工補畫，而且這台電腦只有 Spine 試用版，無法產生 `.spine` 專案檔。已產出 Spine JSON、分層 PNG，以及 idle 和 happy 兩段動畫。

**拆件**：這是一個坐著的擬人動物，拆成 7 個部件：head、body、arm_l（拿筆的手，筆也算在這個部件裡）、arm_r（纏繃帶的手）、leg_l、leg_r，再加一條尾巴 tail。我調了兩輪 polygon，沒被任何部件涵蓋的像素從 8.9% 降到 0.57%，剩下的只是頭頂和手邊幾小撮零碎的毛。因為是坐姿，兩條腿的動作幅度設得很小（0.15）。

**`validation_report.json` 各項結果**

| 項目 | 狀態 |
|---|---|
| bones | PASS |
| slots | PASS |
| image_references | PASS |
| animations | PASS：idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS：初始姿勢和原圖的差異是 0.0015 |
| animation_quality | PASS：沒有破洞、關節縫隙或接觸分離 |
| manual_repairs | **BLOCKED**：tail、body、leg_r 要人工補畫 |
| spine_import | **BLOCKED**：Spine 試用版不能存專案，產生不了 `.spine` |
| spine_roundtrip | NOT_TESTED |
| spine_editable | NOT_TESTED：要在 Spine Editor 裡手動開啟並改關鍵影格確認 |

**要人工補畫的部件（依優先順序）**

1. **body（高）**：衣服約 68% 被頭、手、腿擋住。動畫中最多露出 4.7%，被擋住的輪廓得對照原圖重畫。
2. **leg_r（高）**：約 29% 被左腿和雙手擋住，最多露出 4.7%。
3. **tail（高）**：尾巴根部被右手擋住，最多露出 2.6%。

補畫的對照圖和說明都在 `output/gen_h4/report/repair_priority.md`。補好一張後執行：
```
c2s prepare --replace body=<修好的.png>
c2s run gen_h4.png --motion happy
```
leg_l 和 head 用的是自動補圖。它們的露出量還在門檻內（1.5% 和 0.2%），但最好用肉眼確認一下。

**其他提醒**
- 如果暫時不想補畫，可以在 `gen_h4.parts.json` 把 arm_r 的 `motion` 從 0.5 調低，tail 和 leg_r 的露出量就會跟著變小。
- happy 動畫會讓整個角色往上跳，鞋子也會離地。對坐姿角色來說可能不太自然，可以看 `output/gen_h4/preview/happy_python_simulation_preview.gif`（Python Simulation Preview，不是 Spine 算圖）自己判斷。
- 原圖右側有作者署名浮水印「@VANTIDAZE」，它被切進 body 圖層了，商用前請確認授權。

部件設定存在 `gen_h4.parts.json`（在圖片旁邊），產出的檔案在 `output/gen_h4/`。