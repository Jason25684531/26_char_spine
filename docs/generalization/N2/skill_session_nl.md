# N2 Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`請將這張角色圖拆補圖、建立骨架，製作 Idle／Happy 動畫並輸出結果：gen_n2.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（5 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：0 次
- 工具呼叫次數：{'Edit': 1, 'PowerShell': 5, 'Read': 7, 'Skill': 1, 'Write': 2}

## c2s 指令

- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N2\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" --version`
- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N2\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" analyze gen_n2.png; "exit=$LASTEXITCODE"`
- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N2\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" run gen_n2.png; "exit=$LASTEXITCODE"`
- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N2\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" run gen_n2.png | Select-String -Pattern '"status"|unassigned_ratio|needs_manual|unresolved|detail' ; "exit=$LASTEXITCODE"`
- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N2\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" run gen_n2.png | Select-String -Pattern '"status"|unassigned_ratio|unresolved|detail' ; "exit=$LASTEXITCODE"`

## 讀到答案

- 無

## 使用沙盒外的工具

- 無

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_n2.png"}`
2. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" --version", "description": "Check c2s version and set up environment", "timeout": 600000}`
3. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\.claude\\skills\\character-to-spine\\references\\parts-format.md"}`
4. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" analyze gen_n2.png; \"exit=$LASTEXITCODE\"", "description": "Analyze character image"}`
5. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\output\\gen_n2\\grid_overlay.png"}`
6. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\gen_n2.png"}`
7. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\gen_n2.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[5,762],[385,762],[385,796],[5,796]], \"z\": 0, \"role\": \"ground\"}`
8. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" run gen_n2.png; \"exit=$LASTEXITCODE\"", "description": "Run full character-to-spine pipeline", "timeout": 600000}`
9. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\output\\gen_n2\\layer_preview.png"}`
10. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\output\\gen_n2\\report\\visual_check.png"}`
11. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\gen_n2.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"shadow\", \"polygon\": [[2,760],[388,760],[388,799],[2,799]], \"z\": 0, \"role\": \"ground\"}`
12. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" run gen_n2.png | Select-String -Pattern '\"status\"|unassigned_ratio|needs_manual|unresolved|detail' ; \"exit=$LASTEXITCODE\"", "description": "Rerun pipel`
13. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\output\\gen_n2\\report\\visual_check.png"}`
14. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\output\\gen_n2\\report\\repair_priority.md"}`
15. Edit：`{"replace_all": false, "file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\gen_n2.parts.json", "old_string": "[380,790],[336,790],[312,534]", "new_string": "[380,790],[336,792],[314,772],[310,534]"}`
16. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N2\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" run gen_n2.png | Select-String -Pattern '\"status\"|unassigned_ratio|unresolved|detail' ; \"exit=$LASTEXITCODE\"", "description": "Rerun pipeline after swo`

## 最後回覆（原文）

拆圖、骨架和 Idle／Happy 動畫都已產生，但**整體狀態是 BLOCKED，還不算完成**。卡住的原因有兩個：有 5 個部件要人工補畫，以及這台電腦只有 Spine 試用版，無法建立 `.spine` 專案。Spine JSON、分層 PNG 和預覽都能先用。

## validation_report.json 各項

| 檢查 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 13 根骨頭，階層正確 |
| slots | PASS | 11 個插槽都對應到骨頭與圖片 |
| image_references | PASS | 圖片都存在、尺寸相符、不是空白 |
| animations | PASS | idle 2.0 秒；happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢與原圖差異 0.0107 |
| manual_repairs | **BLOCKED** | 等待補畫：shadow、body、leg_r、leg_l、hair_back |
| animation_quality | PASS | 逐格檢查破洞、關節縫隙、手和劍分開、穿插，都在門檻內（自動修正後採用第 3 輪） |
| spine_import | **BLOCKED** | 偵測到的是 Spine 試用版，它不能儲存專案，所以沒有 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法驗證匯入再匯出 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡手動開啟確認 |

## 拆分方式
共 11 個部件：頭、身體、左右手、左右腳、後髮、紫色前襬（當裙擺）、左肩甲（含紫羽）、劍（道具）、地面影子。畫面右手設定為握住劍柄，劍跟著手動，動畫中手和劍沒有分開。調整過 3 次部件範圍，最後只剩 0.01% 像素沒分到部件。

## 輸出位置（`output/gen_n2/`）
- `layers/`：分層 PNG
- `spine/character.json`：Spine JSON
- `preview/idle_python_simulation_preview.gif`、`preview/happy_python_simulation_preview.gif`：Python Simulation Preview（Python 模擬，不是 Spine 算圖）
- `validation_report.json`
- `report/visual_check.png`

## 需要人工補畫（依 `report/repair_priority.md` 順序）
這些被遮住的區域目前是自動補上的草稿，**還沒修好**：

1. **shadow**（高）：影子約 65% 被腳和劍擋住，Happy 跳起來時最多露出 58.6%，影子會斷成好幾段。
2. **body**（高）：被前襬、手臂、肩甲擋住的盔甲，最多露出 8.2%。
3. **leg_r**（高）：最多露出 7.7%。
4. **leg_l**（高）：最多露出 5.9%。
5. **hair_back**（高）：後髮被身體擋住的部分，最多露出 3.3%。

另有 arm_l（中，1.8%）、sword（中，0.7%）、head（低，0.1%）是自動補但不可靠，建議看一下。

- 每個部件的對照圖：`report/repair_<部件>.png`（原圖、目前圖層、動畫中露出最多的三格）
- 自動補上的區域：`repair_masks/`
- 文字版待修清單：`repair_tasks.md`

**修好後怎麼匯回：** 把修好的 PNG 給我，我執行 `c2s prepare --replace <部件>=<修好的.png>`，再重跑 `c2s run gen_n2.png`。

## 自動檢查沒抓到、我看圖發現的問題
- **Happy 約 0.5 秒時劍會被甩成水平**：右手舉起時，劍以劍柄為軸往右平舉。沒有破圖，但看起來比較像揮劍，不太像開心跳躍。如果想讓劍保持朝下，可以把劍或右手的動作幅度調小。
- **Idle 時劍尖會微微離開地面**：劍跟著手臂擺動，原本拄地的感覺會變弱。
- Happy 模板是站姿跳躍，這個角色是站姿，可以套用。