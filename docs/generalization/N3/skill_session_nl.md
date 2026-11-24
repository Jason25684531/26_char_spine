# N3 Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`請將這張角色圖拆補圖、建立骨架，製作 Idle／Happy 動畫並輸出結果：gen_n3.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash 間接證據（沒呼叫 Skill、沒讀 SKILL.md，前兩個指令就照 Skill 用 c2s）：否
- 讀過 SKILL.md 檔案：否
- 觸發後執行 c2s：是（6 次）
- 讀到答案（既有角色、其他案例、案例描述）：0 次
- 使用沙盒外的工具（呼叫專案的 c2s／python、讀原始碼）：0 次
- 工具呼叫次數：{'Bash': 2, 'PowerShell': 4, 'Read': 5, 'Skill': 1, 'Write': 2}

## c2s 指令

- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N3\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" --version`
- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N3\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" analyze gen_n3.png`
- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N3\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" run gen_n3.png`
- `cd "C:/Users/Norlan/AppData/Local/Temp/c2s_sandbox/N3/sandbox_nl/output/gen_n3" && cat missing_parts.json | head -c 3000; echo; cat quality/quality_report.json | head -c 2500`
- `python "C:\Users\Norlan\AppData\Local\Temp\c2s_sandbox\N3\sandbox_nl\.claude\skills\character-to-spine/scripts/c2s.py" run gen_n3.png | Select-String -Pattern '"status"|unassigned_ratio|needs_manual|downgraded|detail' -Context 0,2`
- `cd "C:/Users/Norlan/AppData/Local/Temp/c2s_sandbox/N3/sandbox_nl/output/gen_n3" && cat report/repair_priority.md; ls report repair_masks layers spine preview`

## 讀到答案

- 無

## 使用沙盒外的工具

- 無

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "gen_n3.png"}`
2. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" --version", "description": "Check c2s version and set up environment", "timeout": 600000}`
3. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\.claude\\skills\\character-to-spine\\references\\parts-format.md"}`
4. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" analyze gen_n3.png", "description": "Analyze character image"}`
5. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\output\\gen_n3\\grid_overlay.png"}`
6. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\gen_n3.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"leg_l\", \"polygon\": [[402,660],[458,660],[452,730],[446,760],[442,800],[362,800],[372,758],`
7. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" run gen_n3.png", "description": "Run full character-to-spine pipeline", "timeout": 600000}`
8. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\output\\gen_n3\\layer_preview.png"}`
9. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\output\\gen_n3\\report\\visual_check.png"}`
10. Bash：`{"command": "cd \"C:/Users/Norlan/AppData/Local/Temp/c2s_sandbox/N3/sandbox_nl/output/gen_n3\" && cat missing_parts.json | head -c 3000; echo; cat quality/quality_report.json | head -c 2500", "description": "Show unassigned regions and quality report"}`
11. Write：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\gen_n3.parts.json", "content": "{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"leg_l\", \"polygon\": [[400,660],[460,660],[455,730],[450,760],[446,800],[356,800],[364,754],`
12. PowerShell：`{"command": "python \"C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\.claude\\skills\\character-to-spine/scripts/c2s.py\" run gen_n3.png | Select-String -Pattern '\"status\"|unassigned_ratio|needs_manual|downgraded|detail' -Context 0,2", "description": "Rerun pipeline with rev`
13. Read：`{"file_path": "C:\\Users\\Norlan\\AppData\\Local\\Temp\\c2s_sandbox\\N3\\sandbox_nl\\output\\gen_n3\\report\\visual_check.png"}`
14. Bash：`{"command": "cd \"C:/Users/Norlan/AppData/Local/Temp/c2s_sandbox/N3/sandbox_nl/output/gen_n3\" && cat report/repair_priority.md; ls report repair_masks layers spine preview", "description": "Show repair priority and output listing"}`

## 最後回覆（原文）

拆圖、骨架和 Idle／Happy 動畫都做好了，Spine JSON 也已輸出，但**整體狀態是 BLOCKED**：身體圖層（`body`）需要人工補畫，而且這台電腦裝的是 Spine 試用版，沒辦法產生 `.spine` 專案檔。

## validation_report.json 各項狀態

| 檢查 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 8 根骨頭，階層順序正確 |
| slots | PASS | 6 個插槽都對應到骨頭與圖片 |
| image_references | PASS | 圖片都存在、尺寸相符、不是空白 |
| animations | PASS | Idle 2.0 秒；Happy 2.4 秒 |
| setup_pose | PASS | 骨架初始姿勢與原圖差異 0.0012 |
| animation_quality | PASS | 以 10 fps 加上所有關鍵影格逐格檢查，沒有破洞、關節縫隙或接觸分離（採用第 3 輪自動修正） |
| manual_repairs | **BLOCKED** | `body` 需要人工補畫 |
| spine_import | **BLOCKED** | 偵測到 Spine 試用版，不能存專案也不能匯出，所以沒有 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法驗證匯入後再匯出是否一致 |
| spine_editable | NOT_TESTED | 要在 Spine Editor 裡開啟並改關鍵影格才能確認 |

## 我做的調整
- 拆成 6 個部件：`head`、`body`、`arm_l`（舉高拳頭那隻手）、`arm_r`（胸前握拳那隻手）、`leg_l`、`leg_r`。
- 第一版有 2.4% 的角色像素沒分到任何部件（頭髮頂端、手臂外框、短褲和鞋子邊緣）。放大範圍後降到 0.16%，只剩頭髮頂端幾個像素。
- 第一版的 Happy 在 t=0.5s 時，舉起的手臂會甩到頭的另一側。我把這隻手臂的動作幅度降一半，現在會變成往正上方揮拳。

## 輸出位置（`output/gen_n3/`）
- `layers/`：分層 PNG
- `spine/character.json`：Spine JSON（圖片在 `spine/images/`）
- `preview/idle_python_simulation_preview.gif`、`preview/happy_python_simulation_preview.gif`：這是 **Python Simulation Preview**，不是 Spine 算圖
- `validation_report.json`
- `report/visual_check.png`

## 需要人工補畫的部件（依 `report/repair_priority.md` 的順序）
1. **`body`（高）**：約 34% 被頭和兩隻手遮住，Happy t=0.5s 會露出 5%。被擋住的身體輪廓（約 30%）和衣服紋理要照原圖重畫。對照圖在 `report/repair_body.png`。

以下目前是自動補的草稿，露出量在門檻內，但建議看一下：
- `leg_l`：中，最多露出 1.7%
- `arm_l`：中，最多露出 1.7%
- `leg_r`：中，最多露出 1.5%
- `head`：低，幾乎不會露出，草稿可以保留

自動補上的區域在 `repair_masks/`，文字版待修清單在 `repair_tasks.md`，每個部件的對照圖在 `report/repair_<部件>.png`（原圖、目前圖層、動畫中露出最多的三格）。

**修好之後**：把修好的 PNG 給我，我會執行 `c2s prepare --replace body=<修好的.png>`，再重跑 `c2s run gen_n3.png`。

## 自動檢查沒抓到的問題
- Happy t=0.5s 手臂舉到頭頂時，左肩外側會露出一塊鋸齒狀的深藍色。那裡就是 `body` 的補圖草稿，補畫 `body` 時請一起處理左肩袖口附近。
- 頭髮頂端還有極少量像素沒分到部件，畫面上幾乎看不出來。