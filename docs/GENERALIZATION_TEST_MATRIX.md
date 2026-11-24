# 泛化測試矩陣

由 `python scripts/generalization.py report` 依 `output/generalization/results.json` 產生，請勿手改。
所有等級都用目前登記的同一套規則重算；變更見 `examples/generalization/manifest.json` 的 criteria_changes。

## 成功率（只計真實陌生角色；格式：成功 PASS｜可處理 PASS＋PARTIAL｜各等級）

- 開發集（dev）：A–E。第一次盲測後依它們的失敗修改過 Skill 與程式，之後的結果**不是泛化證據**。
- 保留集（holdout）：所有修改完成前登記、未曾執行，泛化結論以它與開發集的第一次盲測（baseline）為準。
- UNSUPPORTED 不計入成功；合成角色不計入任何比率。

| 快照 | 開發集 | 保留集 |
|---|---|---|
| baseline | 0/5｜1/5｜PARTIAL 1、FAIL 4 | — |
| 目前 | 0/5｜1/5｜PARTIAL 1、FAIL 4 | — |

## 案例（目前）

| 案例 | 集 | 類型 | 預期 | 等級 | Skill 觸發 | 來源查核 | 重組 MAE | 未分配 | 未持物手臂 | 持物手臂 | 只剩跳動 | 循環 | 需人工 | absent | 主要理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | dev | front-chibi | supported | **PARTIAL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00116 | 0.02% | arm_l 4.4%、arm_r 5.0% | — | 否 | 是 | leg_l, leg_r, body, skirt | — | 需人工修補：leg_l, leg_r, body, skirt；arm_r 被自我修正縮到 ×0.125（素材限制：['exposure']）；arm_l 被自我修正縮到 ×0.125（素材限制：['exposure']）；目視 motion：happy 以整體跳躍與辮子擺動為主；手臂被縮到 ×0.125（草稿露出），只剩小幅擺動（4.4%～5.0%）；目視 occlusion：舉手時裙子兩側露出條狀草稿，一眼可辨（repair_skirt.png）；已列人工修補 |
| B | dev | three-quarter | supported | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00079 | 0.09% | arm_r 12.6% | arm_l 0.6% | 否 | 是 | — | — | 目視 joints：腿完全被長裙蓋住，裙子左右兩半被當成 leg_l／leg_r，捏造了看不見的腿（判準：捏造結構） |
| C | dev | prop | supported | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.01045 | 0.03% | — | arm_r 1.9%、arm_l 1.1% | 否 | 是 | shadow, hair_l, hair_r, leg_r | — | 品質未解：hole:character；目視 joints：body 的 pivot（hip）在裙襬最底下，身體旋轉繞著腳底轉，整件裙子跟著傾斜；目視 motion：四肢在關鍵影格中看不出動作，只剩整體上下跳：長杖 0%、腿 0%、兩手 1%～2%（判準：只剩跳動） |
| D | dev | occlusion | partial | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.0015 | 0.05% | arm_l 1.9%、arm_r 1.2% | — | 否 | 是 | hair_back, body | — | 未持物手臂 arm_l 動作量 1.9% < 2%；未持物手臂 arm_r 動作量 1.2% < 2% |
| E | dev | non-humanoid | partial | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00175 | 0.33% | arm_l 4.1%、arm_r 6.6% | — | 否 | 是 | shadow, cape, horn, leg_l, body | — | arm_r 被自我修正縮到 ×0.125（演算法限制：['exposure', 'hole']） |
| ren | legacy | regression | supported | **PARTIAL** | — | — | 0.00141 | 0.01% | — | arm_l 0.8%、arm_r 1.9% | 否 | 是 | hair_back, leg_l, leg_r, body | — | 需人工修補：hair_back, leg_l, leg_r, body；目視 motion：抱吉他的手動作很小（已知 K-17、K-18），以整體跳躍加頭髮、裙擺為主；目視 occlusion：被遮的身體、腿、頭髮草稿已列人工修補（已知 K-07） |
| zc2 | legacy | regression | supported | **PARTIAL** | — | — | 0.0014 | 0.72% | arm_l 12.9% | arm_r 0.4% | 否 | 是 | hair_back, leg_l, leg_r, body | — | 需人工修補：hair_back, leg_l, leg_r, body；目視 occlusion：被遮的身體、腿、頭髮草稿已列人工修補（已知 K-07） |

## 驗證器原始狀態（PASS／FAIL／BLOCKED／NOT_TESTED）

- A：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- B：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs PASS、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- C：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality BLOCKED、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- D：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- E：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- ren：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- zc2：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED

## 自動量測與目視判斷（分開記錄）

