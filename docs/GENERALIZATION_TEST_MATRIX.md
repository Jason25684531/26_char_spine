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
| 目前 | 0/5｜3/5｜PARTIAL 3、FAIL 2 | 0/4｜1/4｜PARTIAL 1、FAIL 3 |

## 案例（目前）

| 案例 | 集 | 類型 | 預期 | 等級 | Skill 觸發 | 來源查核 | 重組 MAE | 未分配 | 未持物手臂 | 持物手臂 | 只剩跳動 | 循環 | 需人工 | absent | 主要理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | dev | front-chibi | supported | **PARTIAL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00151 | 0.00% | arm_l 2.1%、arm_r 4.9% | — | 否 | 是 | leg_l, leg_r, body, skirt | — | 需人工修補：leg_l, leg_r, body, skirt；arm_l 被自我修正縮到 ×0.125（素材限制：['exposure']）；目視 joints：骨架圖 leg_l/leg_r 的 pivot 在裙襬下緣（可見部分起點），大腿上段被裙子遮住；arm 在肩、braid 在耳側、head 在頸，位置正確；目視 occlusion：happy t=0.5 右手旁裙側出現淡色補圖、兩腿間有補圖縫（repair_skirt/leg_l 紅區），skirt、leg_l  |
| B | dev | three-quarter | supported | **PARTIAL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00097 | 0.45% | arm_r 4.2% | arm_l 1.6% | 否 | 是 | — | leg_l, leg_r | 宣告看不到：leg_l, leg_r；目視 layers：初始姿勢重組與原圖一致；但 happy t=0.2/0.5 左前臂抬起後，手與裙緣之間露出一道黑色楔形線（疑似裙子圖層殘留手臂輪廓或裙內陰影），不在補畫清單 |
| C | dev | prop | supported | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.01714 | 0.18% | arm_r 5.6% | arm_l 1.2% | 否 | 是 | shadow, hair_back, body | leg_l, leg_r | 品質未解：hole:character |
| D | dev | occlusion | partial | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00141 | 0.07% | arm_r 0.9%、arm_l 0.8% | — | 否 | 是 | hair_back, body | — | 未持物手臂 arm_r 動作量 0.9% < 2%；未持物手臂 arm_l 動作量 0.8% < 2% |
| E | dev | non-humanoid | partial | **PARTIAL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.0018 | 0.43% | arm_l 19.0%、arm_r 5.9% | — | 否 | 是 | shadow, cape, horn, leg_l, leg_r, arm_l | — | 需人工修補：shadow, cape, horn, leg_l, leg_r, arm_l；arm_r 被自我修正縮到 ×0.125（素材限制：['exposure']）；目視 layers：影子像素被切進 leg_l：happy t=0.4–0.6 左腳底下黏著一塊灰影子一起離地；初始姿勢右腿多一道原圖沒有的白色短線；其餘分層正確；目視 occlusion：happy t=0.4–0.6 地上留下一塊像腳尖的綠色影子草稿，看起來像斷掉的腳；cape 草稿在 t=0.6 露出 |
| ren | legacy | regression | supported | **PARTIAL** | — | — | 0.00141 | 0.01% | — | arm_l 0.8%、arm_r 1.9% | 否 | 是 | hair_back, leg_l, leg_r, body | — | 需人工修補：hair_back, leg_l, leg_r, body；目視 layers：hair_back 圖層保留了吉他琴頸與琴頭像素：happy t=0.4/0.5 吉他轉動後出現兩個琴頭（重影），手與琴頸間還有一道白縫；hair_back 已列 needs_manual，露出位置與 repair_hair_back (c) 紅區一致；目視 joints：leg_l/leg_r pivot 在裙襬下緣（只露出靴子）；arm 在肩、guitar 在琴身中心、head 在 |
| zc2 | legacy | regression | supported | **PARTIAL** | — | — | 0.0014 | 0.72% | arm_l 12.9% | arm_r 0.4% | 否 | 是 | hair_back, leg_l, leg_r, body | — | 需人工修補：hair_back, leg_l, leg_r, body；目視 layers：圖層重組沒有原圖的發光球與滿地飛散花瓣（missing_parts 列為未分配 12%），角色本體（包括原圖就有的第三隻下垂手 arm_extra）切得正確、順序正確；目視 joints：leg_l/leg_r pivot 在裙襬下緣（只露出鞋）；arm_l 在肩、arm_extra 在肩後、head 在頸，正確；目視 occlusion：happy t=0.4 兩鞋之間露出 leg_ |
| H1 | holdout | front-chibi | supported | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00547 | 0.13% | arm_l 16.7%、arm_r 30.8% | — | 否 | 是 | body | — | 品質未解：hole:character |
| H2 | holdout | prop-adult | supported | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00325 | 0.00% | arm_r 6.6% | arm_l 0.9% | 否 | 是 | leg_l, body | — | 品質未解：hole:character；arm_r 被自我修正縮到 ×0.125（演算法限制：['exposure', 'hole']）；目視 joints：骨架格中 arm_l 的 pivot 在捲袖口，也就是手肘處，上臂留在 body，等於手臂繞手肘轉。而且 rig 的父子關係是反的：arm_l 的 parent 是 clipboard，clipboard 的 pivot 在手上、parent 是 body，所以手臂掛在夾板底下（灰線從 hip 拉到夾板，再接到 arm_ |
| H3 | holdout | prop-occlusion | supported | **PARTIAL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00468 | 0.03% | arm_l 2.2% | arm_r 0.4% | 否 | 是 | hair_back, body, book | — | 需人工修補：hair_back, body, book；目視 layers：圖層重組和原圖幾乎一致，前後順序正確（hair_back 最底，裙子在腿和身體前，書在身體前，手臂最上層）。不過 arm_l 圖層夾帶了一大片藍色頭髮，arm_r 圖層右緣也帶了一縷頭髮，頭髮會跟著手臂動。body 和 hair_back 圖層的大面積補圖都是糊色塊。；目視 joints：骨架格中 head 在頸，arm_l 和 arm_r 在肩附近，hair_back 掛在 head 下，skirt |
| H4 | holdout | sitting-anthro | partial | **FAIL** | 是（c2s 由專案的 .venv 提供） | PASS | 0.00131 | 0.57% | arm_l 3.0%、arm_r 5.1% | — | 否 | 是 | tail, body, leg_r | — | arm_r 被自我修正縮到 ×0.125（演算法限制：['exposure', 'gap']）；目視 motion：happy 4 格中整個坐姿角色原樣跳離地面（t=0.5 連腳一起騰空）。雙腿幾乎不動（約 ±2°），右臂只有約 7°，拿筆的手約 8°。比對 t=0、0.2、0.5、0.9，四肢位置幾乎沒有變化，只剩頭部傾斜和尾巴小擺。符合「動作只剩整體跳動，四肢在關鍵影格中看不出動作」。 |

