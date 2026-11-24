# A Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：examples/generalization/A/gen_a.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開：否
- 觸發後執行 c2s：是（4 次）
- 讀取禁止路徑：0 次
- 工具呼叫次數：{'Edit': 2, 'PowerShell': 5, 'Read': 11, 'Skill': 1, 'Write': 2}

## c2s 指令

- `.\.venv\Scripts\c2s.exe analyze examples/generalization/A/gen_a.png; "exit=$LASTEXITCODE"; Get-ChildItem examples/generalization/A`
- `.\.venv\Scripts\c2s.exe run examples/generalization/A/gen_a.png --motion happy | Select-Object -Last 40; "exit=$LASTEXITCODE"`
- `.\.venv\Scripts\c2s.exe run examples/generalization/A/gen_a.png --motion happy | Out-Null; "exit=$LASTEXITCODE"; $m = Get-Content output/gen_a/missing_parts.json -Raw | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.unassigned_regions | % { "$($_.bbox -join ',') area=$($_.area) $($_.nearest_part)" }; $m.needs_manual | % { "$($_.name): $($_.reason)" }; (Get-Content output/gen_a/validation_report.json -Raw | ConvertFrom-Json).checks | % { "$($_.check) $($_.status) - $($_.detail)" }`
- `.\.venv\Scripts\c2s.exe run examples/generalization/A/gen_a.png --motion happy | Out-Null; "exit=$LASTEXITCODE"`

## 禁止路徑

- 無

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "examples/generalization/A/gen_a.png"}`
2. PowerShell：`{"command": ".\\.venv\\Scripts\\c2s.exe analyze examples/generalization/A/gen_a.png; \"exit=$LASTEXITCODE\"; Get-ChildItem examples/generalization/A", "description": "Analyze character image with c2s"}`
3. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\grid_overlay.png"}`
4. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\A\\gen_a.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"leg_l\", \"polygon\": [[400, 775], [485, 775], [492, 850], [488, 930], [415, 932], [398, 870]], \"z\": 1`
5. PowerShell：`{"command": ".\\.venv\\Scripts\\c2s.exe run examples/generalization/A/gen_a.png --motion happy | Select-Object -Last 40; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline with happy motion", "timeout": 600000}`
6. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\layer_preview.png"}`
7. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\missing_parts.json"}`
8. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\validation_report.json"}`
9. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\A\\gen_a.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"leg_l\", \"polygon\": [[400, 775], [485, 775], [492, 850], [488, 930], [415, 932], [398, 870]], \"z\": 1`
10. PowerShell：`{"command": ".\\.venv\\Scripts\\c2s.exe run examples/generalization/A/gen_a.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"; $m = Get-Content output/gen_a/missing_parts.json -Raw | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; $m.unassigned_regions | % { \"$($_.bbox -join ',') area=`
11. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\quality\\round_3\\happy_t1.6_hole_character.png"}`
12. Edit：`{"replace_all": false, "file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\A\\gen_a.parts.json", "old_string": "[[600, 520], [615, 460], [705, 450], [725, 600], [740, 750], [685, 755], [655, 650], [600, 650]]", "new_string": "[[615, 460], [705, 450], [725, 600], [740, 750], [685, `
13. Edit：`{"replace_all": false, "file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\A\\gen_a.parts.json", "old_string": "[604, 538], [600, 620], [580, 705]", "new_string": "[604, 530], [656, 530], [656, 648], [600, 648], [580, 705]"}`
14. PowerShell：`{"command": ".\\.venv\\Scripts\\c2s.exe run examples/generalization/A/gen_a.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"", "description": "Rerun pipeline after moving hair strip to body", "timeout": 600000}`
15. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\validation_report.json"}`
16. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\missing_parts.json"}`
17. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\layer_preview.png"}`
18. PowerShell：`{"command": ".\\.venv\\Scripts\\python.exe scripts/visual_report.py output/gen_a | Out-Null; \"exit=$LASTEXITCODE\"", "description": "Generate visual repair priority report", "timeout": 300000}`
19. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\preview\\happy_python_simulation_preview.gif"}`
20. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\report\\repair_priority.md"}`
21. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_a\\report\\visual_check.png"}`

## 最後回覆（原文）

Spine JSON 骨架和 Idle、Happy 兩段動畫都做好了，但整體狀態是 **BLOCKED**：還有 5 個部件要人工補畫，而且這台只有 Spine 試用版，沒辦法產生 `.spine` 專案。

部件劃分寫在 `examples/generalization/A/gen_a.parts.json`，共 9 個：必要的 6 個，加上左右辮子 `braid_l`／`braid_r` 和 `skirt`。帽子、蝴蝶結、毛球都算在 `head` 裡。我改了兩輪多邊形：未分配的像素從 1.2% 降到 0.01%（只剩右靴旁邊 24 像素），圖層重組後和原圖一致。

第二輪曾經把右辮內側那條頭髮劃給 `braid_r`，結果 happy 在 t=1.6s 出現破洞，`animation_quality` 變成 BLOCKED。我把那條改劃給 `body` 之後，這一項回到 PASS。

**驗證報告（`validation_report.json`）**

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 11 根骨頭，階層正確 |
| slots | PASS | 9 個插槽 |
| image_references | PASS | |
| animations | PASS | idle 2.0 秒、happy 2.4 秒 |
| setup_pose | PASS | 和原圖差異 0.0015 |
| animation_quality | PASS | 破洞、關節縫隙、接觸分離都在門檻內（採用第 3 輪） |
| manual_repairs | **BLOCKED** | 5 個部件等待人工補畫 |
| spine_import | **BLOCKED** | 只有試用版，無法產生 `.spine` |
| spine_roundtrip | NOT_TESTED | 因為沒有 `.spine` |
| spine_editable | NOT_TESTED | 需要在 Spine Editor 裡人工確認 |

**需要人工補畫的部件（依動畫中實際露出量排序，全部是高優先）**

目前這些部件被遮住的地方只有自動填的草稿，動畫時會露出來，還不算修好。

1. `skirt`：被兩隻手臂遮住的部分，最多露出 12.2%（happy t=0.5s）
2. `leg_l`：被右腿和裙子遮住的部分，最多露出 11.4%
3. `body`：被裙子、頭、手臂遮住的部分，最多露出 3.9%
4. `braid_r`：被身體和頭遮住的部分，最多露出 3.5%
5. `leg_r`：被裙子和右手遮住的部分，最多露出 2.0%

另外 `braid_l` 是自動補的，但不可靠，最多露出 1.9%（中優先），建議目視確認。

每個部件的三格對照圖在 `output/gen_a/report/repair_priority.md`。補好一張後，執行 `c2s prepare --replace <部件>=<修好的.png>`，再跑一次 `c2s run examples/generalization/A/gen_a.png`。

暫時不想補畫的話，可以調低遮擋它的部件的 `motion`，例如兩隻手臂，現在是 0.6。動作會變小，露出也跟著變少。

**預覽**

`output/gen_a/preview/happy_python_simulation_preview.gif` 和 `idle_python_simulation_preview.gif` 是 Python Simulation Preview，不是 Spine 算圖。我看了總覽圖 `report/visual_check.png`，沒有看到肢體轉錯方向或道具亂甩。