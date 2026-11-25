# E Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：examples/generalization/E/gen_e.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（指令可用，且第一個動作就是 c2s analyze）：否
- 觸發後執行 c2s：是（8 次）
- 讀取禁止路徑：0 次
- 工具呼叫次數：{'Edit': 1, 'PowerShell': 11, 'Read': 6, 'Skill': 1, 'Write': 2}

## c2s 指令

- `ls examples/generalization/E; .venv\Scripts\c2s.exe analyze examples/generalization/E/gen_e.png; "exit=$LASTEXITCODE"`
- `.venv\Scripts\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Select-Object -Last 40; "exit=$LASTEXITCODE"`
- `$p='examples/generalization/E/gen_e.parts.json'; $j=Get-Content $p -Raw -Encoding utf8 | ConvertFrom-Json
function S($n,$poly){ ($j.parts | ? name -eq $n).polygon = $poly }
S 'antler' @(@(248,182),@(258,150),@(252,80),@(292,60),@(318,68),@(350,28),@(388,0),@(408,10),@(402,42),@(368,90),@(405,96),@(412,130),@(365,142),@(332,165),@(295,178),@(270,194))
S 'arm_r' @(@(222,305),@(295,255),@(328,145),@(378,130),@(438,85),@(475,88),@(478,115),@(440,160),@(455,215),@(435,262),@(395,298),@(370,315),@(340,335),@(265,388),@(230,365))
S 'head' @(@(0,295),@(8,235),@(45,175),@(105,140),@(190,128),@(250,148),@(282,200),@(290,262),@(272,305),@(240,330),@(200,350),@(150,372),@(100,398),@(62,404),@(28,382),@(0,345))
S 'leg_l' @(@(100,498),@(130,520),@(200,575),@(228,608),@(160,645),@(60,665),@(35,648),@(48,600),@(72,540))
S 'tail' @(@(270,480),@(300,438),@(332,412),@(370,400),@(440,405),@(480,420),@(500,455),@(495,478),@(440,500),@(420,560),@(390,605),@(340,605),@(325,565),@(290,560))
S 'arm_l' @(@(5,455),@(45,420),@(90,420),@(110,420),@(142,450),@(140,492),@(95,505),@(45,525),@(5,490))
$j | ConvertTo-Json -Depth 6 | Set-Content $p -Encoding utf8
.venv\Scripts\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Out-Null; "exit=$LASTEXITCODE"
$m=Get-Content output/gen_e/missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.unassigned_regions | select -First 6 | % { "$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)" }; $m.needs_manual | % name
(Get-Content output/gen_e/validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json).checks | % { "$($_.check): $($_.status) - $($_.detail)" }`
- `.venv\Scripts\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Select-Object -First 30`
- `.venv\Scripts\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Out-Null; "exit=$LASTEXITCODE"
$m=Get-Content output/gen_e/missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.unassigned_regions | select -First 6 | % { "$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)" }; "manual: $($m.needs_manual.name -join ', ')"
(Get-Content output/gen_e/validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json).checks | % { "$($_.check): $($_.status) - $($_.detail)" }`
- `$o = .venv\Scripts\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Out-String | ConvertFrom-Json; $o.status; $o.stopped_after; $o.message`
- `.venv\Scripts\python.exe -c "import pathlib;p=pathlib.Path('examples/generalization/E/gen_e.parts.json');b=p.read_bytes();p.write_bytes(b.removeprefix(b'\xef\xbb\xbf'));print(p.read_bytes()[:3])"
.venv\Scripts\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Out-Null; "exit=$LASTEXITCODE"
$m=Get-Content output/gen_e/missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; $m.unassigned_regions | select -First 6 | % { "$($_.bbox -join ',') area=$($_.area) near=$($_.nearest_part)" }; "manual: $($m.needs_manual.name -join ', ')"
(Get-Content output/gen_e/validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json).checks | % { "$($_.check): $($_.status) - $($_.detail)" }`
- `.venv\Scripts\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Out-Null; "exit=$LASTEXITCODE"
$m=Get-Content output/gen_e/missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; "unassigned=$($m.unassigned_ratio)"; "manual: $($m.needs_manual.name -join ', ')"
(Get-Content output/gen_e/validation_report.json -Raw -Encoding utf8 | ConvertFrom-Json).checks | % { "$($_.check): $($_.status) - $($_.detail)" }`