## 驗證器原始狀態（PASS／FAIL／BLOCKED／NOT_TESTED）

- A：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- B：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs PASS、absent_parts BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- C：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、absent_parts BLOCKED、animation_quality BLOCKED、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- D：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- E：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- ren：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- zc2：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- H1：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality BLOCKED、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- H2：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality BLOCKED、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- H3：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED
- H4：bones PASS、slots PASS、image_references PASS、animations PASS、setup_pose PASS、manual_repairs BLOCKED、animation_quality PASS、spine_import BLOCKED、spine_roundtrip NOT_TESTED、spine_editable NOT_TESTED

## 自動量測與目視判斷（分開記錄）

| 案例 | Agent 目視：分層 | 關節 | 動作 | 遮擋補圖 | 使用者目視 | 補圖最大露出（自動） | 各肢體 happy 動作量（自動） |
|---|---|---|---|---|---|---|---|
| A | OK：圖層重組與原圖幾乎一致；帽子、雙辮、手臂、裙子、雙腿分開，前後順序正確，沒看到漏切或重複 | MINOR：骨架圖 leg_l/leg_r 的 pivot 在裙襬下緣（可見部分起點），大腿上段被裙子遮住；arm 在肩、braid 在耳側、head 在頸，位置正確 | OK：happy t=0.5 雙臂比 t=0 外展約 20–30°、雙辮擺動、頭側傾、雙腳略收，不是只有整體跳動；t=0.2 有下蹲預備 | MINOR：happy t=0.5 右手旁裙側出現淡色補圖、兩腿間有補圖縫（repair_skirt/leg_l 紅區），skirt、leg_l 都已列 needs_manual | NOT_TESTED | body 2.7%、braid_l 1.9%、braid_r 1.3%、leg_l 9.1%、leg_r 2.6%、skirt 9.3% | braid_l 1.9%、braid_r 1.9%、leg_l 2.0%、leg_r 2.3%、skirt 0.2%、arm_l 2.1%、arm_r 4.9% |
| B | MINOR：初始姿勢重組與原圖一致；但 happy t=0.2/0.5 左前臂抬起後，手與裙緣之間露出一道黑色楔形線（疑似裙子圖層殘留手臂輪廓或裙內陰影），不在補畫清單 | OK：arm_l/arm_r pivot 在肩、雙馬尾 pivot 在髮束根部、head 在頸；長裙蓋住腿，沒有捏造腿 | OK：happy t=0.5 右拳明顯上舉、提裙的左臂上抬、雙馬尾擺動、身體微傾；四肢在關鍵影格看得出動作 | OK：自動補圖（arm_r 肩部、body、頭髮）在 happy t=0.5 放大後只有極小色塊，肉眼幾乎看不出；上面那道黑線已計入 layers | NOT_TESTED | arm_l 1.4%、arm_r 1.9%、body 1.7%、hair_l 1.1%、hair_r 0.8%、skirt 0.9% | skirt 1.7%、arm_l 1.6%、arm_r 4.2%、hair_l 1.4%、hair_r 2.3% |
| C | MINOR：初始姿勢重組時裙襬下緣多了一圈深色帶（原圖是淺灰影子），是影子圖層草稿在靜止姿勢就露出；帽子、法杖、手臂分層正確 | OK：arm_l/arm_r 在肩、staff 在握杖手、hat 在頭頂、shadow 在地面；長袍蓋腳，沒有捏造腿 | OK：happy t=0.5 插腰的右手明顯外擺離開腰、法杖上移、帽子跟著頭；不是只有跳動（右臂幅度被 tuning 減半但仍看得出） | MINOR：happy t=0.4–0.6 地上留下一塊深藍色影子草稿（不像影子），袍子下緣同時帶一條淡灰影子離地；shadow 已列 needs_manual，但非常顯眼，建議優先補 | NOT_TESTED | body 2.1%、hair_back 3.9%、head 0.8%、shadow 59.0%、skirt 1.0%、staff 3.9% | hair_back 1.5%、staff 1.3%、skirt 2.1%、arm_r 5.6%、arm_l 1.2% |
| D | OK：圖層重組與原圖一致；相機、雙臂、圍裙、裙、腿、後髮分開，前後順序正確 | MINOR：leg_l/leg_r pivot 在裙襬下緣；arm_l pivot 落在白袖口與胸前交界附近，雙手舉相機的姿勢下看不出是否在肩，無法確認 | MINOR：持相機的雙臂在 happy t=0.5 與 t=0 幾乎相同，只隨身體上移；雙腿在 t=0.5 略張開、頭髮跟隨，屬持物手臂小幅動作 | MINOR：hair_back（idle t=0.6）、body（happy t=0.5）草稿露出只有細紅線，動畫中不明顯；兩者都已列 needs_manual | NOT_TESTED | arm_l 0.7%、arm_r 0.2%、body 1.3%、hair_back 2.5%、head 1.4%、leg_l 16.2%、leg_r 15.7% | hair_back 1.1%、leg_l 8.4%、leg_r 8.6%、skirt 1.1%、arm_r 0.9%、arm_l 0.8%、camera 0.6% |
| E | MINOR：影子像素被切進 leg_l：happy t=0.4–0.6 左腳底下黏著一塊灰影子一起離地；初始姿勢右腿多一道原圖沒有的白色短線；其餘分層正確 | OK：leg_l/leg_r 在胯下腿根、arm_r 在舉起手臂的肩、arm_l 在小手肩部、tail 在尾根、horn 在頭頂、head 在頸，都對 | OK：happy t=0.5 指天的手臂舉得更高、雙腿張開、尾巴與披風跟著動；不是只有整體跳動 | MINOR：happy t=0.4–0.6 地上留下一塊像腳尖的綠色影子草稿，看起來像斷掉的腳；cape 草稿在 t=0.6 露出紅邊。shadow、cape 都已列 needs_manual，但腳尖草稿非常顯眼 | NOT_TESTED | arm_l 2.1%、body 1.5%、cape 7.1%、head 1.9%、horn 2.9%、leg_l 1.5%、leg_r 0.5%、scarf 0.1%、shadow 35.0%、tail 2.2% | cape 2.5%、tail 2.4%、horn 1.9%、leg_l 2.0%、leg_r 1.3%、arm_l 19.0%、arm_r 5.9% |
| ren | MINOR：hair_back 圖層保留了吉他琴頸與琴頭像素：happy t=0.4/0.5 吉他轉動後出現兩個琴頭（重影），手與琴頸間還有一道白縫；hair_back 已列 needs_manual，露出位置與 repair_hair_back (c) 紅區一致 | MINOR：leg_l/leg_r pivot 在裙襬下緣（只露出靴子）；arm 在肩、guitar 在琴身中心、head 在頸，正確 | MINOR：雙臂綁在吉他上，happy t=0.5 隨吉他轉約 15° 立起，幅度小；頭、花冠、頭髮跟著動，雙腳微動，屬持物手臂小幅動作 | MINOR：琴頭重影與 hair_back 草稿在 happy t=0.4–0.5 看得到；leg、body 草稿在裙下緣只有小片；全都已列 needs_manual | NOT_TESTED | body 2.0%、guitar 1.3%、hair_back 3.2%、head 1.0%、leg_l 3.4%、leg_r 3.2%、skirt 0.7% | hair_back 3.0%、leg_l 4.8%、leg_r 4.6%、skirt 3.9%、guitar 1.0%、arm_l 0.8%、arm_r 1.9% |
| zc2 | MINOR：圖層重組沒有原圖的發光球與滿地飛散花瓣（missing_parts 列為未分配 12%），角色本體（包括原圖就有的第三隻下垂手 arm_extra）切得正確、順序正確 | MINOR：leg_l/leg_r pivot 在裙襬下緣（只露出鞋）；arm_l 在肩、arm_extra 在肩後、head 在頸，正確 | OK：happy t=0.5 上舉的手臂更直立、下垂的 arm_extra 外擺、捧的花瓣上移、頭髮擺動；四肢動作看得出 | MINOR：happy t=0.4 兩鞋之間露出 leg_l 草稿、t=0.5 arm_extra 肩部露出一條淡色縫（body/hair_back 草稿）；都已列 needs_manual，不算顯眼 | NOT_TESTED | arm_extra 7.2%、arm_l 4.1%、body 1.6%、hair_back 1.8%、head 1.2%、leg_l 10.2%、leg_r 2.0%、petals 1.0%、skirt 0.4% | hair_back 3.2%、leg_l 5.2%、leg_r 5.6%、skirt 4.4%、arm_l 12.9%、petals 0.6%、arm_r 0.4% |
| H1 | OK：圖層重組格和原圖幾乎一致。前後順序正確：腿在裙下，手臂在身體前，頭和領口荷葉邊在最上層。分層合理：手臂含袖子和手套、body 含圍裙和裙子、腿只有裙襬以下的襪子和鞋。沒看到漏切或重複。body 圖層裡的灰黑條紋屬於補圖，歸在 occlusion 判。 | MINOR：骨架格中 arm_l 和 arm_r 的 pivot 在肩頭，head 在頸部，body/hip 在腰帶，父子關係都是 hip→body→head/arms 和 hip→legs，正確。leg_l 和 leg_r 的 pivot 在裙襬下緣（膝上），大腿被裙子遮住，屬於判準中的 MINOR。 | OK：happy t=0.5 雙臂明顯向外張開（左右幅度不對稱，但看起來自然），t=0.2 和 t=0.9 有身體傾斜和頭部擺動，GIF 中腳也有小幅開合，不只是整體跳動。idle 的手臂和頭部有輕微擺動。裙子和身體同一層，沒有額外的擺動。 | MINOR：body 的自動補圖是灰黑色的模糊條紋，在 happy t=0.4–0.7 和 t=1.6–2.0 明顯露出在腰和手臂兩側，idle t=0.67/1.33 的手臂邊緣也看得到。quality round_3 的 happy t=2.1 在左手套附近有破洞（hole:character）。body 已列入 needs_manual（高，露出 17.78%），所以判 MINOR；不過草稿非常醒目，必須人工補。 | NOT_TESTED | body 17.8%、leg_l 1.7%、leg_r 1.7% | leg_l 4.7%、leg_r 4.5%、arm_l 16.7%、arm_r 30.8% |
| H2 | MINOR：圖層重組接近原圖。不過 arm_l（拿夾板的手）只切出前臂和捲袖口，上臂袖子留在 body 圖層裡。body 圖層的頸部和右側有暗色抹糊的填色，clipboard 圖層的照片處有一團模糊塗抹，這兩處在初始姿勢時被遮住。前後順序正確。 | BAD：骨架格中 arm_l 的 pivot 在捲袖口，也就是手肘處，上臂留在 body，等於手臂繞手肘轉。而且 rig 的父子關係是反的：arm_l 的 parent 是 clipboard，clipboard 的 pivot 在手上、parent 是 body，所以手臂掛在夾板底下（灰線從 hip 拉到夾板，再接到 arm_l）。其餘部位正常：arm_r 在肩、雙腿在胯、head 在頸。 | MINOR：happy t=0.2 有整體傾斜，t=0.5 叉腰的 arm_r 明顯向外擺出（約 14°），夾板有小幅翻轉。拿夾板的 arm_l 幾乎不動（約 ±1°），交叉的雙腿在關鍵影格中也幾乎不動。有可見的手臂動作，不算只剩跳動；持物手臂只有小幅動作，判 MINOR。 | MINOR：repair_leg_l (c)：happy t=0.5 雙腿之間露出 leg_l 的補圖長條，佔 27.74%。round_3 的 happy t=0.4 在軀幹右側和叉腰手臂之間有破洞，GIF 中是一條白縫。repair_body (c)：t=1.8 兩側露出草稿。leg_l 和 body 都列在 needs_manual（高），所以判 MINOR。 | NOT_TESTED | body 11.9%、clipboard 1.3%、leg_l 27.7%、leg_r 1.7% | leg_l 6.8%、leg_r 9.8%、arm_r 6.6%、clipboard 2.2%、arm_l 0.9% |
| H3 | MINOR：圖層重組和原圖幾乎一致，前後順序正確（hair_back 最底，裙子在腿和身體前，書在身體前，手臂最上層）。不過 arm_l 圖層夾帶了一大片藍色頭髮，arm_r 圖層右緣也帶了一縷頭髮，頭髮會跟著手臂動。body 和 hair_back 圖層的大面積補圖都是糊色塊。 | MINOR：骨架格中 head 在頸，arm_l 和 arm_r 在肩附近，hair_back 掛在 head 下，skirt 掛在 body 下。leg_l 和 leg_r 的 pivot 在裙襬下緣（大腿中段），大腿上半被裙子遮住，屬於 MINOR。另外 rig 的父子關係是反的：arm_r 的 parent 是 book（應該是書掛在手下）。目前書只轉約 ±2°，預覽中看不出肩膀脫離，所以沒判 BAD，但這是結構錯誤。 | MINOR：happy t=0.5 雙腿從裙下明顯向外張開，裙子有縮放，頭髮跟著頭動（約 ±3°）。推眼鏡的 arm_l 只有約 8°，抱書的 arm_r 只有約 1°，關鍵影格中手臂幾乎看不出變化，屬於持物手臂只有小幅動作。 | MINOR：repair_hair_back (c)：t=1.8 身體兩側露出少量頭髮草稿的細邊。repair_body (c)：t=0.6 書和手臂周圍露出細碎的草稿紅點。這兩處加上 book 都列在 needs_manual。正常大小的影格中不太醒目，round_3 沒有破洞，判 MINOR。 | NOT_TESTED | body 2.4%、book 1.8%、hair_back 4.1%、head 1.1%、leg_l 1.6%、leg_r 1.2% | hair_back 1.9%、leg_l 9.7%、leg_r 9.8%、skirt 0.4%、book 0.4%、arm_r 0.4%、arm_l 2.2% |
| H4 | MINOR：坐姿角色，圖層重組格和原圖幾乎一致，前後順序正確（tail 最底，手臂在腿前）。不過 arm_l 只切出拿筆的手，而且手的下緣夾帶了一點牛仔褲碎片。body 圖層有大面積灰白抹糊的補圖。兩條腿靠兩隻鞋分開，這有畫面依據，不算捏造。 | MINOR：骨架格中 hip 和雙腿 pivot 在臀部附近。坐姿的臀部本來就貼地，所以合理。head 在頸。arm_r 的 pivot 在短袖下緣（上臂中段），上臂在 body 裡，屬於「可見部分起點」的情況。arm_l 只有一隻手，pivot 在手背上方靠近軀幹處，看不到手腕和肩膀，無法確認是否對到關節。tail 的 pivot 在可見的尾巴根部，被手遮住的位置。沒看到明顯錯位，但 arm_l 的判斷沒把握。 | BAD：happy 4 格中整個坐姿角色原樣跳離地面（t=0.5 連腳一起騰空）。雙腿幾乎不動（約 ±2°），右臂只有約 7°，拿筆的手約 8°。比對 t=0、0.2、0.5、0.9，四肢位置幾乎沒有變化，只剩頭部傾斜和尾巴小擺。符合「動作只剩整體跳動，四肢在關鍵影格中看不出動作」。 | MINOR：happy t=0.5 鞋底下有一條灰色長條跟著角色騰空，這是 leg_r 鞋下補圖的露出，乍看像離地的影子。round_3 的 t=1.7 在軀幹和衣服接縫、右臂旁、拿筆的手旁露出 body 草稿（4.73%）。t=0.2 尾巴根部露出草稿。body、leg_r、tail 都列在 needs_manual，所以判 MINOR。 | NOT_TESTED | body 4.7%、head 0.2%、leg_l 1.5%、leg_r 4.7%、tail 2.5% | tail 2.4%、leg_r 3.0%、leg_l 2.8%、arm_l 3.0%、arm_r 5.1% |