| 案例 | Agent 目視：分層 | 關節 | 動作 | 遮擋補圖 | 使用者目視 | 補圖最大露出（自動） | 各肢體 happy 動作量（自動） |
|---|---|---|---|---|---|---|---|
| A | OK：重組與原圖看不出差異；帽子、辮子、裙子邊界乾淨 | OK：頭在脖子、手臂在肩膀、腿在髖部 | MINOR：happy 以整體跳躍與辮子擺動為主；手臂被縮到 ×0.125（草稿露出），只剩小幅擺動（4.4%～5.0%） | MINOR：舉手時裙子兩側露出條狀草稿，一眼可辨（repair_skirt.png）；已列人工修補 | NOT_TESTED | body 5.2%、braid_l 1.4%、braid_r 1.7%、leg_l 10.8%、leg_r 3.4%、skirt 14.9% | braid_l 3.4%、braid_r 4.0%、leg_l 1.2%、leg_r 2.2%、skirt 0.5%、arm_l 4.4%、arm_r 5.0% |
| B | OK：重組一致 | BAD：腿完全被長裙蓋住，裙子左右兩半被當成 leg_l／leg_r，捏造了看不見的腿（判準：捏造結構） | OK：舉拳的手明顯揮動（12.6%），雙馬尾擺動；提裙的手有接觸約束，幅度小合理 | OK：所有補圖露出 < 2%，驗收圖尺寸看不出痕跡（未逐格放大） | NOT_TESTED | body 1.7%、hair_l 1.5%、hair_r 1.4%、leg_l 1.4%、leg_r 0.1% | leg_l 1.9%、leg_r 1.7%、arm_l 0.6%、hair_l 0.7%、hair_r 1.2%、arm_r 12.6% |
| C | OK：重組一致；長杖、帽子、斗篷分開 | BAD：body 的 pivot（hip）在裙襬最底下，身體旋轉繞著腳底轉，整件裙子跟著傾斜 | BAD：四肢在關鍵影格中看不出動作，只剩整體上下跳：長杖 0%、腿 0%、兩手 1%～2%（判準：只剩跳動） | MINOR：頭髮、影子草稿露出約 2%～2.7%，已列人工修補 | NOT_TESTED | body 0.5%、hair_l 2.6%、hair_r 2.7%、leg_r 2.2%、shadow 2.0%、staff 1.5% | hair_l 0.3%、hair_r 0.4%、leg_l 0.0%、leg_r 0.0%、staff 0.0%、arm_r 1.9%、arm_l 1.1% |
| D | OK：重組一致 | MINOR：腿的 pivot 在裙襬下緣（約膝蓋高度），happy 時雙腿從膝部張開；上半截被裙子遮住（判準：MINOR） | MINOR：雙腿明顯踢動（約 11.7%）；拿相機的雙手幾乎不動（1.2%～1.9%） | MINOR：腿的可靠補圖露出 17% 但放大後看不出接縫（exposure_legs.png）；hair_back、body 草稿已列人工修補 | NOT_TESTED | arm_l 0.3%、body 3.5%、camera 0.8%、hair_back 2.9%、head 1.5%、leg_l 17.9%、leg_r 17.4%、skirt 0.0% | hair_back 1.3%、leg_l 11.6%、leg_r 11.8%、skirt 1.4%、arm_l 1.9%、arm_r 1.2% |
| E | OK：重組一致；角、圍巾、披風、尾巴分開 | OK：以人形骨架套在雙足龍上，肩、頸、胯的位置合理 | MINOR：尾巴與披風隨跳躍擺動、舉起的手小幅揮動；地面影子跟著角色離地（判準：MINOR） | MINOR：披風、影子草稿露出約 7%～8%，已列人工修補 | NOT_TESTED | arm_l 0.7%、body 1.0%、cape 7.4%、head 0.6%、horn 2.7%、leg_l 5.5%、leg_r 0.7%、scarf 0.1%、shadow 7.9%、tail 1.6% | cape 2.2%、tail 2.0%、horn 1.4%、leg_l 3.1%、leg_r 1.4%、arm_l 4.1%、arm_r 6.6% |
| ren | OK：重組一致 | OK：與既有交付相同 | MINOR：抱吉他的手動作很小（已知 K-17、K-18），以整體跳躍加頭髮、裙擺為主 | MINOR：被遮的身體、腿、頭髮草稿已列人工修補（已知 K-07） | NOT_TESTED | body 2.0%、guitar 1.3%、hair_back 3.2%、head 1.0%、leg_l 3.4%、leg_r 3.2%、skirt 0.7% | hair_back 3.0%、leg_l 4.8%、leg_r 4.6%、skirt 3.9%、guitar 1.0%、arm_l 0.8%、arm_r 1.9% |
| zc2 | OK：重組一致；散落花瓣依規定不屬於任何部件 | OK：與既有交付相同 | OK：舉起的手揮動明顯（12.9%） | MINOR：被遮的身體、腿、頭髮草稿已列人工修補（已知 K-07） | NOT_TESTED | arm_extra 7.2%、arm_l 4.1%、body 1.6%、hair_back 1.8%、head 1.2%、leg_l 10.2%、leg_r 2.0%、petals 1.0%、skirt 0.4% | hair_back 3.2%、leg_l 5.2%、leg_r 5.6%、skirt 4.4%、arm_l 12.9%、petals 0.6%、arm_r 0.4% |
