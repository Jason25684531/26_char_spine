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
| skill_v2 | 0/5｜0/5｜FAIL 2、NOT_TESTED 3 | — |
| final | 0/5｜3/5｜PARTIAL 3、FAIL 2 | 0/4｜1/4｜PARTIAL 1、FAIL 3 |
| v1_before | 0/5｜3/5｜PARTIAL 3、FAIL 2 | 0/4｜1/4｜PARTIAL 1、FAIL 3 |
| v1_k24k28 | 0/5｜4/5｜PARTIAL 4、FAIL 1 | 0/4｜2/4｜PARTIAL 2、FAIL 2 |
| v1_regrow | 0/5｜3/5｜PARTIAL 3、FAIL 2 | 0/4｜2/4｜PARTIAL 2、FAIL 2 |
| v1_final | 0/5｜4/5｜PARTIAL 4、FAIL 1 | 0/4｜2/4｜PARTIAL 2、FAIL 2 |
| v1_final2 | 0/5｜4/5｜PARTIAL 4、FAIL 1 | 0/4｜2/4｜PARTIAL 2、FAIL 2 |
| 目前 | 0/5｜4/5｜PARTIAL 4、FAIL 1 | 0/4｜2/4｜PARTIAL 2、FAIL 2 |

## 案例（目前）