## 前後比較：baseline → final

| 案例 | 等級 | 重組 MAE | 未分配 | 未持物手臂動作量 | 需人工 | 品質未解 |
|---|---|---|---|---|---|---|
| A | PARTIAL → PARTIAL | 0.00116 → 0.00151 | 0.0002 → 0.0 | arm_l 4.4%、arm_r 5.0% → arm_l 2.1%、arm_r 4.9% | 4 → 4 | 0 → 0 |
| B | FAIL → PARTIAL | 0.00079 → 0.00097 | 0.0009 → 0.0045 | arm_r 12.6% → arm_r 4.2% | 0 → 0 | 0 → 0 |
| C | FAIL → FAIL | 0.01045 → 0.01714 | 0.0003 → 0.0018 | — → arm_r 5.6% | 4 → 3 | 1 → 1 |
| D | FAIL → FAIL | 0.0015 → 0.00141 | 0.0005 → 0.0007 | arm_l 1.9%、arm_r 1.2% → arm_r 0.9%、arm_l 0.8% | 2 → 2 | 0 → 0 |
| E | FAIL → PARTIAL | 0.00175 → 0.0018 | 0.0033 → 0.0043 | arm_l 4.1%、arm_r 6.6% → arm_l 19.0%、arm_r 5.9% | 5 → 6 | 0 → 0 |
| ren | PARTIAL → PARTIAL | 0.00141 → 0.00141 | 0.0001 → 0.0001 | — → — | 4 → 4 | 0 → 0 |
| zc2 | PARTIAL → PARTIAL | 0.0014 → 0.0014 | 0.0072 → 0.0072 | arm_l 12.9% → arm_l 12.9% | 4 → 4 | 0 → 0 |
| H1 | （baseline 沒有此案例）→ FAIL | | | | | |
| H2 | （baseline 沒有此案例）→ FAIL | | | | | |
| H3 | （baseline 沒有此案例）→ PARTIAL | | | | | |
| H4 | （baseline 沒有此案例）→ FAIL | | | | | |