## 禁止路徑

- 無

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "examples/generalization/E/gen_e.png"}`
2. PowerShell：`{"command": "ls examples/generalization/E; .venv\\Scripts\\c2s.exe analyze examples/generalization/E/gen_e.png; \"exit=$LASTEXITCODE\"", "description": "List folder and run c2s analyze"}`
3. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_e\\grid_overlay.png"}`
4. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\E\\gen_e.png"}`
5. PowerShell：`{"command": "Get-ChildItem examples -Recurse -Filter *.parts.json | % FullName; Get-Content output/gen_e/parts.template.json", "description": "Find existing parts.json examples and template"}`
6. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\E\\gen_e.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[15, 640], [200, 628], [360, 628], [485, 638], [470, 660], [360, 672], [360, 715`
7. PowerShell：`{"command": ".venv\\Scripts\\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Select-Object -Last 40; \"exit=$LASTEXITCODE\"", "description": "Run full c2s pipeline", "timeout": 600000}`
8. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_e\\layer_preview.png"}`
9. PowerShell：`{"command": "Get-Content output/gen_e/missing_parts.json -Raw | Select-Object -First 1; Get-Content output/gen_e/quality/quality_report.json -Raw | % { $_.Substring(0, [Math]::Min(3000, $_.Length)) }", "description": "Show missing parts and quality report"}`
10. PowerShell：`{"command": "$p='examples/generalization/E/gen_e.parts.json'; $j=Get-Content $p -Raw -Encoding utf8 | ConvertFrom-Json\nfunction S($n,$poly){ ($j.parts | ? name -eq $n).polygon = $poly }\nS 'antler' @(@(248,182),@(258,150),@(252,80),@(292,60),@(318,68),@(350,28),@(388,0),@(408,10),@(402,42),@(368,90`
11. PowerShell：`{"command": ".venv\\Scripts\\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Select-Object -First 30", "description": "Rerun to see exit-2 message", "timeout": 600000}`
12. Write：`{"file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\E\\gen_e.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[15, 640], [200, 628], [360, 628], [485, 638], [470, 660], [360, 672], [360, 715`
13. PowerShell：`{"command": ".venv\\Scripts\\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"\n$m=Get-Content output/gen_e/missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; $m.unassigned_regions | select -First 6 | % { `
14. PowerShell：`{"command": "$o = .venv\\Scripts\\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Out-String | ConvertFrom-Json; $o.status; $o.stopped_after; $o.message", "description": "Show c2s run status message", "timeout": 600000}`
15. PowerShell：`{"command": ".venv\\Scripts\\python.exe -c \"import pathlib;p=pathlib.Path('examples/generalization/E/gen_e.parts.json');b=p.read_bytes();p.write_bytes(b.removeprefix(b'\\xef\\xbb\\xbf'));print(p.read_bytes()[:3])\"\n.venv\\Scripts\\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Ou`
16. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_e\\quality\\round_3\\happy_t1.4_hole_character.png"}`
17. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_e\\layer_preview.png"}`
18. Edit：`{"replace_all": false, "file_path": "D:\\01_Project\\26_char_spine\\examples\\generalization\\E\\gen_e.parts.json", "old_string": "[[105, 420], [190, 370], [250, 330], [295, 360], [310, 450], [330, 540], [320, 595], [230, 620], [130, 610], [100, 520]]", "new_string": "[[100, 420], [160, 370], [215, `
19. PowerShell：`{"command": ".venv\\Scripts\\c2s.exe run examples/generalization/E/gen_e.png --motion happy | Out-Null; \"exit=$LASTEXITCODE\"\n$m=Get-Content output/gen_e/missing_parts.json -Raw -Encoding utf8 | ConvertFrom-Json; \"unassigned=$($m.unassigned_ratio)\"; \"manual: $($m.needs_manual.name -join ', ')\"`
20. PowerShell：`{"command": ".venv\\Scripts\\python.exe scripts/visual_report.py output/gen_e | Out-Null; \"exit=$LASTEXITCODE\"; Get-Content output/gen_e/report/repair_priority.md -Encoding utf8 | Select-Object -First 40; ls output/gen_e/spine* , output/gen_e/*.json | % Name", "description": "Generate visual repai`
21. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_e\\report\\visual_check.png"}`

## 最後回覆（原文）

Spine JSON 骨架和兩段動畫（idle、happy）已經產生。Python 預覽裡動作正常，但還不算完成：有 6 個部件要人工補畫，而且這台只有 Spine 試用版，沒辦法建立 `.spine` 專案。

**檔案位置**
- 部件定義：`examples/generalization/E/gen_e.parts.json`（放在原圖旁，原圖沒動）
- 產物：`output/gen_e/`，Spine JSON 在 `output/gen_e/spine/`
- 預覽：`output/gen_e/preview/happy_python_simulation_preview.gif`、`idle_python_simulation_preview.gif`（Python Simulation Preview，不是 Spine 算圖）

部件共 11 個：頭、身體、左右手、左右腿，加上角、耳、領巾、尾巴、地上的陰影。改了三輪 parts.json，沒歸到任何部件的像素從 6.7% 降到 0.42%。

**驗證報告（`validation_report.json`）**

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 13 根骨頭，階層順序正確 |
| slots | PASS | 11 個插槽都對應到骨頭與附件 |
| image_references | PASS | 附件圖片都存在、尺寸相符、不是空白 |
| animations | PASS | idle 2.0 秒 31 個關鍵影格，happy 2.4 秒 106 個 |
| setup_pose | PASS | 初始姿勢與原圖差異 0.0018 |
| animation_quality | PASS | 第 3 輪自動修正後，破洞、縫隙、接觸分離、穿插都在門檻內。尾巴有 1.6%、頭有 0.7% 的自動補圖會在動畫中露出，在門檻內，但建議目視確認 |
| manual_repairs | **BLOCKED** | 6 個部件等人工補畫，見下表 |
| spine_import | **BLOCKED** | 偵測到的是 Spine 試用版，不能存專案或匯出，所以沒有 `.spine` 檔 |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法往返驗證 |
| spine_editable | NOT_TESTED | 要人工在 Spine Editor 打開專案確認 |

**要人工補畫的部件**（依動畫中露出量排序，詳見 `output/gen_e/report/repair_priority.md`）

| 順位 | 部件 | 優先 | 最大露出 | 被誰遮住 |
|---|---|---|---|---|
| 1 | shadow | 高 | 9.98% | 雙腿、身體 |
| 2 | leg_l | 中 | 1.79% | 身體、左手 |
| 3 | arm_l | 中 | 1.46% | 領巾 |
| 4 | leg_r | 中 | 1.17% | 左腿、身體 |
| 5 | ear | 中 | 1.11% | 頭 |
| 6 | body | 中 | 0.82% | 頭、手、領巾 |

除了陰影，其他部件露出都不到 2%，可以先用自動補的草稿，但被遮住的輪廓要對照原圖重畫，自動補不出來。補好後執行：

```
c2s prepare --replace <部件>=<修好的.png>
c2s run examples/generalization/E/gen_e.png
```

**預覽裡看到的問題**：陰影設了 `motion: 0`，但它掛在身體骨頭下，happy t=0.5s 角色跳起來時陰影也跟著往上。其他部件在預覽裡沒看到轉錯方向或亂甩。修法有兩個，你選一個：
- 把陰影從部件裡拿掉。
- 在 Spine 裡把陰影改掛到 root 骨頭下。

**其他**：在 PowerShell 5.1 裡寫 parts.json 會加上 BOM，c2s 讀不了。這次已經去掉了，之後手動改這個檔要存成不含 BOM 的 UTF-8。