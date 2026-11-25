# D Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：examples/generalization/D/gen_d.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（指令可用，且第一個動作就是 c2s analyze）：否
- 觸發後執行 c2s：是（3 次）
- 讀取禁止路徑：1 次
- 工具呼叫次數：{'Glob': 1, 'PowerShell': 7, 'Read': 6, 'Skill': 1, 'Write': 1}

## c2s 指令

- `Get-ChildItem examples/generalization/D; .\.venv\Scripts\c2s.exe analyze examples/generalization/D/gen_d.png; "exit=$LASTEXITCODE"`
- `.\.venv\Scripts\c2s.exe run examples/generalization/D/gen_d.png --motion happy | Select-Object -Last 60; "exit=$LASTEXITCODE"`
- `$f='examples/generalization/D/gen_d.parts.json'; $t=[IO.File]::ReadAllText($f)
$r=@{
'[[110, 150], [200, 90]'='[[106, 104], [126, 104], [200, 90]';
'[410, 320], [440, 420], [465, 520], [472, 600]'='[418, 304], [440, 420], [476, 502], [478, 600]';
'[68, 540], [105, 480]'='[52, 540], [105, 480]';
'[370, 722], [330, 702]'='[394, 724], [372, 740], [330, 702]';
'[422, 940], [428, 988], [342, 1012]'='[430, 912], [434, 990], [402, 1022], [342, 1018]';
'[82, 792], [56, 740], [52, 650]'='[84, 842], [48, 832], [38, 745], [50, 650]';
'[382, 1208], [428, 1250], [442, 1290], [412, 1314]'='[398, 1182], [428, 1250], [444, 1300], [442, 1318], [412, 1318]'}
foreach($k in $r.Keys){ if(-not $t.Contains($k)){throw "missing $k"}; $t=$t.Replace($k,$r[$k]) }
[IO.File]::WriteAllText($f,$t,(New-Object Text.UTF8Encoding $false))
.\.venv\Scripts\c2s.exe run examples/generalization/D/gen_d.png --motion happy | Out-Null; "exit=$LASTEXITCODE"
$m=Get-Content output/gen_d/missing_parts.json -Encoding utf8 -Raw | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.unassigned_regions | % { "$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)" }
(Get-Content output/gen_d/validation_report.json -Encoding utf8 -Raw | ConvertFrom-Json).checks | % { "$($_.check): $($_.status) — $($_.detail)" }`

## 禁止路徑