| 案例 | 集 | 類型 | 預期 | 等級 | Skill 觸發 | 來源查核 | 重組 MAE | 未分配 | 未持物手臂 | 持物手臂 | 只剩跳動 | 循環 | 需人工 | absent | 主要理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | dev | front-chibi | supported | **PARTIAL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00151 | 0.00% | arm_l 2.1%、arm_r 4.9% | — | 否 | 是 | leg_l, leg_r, body, skirt | — | 需人工修補：leg_l, leg_r, body, skirt；arm_l 被自我修正縮到 ×0.125（素材限制，被 skirt 的草稿露出拖累）；目視 joints：骨架圖 leg_l/leg_r 的 pivot 在裙襬下緣（可見部分起點），大腿上段被裙子遮住；arm 在肩、braid 在耳側、head 在頸，位置正確；目視 occlusion：happy t=0.5 右手旁裙側出現淡色補圖、兩腿間有補圖縫（repair_skirt/leg_l 紅區），skirt、leg |
| B | dev | three-quarter | supported | **PARTIAL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00097 | 0.45% | arm_r 5.9% | arm_l 1.6% | 否 | 是 | — | leg_l, leg_r | 宣告看不到：leg_l, leg_r；目視 occlusion：左手拉裙處在 happy t=0.2/0.5/1.4 手和裙襬接點稍微錯開，露出一小段黑線；其他沒有明顯破洞。 |
| C | dev | prop | supported | **PARTIAL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00681 | 0.18% | arm_r 5.6% | arm_l 4.1% | 否 | 是 | hair_back, body | leg_l, leg_r | 需人工修補：hair_back, body；宣告看不到：leg_l, leg_r；目視 layers：影子層本身乾淨（純黑低透明橢圓、無腳或裙襬像素），鞋子正確歸在裙子並隨跳躍離地；但裙子層下緣夾帶一條灰色影子帶，Happy 跳起時跟著裙襬離地；hair_back 仍為 needs_manual；目視 motion：Happy 除跳躍外有身體 8° 傾、雙臂 15–18°、杖隨手擺動，不是只剩整體跳；但持杖臂與叉腰臂幅度都小，Idle 幾乎只有呼吸與頭 3°；目視 occlu |
| D | dev | occlusion | partial | **FAIL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00141 | 0.07% | arm_r 1.2%、arm_l 1.2% | — | 否 | 是 | hair_back, body | — | 未持物手臂 arm_r 動作量 1.2% < 2%；未持物手臂 arm_l 動作量 1.2% < 2% |
| E | dev | non-humanoid | partial | **PARTIAL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00183 | 0.43% | arm_l 19.0%、arm_r 5.9% | — | 否 | 是 | cape, horn, leg_l, leg_r, arm_l | — | 需人工修補：cape, horn, leg_l, leg_r, arm_l；arm_r 被自我修正縮到 ×0.125（素材限制，被 body、cape、horn 的草稿露出拖累）；目視 layers：影子層只有灰色影子、無綠色腳部像素，但被腳遮住處平塗成腳形尖角與缺口，跳起時地上留下帶尖角的怪形灰影；跳起時腳下另有淡灰／白色殘邊跟著離地；leg_l、leg_r、cape 為 needs_manual；目視 joints：腿 pivot 在髖、小手在肩、尾巴在尾根，未見繞錯關節 |
| ren | legacy | regression | supported | **PARTIAL** | — | — | 0.00141 | 0.01% | — | arm_l 0.8%、arm_r 1.9% | 否 | 是 | hair_back, leg_l, leg_r, body | — | 需人工修補：hair_back, leg_l, leg_r, body；目視 layers：hair_back 圖層保留了吉他琴頸與琴頭像素：happy t=0.4/0.5 吉他轉動後出現兩個琴頭（重影），手與琴頸間還有一道白縫；hair_back 已列 needs_manual，露出位置與 repair_hair_back (c) 紅區一致；目視 joints：leg_l/leg_r pivot 在裙襬下緣（只露出靴子）；arm 在肩、guitar 在琴身中心、head 在 |
| zc2 | legacy | regression | supported | **FAIL** | — | — | 0.0014 | 0.72% | arm_l 12.9% | arm_r 0.8% | 否 | 是 | hair_back, leg_l, leg_r, body, petals | — | arm_r 被自我修正縮到 ×0.125（演算法限制：['exposure', 'gap']，被 body 的草稿露出拖累） |
| H1 | holdout | front-chibi | supported | **PARTIAL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00547 | 0.13% | arm_l 16.7%、arm_r 30.8% | — | 否 | 是 | body | —（預登記持物手 0、宣告 0） | 需人工修補：body；目視 joints：骨架格中 arm_l 和 arm_r 的 pivot 在肩頭，head 在頸部，body/hip 在腰帶，父子關係都是 hip→body→head/arms 和 hip→legs，正確。leg_l 和 leg_r 的 pivot 在裙襬下緣（膝上），大腿被裙子遮住，屬於判準中的 MINOR。；目視 occlusion：body 的自動補圖是灰黑色的模糊條紋，在 happy t=0.4–0.7 和 t=1.6–2.0 明顯露出在腰和手臂 |
| H2 | holdout | prop-adult | supported | **PARTIAL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00325 | 0.00% | arm_r 6.6% | arm_l 15.5% | 否 | 是 | leg_l, body | —（預登記持物手 1、宣告 1） | 需人工修補：leg_l, body；arm_r 被自我修正縮到 ×0.125（素材限制，被 body 的草稿露出拖累）；目視 occlusion：叉腰手移開後，腰側有小塊白色缺口；body 降級為 needs_manual，leg_l 數值露出 27.7%，但畫面上不算明顯。 |
| H3 | holdout | prop-occlusion | supported | **FAIL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00468 | 0.03% | arm_l 2.2% | arm_r 4.1% | 否 | 是 | hair_back, body, book | —（預登記持物手 1、宣告 1） | arm_r 被自我修正縮到 ×0.125（演算法限制：['exposure', 'gap']，被 body 的草稿露出拖累） |
| H4 | holdout | sitting-anthro | partial | **FAIL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00131 | 0.57% | arm_l 3.0%、arm_r 5.1% | — | 否 | 是 | tail, body, leg_r | —（預登記持物手 0、宣告 0） | arm_r 被自我修正縮到 ×0.125（演算法限制：['exposure', 'gap']，被 body、leg_r、tail 的草稿露出拖累）；目視 motion：happy 4 格中整個坐姿角色原樣跳離地面（t=0.5 連腳一起騰空）。雙腿幾乎不動（約 ±2°），右臂只有約 7°，拿筆的手約 8°。比對 t=0、0.2、0.5、0.9，四肢位置幾乎沒有變化，只剩頭部傾斜和尾巴小擺。符合「動作只剩整體跳動，四肢在關鍵影格中看不出動作」。 |
| rq | legacy | regression | supported | **PARTIAL** | — | — | 0.00088 | 0.16% | — | arm_l 0.8%、arm_r 2.5% | 否 | 是 | hair_back, leg_l, leg_r, body | — | 需人工修補：hair_back, leg_l, leg_r, body；目視 joints：pivot 位置大致正確（頭在頸、手臂在肩、後髮在頭頂）；但父子關係是 arm_l/arm_r 掛在 guitar 底下（body→guitar→arms），持物階層倒過來，靠吉他轉動帶手臂，視覺上沒有顛倒但不符合手持物的慣例、難以在 Spine 裡手動調；目視 motion：happy 主要是整體跳起加頭部擺動，手臂與吉他只小幅擺動，雙腿幾乎不動；idle 幾乎靜止 |
| yz | legacy | regression | supported | **FAIL** | — | — | 0.00087 | 1.56% | arm_l 15.8% | arm_r 4.4% | 否 | 是 | hair_back, leg_l, leg_r, body, arm_r | — | 未分配前景 1.6% > 1% |
| N1 | holdout2 | prop-effect-chibi | supported | **FAIL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00399 | 2.54% | arm_l 6.4% | arm_r 2.7% | 否 | 是 | leg_l, leg_r, body | —（預登記持物手 1、宣告 1） | 未分配前景 2.5% > 1%；arm_r 被自我修正縮到 ×0.125（演算法限制：['intrude']） |
| N2 | holdout2 | prop-armor | supported | **PARTIAL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00443 | 0.01% | arm_l 5.2% | arm_r 22.5% | 否 | 是 | hair_back, leg_l, leg_r, body | —（預登記持物手 1、宣告 1） | 需人工修補：hair_back, leg_l, leg_r, body；arm_l 被自我修正縮到 ×0.125（素材限制，被 arm_l、body 的草稿露出拖累）；目視 layers：影子層只有低透明深色影子，腳的位置挖出缺口，跳起時地上沒有留下靴子或戰袍碎片；但跳起時腳下仍跟著一條淡灰殘影，戰袍下緣有白色鋸齒，body、雙腿為 needs_manual；目視 occlusion：Happy 舉劍時胸甲右側露出棕色碎片（body 補畫草稿）與肩部暗縫；leg_r 露出 0 |
| N3 | holdout2 | dynamic-foreshortened | supported | **PARTIAL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.00056 | 0.16% | arm_l 52.0%、arm_r 3.2% | — | 否 | 是 | body | —（預登記持物手 0、宣告 0） | 需人工修補：body；arm_r 被自我修正縮到 ×0.125（素材限制，被 body 的草稿露出拖累）；目視 joints：手臂 pivot 在肩、頭在頸都正確；腿 pivot 在短褲下緣（可見部分起點），短褲跟著 body 走；目視 occlusion：happy t=0.5 手臂轉開後肩膀露出紅色草稿與鋸齒狀藍色袖子碎片（body 露出 5%），而 body 只標 auto_repaired、沒有列入人工補畫 |
| N4 | holdout2 | flat-mascot-akimbo | supported | **FAIL** | 是（c2s 由 Skill 自己建立的 .venv 提供） | PASS | 0.02244 | 0.37% | arm_l 62.5%、arm_r 55.1% | — | 否 | 是 | body | —（預登記持物手 0、宣告 0） | c2s 結束碼 1 |

