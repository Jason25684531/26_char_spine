# Character-to-Spine Skill v1.0：實際使用與測試報告

日期：2026-11-24。分支 `feat/character-to-spine-mvp`（未合併、未推送）。

## 1. 交付的 Skill

| 項目 | 內容 |
|---|---|
| 套件 | `dist/character-to-spine-skill-v1.0.0.zip`（由 `scripts/build_skill.py` 產生）；交付目錄 `Character-to-Spine-Deliverables/00_Skill_v1.0/` |
| 內容 | `SKILL.md`、`references/parts-format.md`、啟動器 `scripts/c2s.py`（只用標準函式庫）、`core/character_to_spine-1.0.0-py3-none-any.whl`、`core/constraints.txt` |
| 安裝 | 解壓到 `<專案>\.claude\skills\` 或 `%USERPROFILE%\.claude\skills\`（README「新使用者：安裝 Claude Skill」） |
| 執行環境 | 第一次執行時，啟動器在 Skill 資料夾內建立 `.venv` 並安裝 wheel，不使用開發者的 `.venv` 或任何絕對路徑 |
| 需要 | Claude Code、Python 3.11 以上、第一次使用時可連網。不需要 API Key、付費服務或 AI 影像模型 |

## 2. 新使用者驗收（真正的 Claude Code，不是模擬）

方法（`scripts/acceptance.py`）：

1. 在 repo 外建立空資料夾，用 README 寫的 `Expand-Archive` 解壓 zip 到 `.claude\skills`。
2. 放入一張未參與開發的圖片 `examples/acceptance/music_fan.png`（Openclipart，CC0）。
3. 執行 `claude -p "<一句話>"`：stream-json 紀錄；PATH 移除本專案；`--setting-sources project,local` 不載入使用者層設定；`--strict-mcp-config` 不載入 MCP。

| 驗收 | 提問 | Skill 觸發 | 自己寫 parts.json | c2s 由 Skill 的 .venv 執行 | 讀到不該讀的檔 | 沙盒外動作 | 回覆語言 |
|---|---|---|---|---|---|---|---|
| 自然語言 | 「請將這張角色圖拆補圖、建立骨架，製作 Idle／Happy 動畫並輸出結果：music_fan.png」 | 是（Skill 工具呼叫） | 是 | 是 | 0 | 0 | 中文 |
| `/character-to-spine music_fan.png` | slash 呼叫 | 是（slash 展開後第一步就執行 Skill 的指令，沒有另外讀 SKILL.md） | 是 | 是 | 0 | 0 | 中文 |
| 自然語言（最終 zip 重驗，與交付 zip 同一個 SHA-256 `5453eec8…0aa2`） | 同第一列 | 是 | 是 | 是 | 0 | 0 | 中文 |

兩次驗收都產生了下列輸出：
- 分層透明 PNG：head、body、banner、arm_l、arm_r、leg_l、leg_r。
- Spine JSON：`spine/character.json`。
- Idle／Happy 的 Python Simulation Preview GIF。
- 驗證與品質報告：`validation_report.json`、`quality/quality_report.json`。
- 補畫資料：`report/repair_priority.md`、`report/repair_<部件>.png`、`repair_masks/`、`repair_tasks.md`。

驗證結果：bones、slots、image_references、animations、setup_pose、animation_quality 都是 PASS。manual_repairs 是 BLOCKED（body 需補畫），spine_import 是 BLOCKED（只有試用版），spine_roundtrip 與 spine_editable 是 NOT_TESTED。

Claude 自己做了這些事：
- 判斷布條是雙手共同拿著的道具。
- 發現頭髮、布條、鞋邊有未分配像素，自己擴大部件後重跑。
- 把飄浮的音符留在特效、不放進部件。
- 看過 `visual_check.png` 後指出手臂圖層只有手掌。

使用者沒有執行任何指令。目視：雙手與布條在 Idle／Happy 每格都接觸、沒有破圖，但動作偏保守，主要是整體跳躍與布條擺動。

證據：`docs/acceptance/`（判定與最後回覆）。原始 stream-json 在 `output/acceptance/<名稱>/session.jsonl`，沙盒保留在 `%TEMP%\c2s_acceptance\`。

## 3. 其他真實 Skill session

同樣的沙盒方式（`scripts/generalization.py skill <案例>`），每次都是全新的 `claude -p`，提問都是上面那一句：

| 案例 | 圖片 | 觸發 | 寫出 parts.json | 讀到不該讀的檔 | 沙盒外動作 | 回覆語言 |
|---|---|---|---|---|---|---|
| rq | `人物 拷贝.png`（開發參考圖，邊跑邊彈吉他） | 是 | 是 | 0 | 0 | 中文 |
| yz | `预中奖.png`（開發參考圖，大量飄落花瓣） | 是 | 是 | 0 | 0 | 中文 |
| N1 | Q 版老法師（持杖、杖頭發光） | 是 | 是 | 0 | 0 | **英文** |
| N2 | 女騎士（盔甲、單手扶劍） | 是 | 是 | 0 | 0 | 中文 |
| N3 | 男孩（握拳伸向鏡頭） | 是 | 是 | 0 | 0 | 中文 |
| N4 | Togo-kun（單色吉祥物、叉腰） | 是 | 是 | 0 | **8**（在沙盒上一層寫診斷腳本） | 中文 |

N1 的英文回覆與 N4 的診斷腳本違反 Skill 規則（K-36）。SKILL.md 已補強：語言規則移到開頭，並明確禁止寫診斷程式。補強後的三次驗收都遵守。

yz 第一次 session 失敗，原因是沙盒複製到正在重建的 `dist/`（`core/` 是空的）。Skill 照實回報 BLOCKED，沒有自己寫替代程式。這是測試時序問題，重跑成功。

## 4. 程式修正與前後比較

| 問題 | 修正 | 證據 |
|---|---|---|
| K-24 破洞誤判 | 只算「初始被某部件蓋住、現在透明、而該部件已離開」的被包圍像素（D-42） | C、H1、H2 的 `hole:character` 消失 |
| K-24 縫隙量錯關節 | 依身體結構選關節（D-43） | `test_gap_joint_follows_skeleton_not_largest_contact` |
| K-28 持物骨架顛倒 | 單手 → 道具掛在手下；雙手 → 手掛在道具下（D-44） | H2 拿夾板的手 0.9%→15.5%、C 拿杖的手 1.2%→4.1%、獨立目視 H2、C、N1、N2 的持物關係正確 |
| 過度縮小動作 | refine 減半後以 √2 回升（D-45） | B arm_r 4.2%→5.9%、D 雙手 0.8%→1.2%；`test_refine_does_not_over_reduce` |
| 影子混入腳、靴子、裙襬 | 影子只保留影子，被擋住處平塗（D-49，三輪） | E、C、N2 的影子圖層只剩影子 |
| K-30 Skill 依賴專案腳本 | 報告成為 `c2s run` 的最後一步（D-47） | 沙盒 session 都沒有跑回本專案 |
| K-26 依賴開發者 `.venv` | Skill 自帶啟動器與 wheel（D-48） | 第 2、3 節 |

補圖演算法比較過三種（Telea、最近色、金字塔），沒有一種同時在量測與目視上勝出，維持 Telea（D-46）。無法可靠補的部位照舊輸出遮罩、三格補畫參考與待修清單，不當成完成品。

泛化判定（`docs/GENERALIZATION_TEST_MATRIX.md`，規則與門檻沿用前一階段凍結的版本）：

| 案例 | 改動前（HEAD 基準） | 改動後 |
|---|---|---|
| A | PARTIAL | PARTIAL |
| B | PARTIAL | PARTIAL |
| C | FAIL（破洞誤判） | PARTIAL（破洞誤判消失；影子不再留下裙襬） |
| D | FAIL | FAIL（雙手動作 1.2% < 2%，被草稿露出限制） |
| E | PARTIAL | PARTIAL（地上不再留下腳尖） |
| ren | PARTIAL | PARTIAL |
| zc2 | PARTIAL | FAIL（arm_r 縮到 ×0.125，混到一次 gap，依規則算演算法限制；手的動作量 0.4%→0.8%） |
| H1 | FAIL（破洞誤判） | PARTIAL |
| H2 | FAIL（破洞誤判、骨架顛倒） | PARTIAL |
| H3 | PARTIAL | FAIL（同 zc2；手的動作量 0.4%→4.1%） |
| H4 | FAIL | FAIL（坐姿只剩整體跳動） |

zc2 與 H3 降級的原因：改用肩膀當關節後，量到一次 gap，判定規則就把整個縮小歸為演算法限制。這兩個案例的手實際上動得更多。判定規則不在執行後修改。

## 5. 保留集 N1–N4（預登記後第一次執行）

N1–N4 在所有程式修改完成後預登記（提交 `9e03fe5`），之後才第一次執行。第一次執行的結果（快照 `v1_final`）：

| 案例 | 等級 | 主要原因 |
|---|---|---|
| N1 | FAIL | 未分配前景 2.5%，全是法杖頂端被正確排除的光芒（K-35，評估限制）；arm_r 因穿插縮到 ×0.125 |
| N2 | FAIL | 獨立目視：影子圖層切進靴子、劍尖（分層 BAD）。之後以 D-49 修正為 PARTIAL，N2 因此不再是盲測 |
| N3 | PARTIAL | body 需補畫；舉拳動作明顯 |
| N4 | FAIL | `setup_pose` 0.0226 > 0.02（柔和投影，K-34），c2s 結束碼 1 |

保留集沒有一張 PASS。可以處理的人形角色都產生了完整的分層、骨架、動畫與報告。程式沒有為任何一張圖寫死座標或改核心規則。

## 6. 回歸測試

`pytest`：改動前 148 passed；最終 **153 passed**（交付目錄 `07_Test_Reports/pytest_output.txt`、`pytest.xml`）。新增的回歸測試都先確認在修正前失敗：
- 破洞與縫隙：`test_real_holes_only_count_what_a_departed_part_used_to_cover`、`test_gap_joint_follows_skeleton_not_largest_contact`。
- 持物骨架：`test_single_hand_holds_prop_as_child`。
- 過度縮小：`test_refine_does_not_over_reduce`。
- 影子：`test_ground_shadow_keeps_only_shadow_pixels`、`test_ground_shadow_behind_feet_stays_shadow`。

## 7. 尚未完成、需要外部條件的項目

- **`.spine` 專案、往返驗證、Editor 可編輯性：BLOCKED**。這台機器只有 Spine 試用版（K-01）。取得 Essential 或 Professional 授權後，設定 `SPINE_EXE` 重跑即可。Python Simulation Preview 不是 Spine 算圖。
- **人工補畫**：每個角色的 `repair_priority.md` 都列出需補畫的部件與優先順序，例如 `人.png` 的 hair_back、leg_l、leg_r、body。
- **動作品質的限制**：
  - 需人工部件的草稿在補畫前不讓它露出（D-36），所以有些手臂被縮小。補畫並以 `--replace` 匯回後會自動放寬。
  - Happy 是站姿跳躍模板，跑步、坐姿只剩整體跳動（K-37）。
- **測試環境**：所有 Skill 實測都在同一台機器與 Claude 帳號上執行（K-31）。