- Read：`转场2.parts`：{"file_path": "D:\\01_Project\\26_char_spine\\examples\\real\\转场2.parts.json"}

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "examples/generalization/D/gen_d.png"}`
2. PowerShell：`{"command": "Get-ChildItem examples/generalization/D; .\\.venv\\Scripts\\c2s.exe analyze examples/generalization/D/gen_d.png; \"exit=$LASTEXITCODE\"", "description": "List folder and run c2s analyze"}`
3. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\grid_overlay.png"}`
4. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\D\\gen_d.png"}`
5. PowerShell：`{"command": "Get-ChildItem examples -Recurse -Filter *.parts.json | % FullName; Get-ChildItem docs/generalization -Recurse | % FullName", "description": "Find existing parts.json examples"}`
6. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\real\\转场2.parts.json"}`
7. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\D\\gen_d.parts.json", "content": "{\n  \"version\": 1,\n  \"image\": \"gen_d.png\",\n  \"preset\": \"humanoid-chibi\",\n  \"_note\": \"由 Claude Code 依 grid_overlay.png 目測撰寫。雙手舉相機在臉前；相機掛在 arm_l 下，arm_r 以 attach 保持接觸。\",\n  \"part`
8. PowerShell：`{"command": ".\\.venv\\Scripts\\c2s.exe run examples/generalization/D/gen_d.png --motion happy | Select-Object -Last 60; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
9. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\layer_preview.png"}`
10. PowerShell：`{"command": "Get-Content output/gen_d/missing_parts.json -Encoding utf8 | Select-Object -First 60", "description": "Show unassigned regions"}`
11. PowerShell：`{"command": "(Get-Content output/gen_d/missing_parts.json -Encoding utf8 -Raw | ConvertFrom-Json).unassigned_regions | % { \"$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)\" }", "description": "List all unassigned regions compactly"}`
12. PowerShell：`{"command": "$f='examples/generalization/D/gen_d.parts.json'; $t=[IO.File]::ReadAllText($f)\n$r=@{\n'[[110, 150], [200, 90]'='[[106, 104], [126, 104], [200, 90]';\n'[410, 320], [440, 420], [465, 520], [472, 600]'='[418, 304], [440, 420], [476, 502], [478, 600]';\n'[68, 540], [105, 480]'='[52, 540], `
13. PowerShell：`{"command": ".\\.venv\\Scripts\\python.exe scripts/visual_report.py output/gen_d | Select-Object -Last 10; $q=Get-Content output/gen_d/quality/quality_report.json -Encoding utf8 -Raw | ConvertFrom-Json; \"unresolved=$($q.unresolved | ConvertTo-Json -Compress -Depth 4)\"; Get-Content output/gen_d/rep`
14. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\preview\\happy_python_simulation_preview.gif"}`
15. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_d\\report\\visual_check.png"}`
16. Glob：`{"pattern": "output/gen_d/**/*.{json,md}"}`

## 最後回覆（原文）

The Spine JSON for the idle and happy animations is built, but it isn't finished: three parts need hand-painting, and nothing has been opened in Spine yet.

**What I made**
- I wrote the parts list from the character image: `examples/generalization/D/gen_d.parts.json`. It has 11 parts: the 6 required ones plus hair_back, bow, skirt, apron and camera.
- The camera follows the screen-left arm (`arm_l`), and the screen-right arm (`arm_r`) is tied to the camera so the two stay in contact. Both arms move at 0.2 so the camera stays steady.
- On the first run 0.55% of the picture's pixels weren't in any part. I widened the outlines and it's now 0.05%, just a few thin edge slivers.
- Spine JSON: `output/gen_d/spine/character.json`. The preview GIFs are a Python simulation, not a Spine render. In the key-frame overview (`report/visual_check.png`) the hand stays on the camera and I saw no visible gaps or tears.

**`validation_report.json` results**

| Check | Status |
|---|---|
| bones | PASS (13 bones) |
| slots | PASS |
| image_references | PASS |
| animations | PASS (idle 2.0s, happy 2.4s) |
| setup_pose | PASS (0.0018 difference from the original image) |
| animation_quality | PASS (passed every threshold on the third tuning round; no problems left) |
| manual_repairs | **BLOCKED**: 3 parts need hand-painting |
| spine_import | **BLOCKED**: only the Spine trial is installed, and it can't save or export, so no `.spine` project was created |
| spine_roundtrip | NOT_TESTED |
| spine_editable | NOT_TESTED |

**Parts to repaint by hand** (most visible first; how much hidden area shows during the animation):
1. `body` 3.27%: about 57% of it was hidden behind the skirt, apron, head and arms, so the fill there is only an automatic draft.
2. `hair_back` 2.87%: about 80% was hidden.
3. `skirt` 2.03%: the part covered by the apron.

Four more parts were filled automatically and show a little during the animation (still within limits, but worth a look): bow 1.7%, camera 1.3%, head 1.0%, apron 0.02%. The comparison images are in `output/gen_d/report/repair_priority.md`.

To bring a repainted part back in:
`c2s prepare --replace body=<repaired.png>`
then re-run `c2s run examples/generalization/D/gen_d.png --motion happy`.

To clear the two Spine checks you'll need the full version of Spine to build the `.spine` project, and then someone has to open it in the Spine Editor and confirm it can be edited.