## 驗證器原始狀態（PASS／FAIL／BLOCKED／NOT_TESTED）

- A：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- B：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs PASS、absent_parts BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- C：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、absent_parts BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- D：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- E：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- ren：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- zc2：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- H1：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- H2：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- H3：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- H4：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- rq：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- yz：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- N1：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- N2：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- N3：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- N4：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose FAIL、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED

## 自動量測與目視判斷（分開記錄）

| 案例 | Agent 目視：分層 | 關節 | 動作 | 遮擋補圖 | 使用者目視 | 補圖最大露出（自動） | 各肢體 happy 動作量（自動） |
|---|---|---|---|---|---|---|---|
| A | OK：圖層重組與原圖幾乎一致；帽子、雙辮、手臂、裙子、雙腿分開，前後順序正確，沒看到漏切或重複 | MINOR：骨架圖 leg_l/leg_r 的 pivot 在裙襬下緣（可見部分起點），大腿上段被裙子遮住；arm 在肩、braid 在耳側、head 在頸，位置正確 | OK：happy t=0.5 雙臂比 t=0 外展約 20–30°、雙辮擺動、頭側傾、雙腳略收，不是只有整體跳動；t=0.2 有下蹲預備 | MINOR：happy t=0.5 右手旁裙側出現淡色補圖、兩腿間有補圖縫（repair_skirt/leg_l 紅區），skirt、leg_l 都已列 needs_manual | NOT_TESTED | body 2.7%、braid_l 1.9%、braid_r 1.3%、leg_l 9.1%、leg_r 2.6%、skirt 9.3% | braid_l 1.9%、braid_r 1.9%、leg_l 2.0%、leg_r 2.3%、skirt 0.2%、arm_l 2.1%、arm_r 4.9% |
| B | OK：長洋裝角色沒有捏造雙腿，裙子整片一層；頭、雙側髮束、雙臂分層合理，重組與原圖一致。 | OK：arm_l/arm_r pivot 在肩、head 在頸、hip/skirt 在腰，髮束掛在頭上，父子關係正確。 | OK：右手握拳在 Happy 明顯揮動，加上歪頭和跳起；左手拉裙襬只有小幅動作，算合理。 | MINOR：左手拉裙處在 happy t=0.2/0.5/1.4 手和裙襬接點稍微錯開，露出一小段黑線；其他沒有明顯破洞。 | NOT_TESTED | arm_l 1.4%、arm_r 2.0%、body 1.7%、hair_l 1.5%、hair_r 1.1%、skirt 0.9% | skirt 1.7%、arm_l 1.6%、arm_r 5.9%、hair_l 1.4%、hair_r 2.2% |
| C | MINOR：影子層本身乾淨（純黑低透明橢圓、無腳或裙襬像素），鞋子正確歸在裙子並隨跳躍離地；但裙子層下緣夾帶一條灰色影子帶，Happy 跳起時跟著裙襬離地；hair_back 仍為 needs_manual | OK：hip 在腰帶、arm_l／arm_r pivot 在兩肩、skirt 自腰懸掛、hat 隨 head；staff 以 arm_l 為父、pivot 在握手處，Happy 全程握點未分開（attach 0.95） | MINOR：Happy 除跳躍外有身體 8° 傾、雙臂 15–18°、杖隨手擺動，不是只剩整體跳；但持杖臂與叉腰臂幅度都小，Idle 幾乎只有呼吸與頭 3° | MINOR：各影格未見明顯破洞或部件分離；body 被降為 needs_manual（Happy t1.7 露出 0.026），重組圖帽緣與裙襬有零星殘邊像素，跳起時裙下灰帶露出 | NOT_TESTED | body 2.6%、hair_back 2.6%、head 0.5%、shadow 51613.1%、skirt 1.0%、staff 2.8% | hair_back 0.7%、staff 13.6%、skirt 2.1%、arm_r 5.6%、arm_l 4.1% |
| D | OK：相機獨立一層，頭、後髮、雙臂、圍裙裙子、雙腿分層合理，重組與原圖一致。 | MINOR：相機掛在 arm_l 下，合理；arm pivot 在肩、head 在頸。但雙腿 pivot 在裙襬下緣（可見部分起點），不在髖。 | MINOR：Happy 跳起時雙腿明顯張開；雙手捧著相機只有小幅動作（符合「持物只有小幅動作」）。 | OK：所有關鍵影格都沒有看到補圖草稿露出或破洞；相機和雙手接點沒有分開。 | NOT_TESTED | arm_l 0.9%、arm_r 0.3%、body 1.9%、hair_back 2.5%、head 1.9%、leg_l 16.2%、leg_r 15.7% | hair_back 1.3%、leg_l 8.4%、leg_r 8.6%、skirt 1.1%、arm_r 1.2%、arm_l 1.2%、camera 0.7% |
| E | MINOR：影子層只有灰色影子、無綠色腳部像素，但被腳遮住處平塗成腳形尖角與缺口，跳起時地上留下帶尖角的怪形灰影；跳起時腳下另有淡灰／白色殘邊跟著離地；leg_l、leg_r、cape 為 needs_manual | MINOR：腿 pivot 在髖、小手在肩、尾巴在尾根，未見繞錯關節；但 head、arm_r、cape、scarf pivot 擠在胸口同一點（無脖子角色可理解），horn 繞頭頂內側轉 | MINOR：Happy 小手擺動明顯（84°）、尾巴與披風 9.6°、雙腿 5–7°，不是只剩整體跳；但最醒目的指天手臂只動 7.5°（被調降到 0.125），整體看起來仍以跳為主 | MINOR：右腳與地面影子交界在 Idle／Happy 各格都有白色細縫；cape 露出 0.07 超過門檻但已列人工修補；未見大破洞或部件分離 | NOT_TESTED | arm_l 2.1%、body 1.5%、cape 7.1%、head 1.9%、horn 2.9%、leg_l 1.9%、leg_r 0.5%、scarf 0.1%、shadow 37.4%、tail 2.2% | cape 2.5%、tail 2.8%、horn 1.9%、leg_l 2.7%、leg_r 4.2%、arm_l 19.0%、arm_r 5.9% |
| ren | MINOR：hair_back 圖層保留了吉他琴頸與琴頭像素：happy t=0.4/0.5 吉他轉動後出現兩個琴頭（重影），手與琴頸間還有一道白縫；hair_back 已列 needs_manual，露出位置與 repair_hair_back (c) 紅區一致 | MINOR：leg_l/leg_r pivot 在裙襬下緣（只露出靴子）；arm 在肩、guitar 在琴身中心、head 在頸，正確 | MINOR：雙臂綁在吉他上，happy t=0.5 隨吉他轉約 15° 立起，幅度小；頭、花冠、頭髮跟著動，雙腳微動，屬持物手臂小幅動作 | MINOR：琴頭重影與 hair_back 草稿在 happy t=0.4–0.5 看得到；leg、body 草稿在裙下緣只有小片；全都已列 needs_manual | NOT_TESTED | body 2.0%、guitar 1.3%、hair_back 3.2%、head 1.0%、leg_l 3.4%、leg_r 3.2%、skirt 0.7% | hair_back 3.0%、leg_l 4.8%、leg_r 4.6%、skirt 3.9%、guitar 1.0%、arm_l 0.8%、arm_r 1.9% |
| zc2 | MINOR：原圖中散落的花瓣和左上的發光光球沒有出現在任何動畫影格（重組圖用洋紅標出大片缺失），少掉了裝飾元素；角色本體分層正確。 | MINOR：arm_l 在肩，舉起的手可以正確擺動；捧花瓣的 petals 掛在 arm_r 下，合理。但雙腿 pivot 在裙襬下緣。 | OK：Happy 時舉起的手臂往上揮，捧花瓣的手跟著動，再加上跳起和歪頭，動作清楚。 | MINOR：leg_l 在 happy t=1.6 露出約 10%，leg_r/petals 已列 needs_manual；關鍵影格裡沒有看到大塊破洞。 | NOT_TESTED | arm_extra 7.2%、arm_l 5.3%、body 2.4%、hair_back 1.8%、head 1.1%、leg_l 10.2%、leg_r 2.0%、petals 2.0%、skirt 0.4% | hair_back 1.9%、leg_l 5.2%、leg_r 5.6%、skirt 4.4%、arm_l 12.9%、petals 1.3%、arm_r 0.8% |
| H1 | OK：圖層重組格和原圖幾乎一致。前後順序正確：腿在裙下，手臂在身體前，頭和領口荷葉邊在最上層。分層合理：手臂含袖子和手套、body 含圍裙和裙子、腿只有裙襬以下的襪子和鞋。沒看到漏切或重複。body 圖層裡的灰黑條紋屬於補圖，歸在 occlusion 判。 | MINOR：骨架格中 arm_l 和 arm_r 的 pivot 在肩頭，head 在頸部，body/hip 在腰帶，父子關係都是 hip→body→head/arms 和 hip→legs，正確。leg_l 和 leg_r 的 pivot 在裙襬下緣（膝上），大腿被裙子遮住，屬於判準中的 MINOR。 | OK：happy t=0.5 雙臂明顯向外張開（左右幅度不對稱，但看起來自然），t=0.2 和 t=0.9 有身體傾斜和頭部擺動，GIF 中腳也有小幅開合，不只是整體跳動。idle 的手臂和頭部有輕微擺動。裙子和身體同一層，沒有額外的擺動。 | MINOR：body 的自動補圖是灰黑色的模糊條紋，在 happy t=0.4–0.7 和 t=1.6–2.0 明顯露出在腰和手臂兩側，idle t=0.67/1.33 的手臂邊緣也看得到。quality round_3 的 happy t=2.1 在左手套附近有破洞（hole:character）。body 已列入 needs_manual（高，露出 17.78%），所以判 MINOR；不過草稿非常醒目，必須人工補。 | NOT_TESTED | body 17.8%、leg_l 1.7%、leg_r 1.7% | leg_l 4.7%、leg_r 4.5%、arm_l 16.7%、arm_r 30.8% |
| H2 | OK：寫字板獨立一層，頭、身體、雙臂、雙腿分層正確。 | OK：寫字板掛在 arm_l 下，pivot 在手，舉起時跟著手移動；arm 在肩、腿在髖。root 偏到雙腳左側，但不影響畫面。 | OK：Happy 把寫字板高舉過肩，叉腰的手放下來，再加上跳起，四肢動作明顯。 | MINOR：叉腰手移開後，腰側有小塊白色缺口；body 降級為 needs_manual，leg_l 數值露出 27.7%，但畫面上不算明顯。 | NOT_TESTED | body 10.3%、clipboard 1.6%、leg_l 27.7%、leg_r 1.7% | leg_l 6.8%、leg_r 9.8%、arm_r 6.6%、clipboard 24.5%、arm_l 15.5% |
| H3 | OK：書本、雙臂、頭、後髮、裙、雙腿分層合理，重組與原圖一致。 | MINOR：書掛在 arm_r（抱書的手）下，合理；arm 在肩、head 在頸。但雙腿 pivot 在裙襬下緣。 | MINOR：Happy 跳起時雙腿明顯張開；抱書手和扶眼鏡手都只有小幅動作。 | MINOR：body 在 happy t=1.7 露出約 12%，book/hair_back 已列 needs_manual；關鍵影格裡沒有看到大塊破洞。 | NOT_TESTED | body 12.0%、book 1.3%、hair_back 2.9%、head 1.2%、leg_l 1.7%、leg_r 1.5% | hair_back 1.9%、leg_l 10.0%、leg_r 10.1%、skirt 0.4%、book 1.4%、arm_r 4.1%、arm_l 2.2% |
| H4 | MINOR：坐姿角色，圖層重組格和原圖幾乎一致，前後順序正確（tail 最底，手臂在腿前）。不過 arm_l 只切出拿筆的手，而且手的下緣夾帶了一點牛仔褲碎片。body 圖層有大面積灰白抹糊的補圖。兩條腿靠兩隻鞋分開，這有畫面依據，不算捏造。 | MINOR：骨架格中 hip 和雙腿 pivot 在臀部附近。坐姿的臀部本來就貼地，所以合理。head 在頸。arm_r 的 pivot 在短袖下緣（上臂中段），上臂在 body 裡，屬於「可見部分起點」的情況。arm_l 只有一隻手，pivot 在手背上方靠近軀幹處，看不到手腕和肩膀，無法確認是否對到關節。tail 的 pivot 在可見的尾巴根部，被手遮住的位置。沒看到明顯錯位，但 arm_l 的判斷沒把握。 | BAD：happy 4 格中整個坐姿角色原樣跳離地面（t=0.5 連腳一起騰空）。雙腿幾乎不動（約 ±2°），右臂只有約 7°，拿筆的手約 8°。比對 t=0、0.2、0.5、0.9，四肢位置幾乎沒有變化，只剩頭部傾斜和尾巴小擺。符合「動作只剩整體跳動，四肢在關鍵影格中看不出動作」。 | MINOR：happy t=0.5 鞋底下有一條灰色長條跟著角色騰空，這是 leg_r 鞋下補圖的露出，乍看像離地的影子。round_3 的 t=1.7 在軀幹和衣服接縫、右臂旁、拿筆的手旁露出 body 草稿（4.73%）。t=0.2 尾巴根部露出草稿。body、leg_r、tail 都列在 needs_manual，所以判 MINOR。 | NOT_TESTED | body 4.7%、head 0.2%、leg_l 1.5%、leg_r 4.7%、tail 2.5% | tail 2.4%、leg_r 3.0%、leg_l 2.8%、arm_l 3.0%、arm_r 5.1% |
| rq | OK：吉他、裙子、後髮、雙腿分層合理，重組與原圖一致，沒有特效或背景混入 | MINOR：pivot 位置大致正確（頭在頸、手臂在肩、後髮在頭頂）；但父子關係是 arm_l/arm_r 掛在 guitar 底下（body→guitar→arms），持物階層倒過來，靠吉他轉動帶手臂，視覺上沒有顛倒但不符合手持物的慣例、難以在 Spine 裡手動調 | MINOR：happy 主要是整體跳起加頭部擺動，手臂與吉他只小幅擺動，雙腿幾乎不動；idle 幾乎靜止 | OK：驗收圖尺度下看不到明顯草稿或破洞；hair_back、body、腿列 needs_manual，量到的露出很小 | NOT_TESTED | body 2.0%、guitar 2.0%、hair_back 1.8%、leg_l 1.5%、leg_r 3.0%、skirt 0.3% | hair_back 3.0%、leg_l 5.8%、leg_r 5.8%、skirt 0.9%、guitar 2.1%、arm_l 0.8%、arm_r 2.5% |
| yz | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED | NOT_TESTED | arm_r 1.8%、body 7.5%、hair_back 3.4%、leg_l 8.1%、leg_r 6.5%、skirt 0.2% | hair_back 3.2%、leg_l 3.8%、leg_r 1.9%、skirt 1.0%、arm_r 4.4%、bouquet 5.1%、arm_l 15.8% |
| N1 | MINOR：人物、手杖分層正確，杖頭光球留在 staff 圖層（合理，沒有混進頭或身體）；但杖頭周圍半透明的星形光芒在重組中整片遺失（visual_check 洋紅區），特效被丟掉了 | MINOR：staff 正確掛在 arm_r 下、pivot 在手；手臂在肩、頭在頸；hip 很低（接近長袍下緣），腿只剩袍下的鞋，pivot 在可見部分起點 | MINOR：happy 以整體跳起加身體傾斜為主，持杖手臂與另一手只有小幅擺動；idle 幾乎靜止 | OK：驗收圖尺度下沒有明顯草稿露出；腿（鞋）列 needs_manual | NOT_TESTED | body 6.1%、head 0.0%、leg_l 4.3%、leg_r 5.2%、staff 0.1% | leg_l 1.5%、leg_r 1.4%、staff 6.2%、arm_l 6.4%、arm_r 2.7% |
| N2 | MINOR：影子層只有低透明深色影子，腳的位置挖出缺口，跳起時地上沒有留下靴子或戰袍碎片；但跳起時腳下仍跟著一條淡灰殘影，戰袍下緣有白色鋸齒，body、雙腿為 needs_manual | OK：arm_r pivot 在右肩、sword 以 arm_r 為父、pivot 在握柄，舉劍時握點不分開（attach 0.956）；雙腿 pivot 在髖，hair_back 繞頭頂轉，可以接受 | OK：Happy 右臂舉劍 60°、左臂 15°、頭 8°，加上跳躍，四肢在關鍵影格有明顯動作；只是雙腿只動 3°、Idle 幅度很小 | MINOR：Happy 舉劍時胸甲右側露出棕色碎片（body 補畫草稿）與肩部暗縫；leg_r 露出 0.15、body 0.083 超過門檻，但都已列為 needs_manual | NOT_TESTED | arm_l 1.9%、body 8.3%、hair_back 3.3%、head 0.2%、leg_l 7.6%、leg_r 15.0%、shadow 16876.1%、sword 0.8% | hair_back 1.6%、leg_l 3.0%、leg_r 3.7%、tabard 2.4%、arm_l 5.2%、sword 60.0%、arm_r 22.5% |
| N3 | OK：手臂（透視縮短的拳頭）、頭、身體、腿分層乾淨，重組與原圖一致，只有頭髮邊緣零星缺像素 | MINOR：手臂 pivot 在肩、頭在頸都正確；腿 pivot 在短褲下緣（可見部分起點），短褲跟著 body 走 | OK：happy 有明顯的舉拳動作、頭與身體擺動、腿部動作，不只整體跳動；idle 為小幅擺動。舉拳到頭頂時拳頭壓在頭上、手臂藏在頭後，略怪 | MINOR：happy t=0.5 手臂轉開後肩膀露出紅色草稿與鋸齒狀藍色袖子碎片（body 露出 5%），而 body 只標 auto_repaired、沒有列入人工補畫 | NOT_TESTED | arm_l 1.7%、body 5.1%、head 0.0%、leg_l 1.7%、leg_r 1.5% | leg_l 4.3%、leg_r 4.5%、arm_l 52.0%、arm_r 3.2% |
| N4 | MINOR：validation 的 setup_pose FAIL（0.0226 > 0.02），c2s run 中止，但仍有驗收圖。分層大致可用，但叉腰手的一小條殘留在身體右側（idle 每格都看得到細直線與小凸塊），投影被烤在各部件上 | OK：手臂 pivot 在肩、頭在頸、腿在胯下兩側，沒有繞錯關節 | MINOR：happy 四肢有動作，但 t=0.5 指向的手臂往上甩、直接橫過臉（手臂圖層在頭上面），叉腰手臂舉起後露出三角形暗線；idle 小幅擺動 | MINOR：叉腰手移開後，腰側露出補色區（body 露出 5.5%）與殘留陰影線；無 needs_manual 項，但沒有列人工補畫 | NOT_TESTED | body 5.5%、leg_l 2.2%、leg_r 2.6% | leg_l 10.2%、leg_r 10.2%、arm_l 62.5%、arm_r 55.1% |

## 前後比較：v1_before → v1_final2

| 案例 | 等級 | 重組 MAE | 未分配 | 未持物手臂動作量 | 需人工 | 品質未解 |
|---|---|---|---|---|---|---|
| A | PARTIAL → PARTIAL | 0.00151 → 0.00151 | 0.0 → 0.0 | arm_l 2.1%、arm_r 4.9% → arm_l 2.1%、arm_r 4.9% | 4 → 4 | 0 → 0 |
| B | PARTIAL → PARTIAL | 0.00097 → 0.00097 | 0.0045 → 0.0045 | arm_r 4.2% → arm_r 5.9% | 0 → 0 | 0 → 0 |
| C | FAIL → PARTIAL | 0.01714 → 0.00681 | 0.0018 → 0.0018 | arm_r 5.6% → arm_r 5.6% | 3 → 2 | 1 → 0 |
| D | FAIL → FAIL | 0.00141 → 0.00141 | 0.0007 → 0.0007 | arm_r 0.9%、arm_l 0.8% → arm_r 1.2%、arm_l 1.2% | 2 → 2 | 0 → 0 |
| E | PARTIAL → PARTIAL | 0.0018 → 0.00183 | 0.0043 → 0.0043 | arm_l 19.0%、arm_r 5.9% → arm_l 19.0%、arm_r 5.9% | 6 → 5 | 0 → 0 |
| ren | PARTIAL → PARTIAL | 0.00141 → 0.00141 | 0.0001 → 0.0001 | — → — | 4 → 4 | 0 → 0 |
| zc2 | PARTIAL → FAIL | 0.0014 → 0.0014 | 0.0072 → 0.0072 | arm_l 12.9% → arm_l 12.9% | 4 → 5 | 0 → 0 |
| H1 | FAIL → PARTIAL | 0.00547 → 0.00547 | 0.0013 → 0.0013 | arm_l 16.7%、arm_r 30.8% → arm_l 16.7%、arm_r 30.8% | 1 → 1 | 1 → 0 |
| H2 | FAIL → PARTIAL | 0.00325 → 0.00325 | 0.0 → 0.0 | arm_r 6.6% → arm_r 6.6% | 2 → 2 | 1 → 0 |
| H3 | PARTIAL → FAIL | 0.00468 → 0.00468 | 0.0003 → 0.0003 | arm_l 2.2% → arm_l 2.2% | 3 → 3 | 0 → 0 |
| H4 | FAIL → FAIL | 0.00131 → 0.00131 | 0.0057 → 0.0057 | arm_l 3.0%、arm_r 5.1% → arm_l 3.0%、arm_r 5.1% | 3 → 3 | 0 → 0 |
| rq | （v1_before 沒有此案例）→ PARTIAL | | | | | |
| yz | （v1_before 沒有此案例）→ FAIL | | | | | |
| N1 | （v1_before 沒有此案例）→ FAIL | | | | | |
| N2 | （v1_before 沒有此案例）→ PARTIAL | | | | | |
| N3 | （v1_before 沒有此案例）→ PARTIAL | | | | | |
| N4 | （v1_before 沒有此案例）→ FAIL | | | | | |
