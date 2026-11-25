# 已知問題

## 未解決

| # | 問題 | 狀態 | 影響 | 解除方式 |
|---|---|---|---|---|
| K-01 | 只有 Spine 試用版，CLI 沒有匯入參數也不能存檔 | BLOCKED | 無法產生 `.spine`、無法往返驗證與 Editor 可編輯性驗證 | 使用者取得完整版授權後，設定 `SPINE_EXE` 指向 `Spine.com` 並重跑 `c2s export` |
| K-02 | 使用者把 `.claude/*`、`.codex/*` 加入 `.gitignore`（同時移除了先前加入的 `openspec`） | 已接受 | Skill 只有 `skills/character-to-spine/` 這份正本進版控；clone 後需要自行複製到 `.claude/skills/`、`.codex/skills/` | 見 README「安裝 Skill」 |
| K-03 | Python Simulation Preview 只支援本專案輸出的功能（rotate／translate／scale、平切線 bezier） | 設計限制 | 在 Spine 裡手動改成其他曲線後，預覽會不準 | 預覽只用於自我檢查，正式預覽以 Spine 為準 |
| K-04 | 自動填補只用 OpenCV Telea 邊緣延伸 | 設計限制 | 大面積遮擋的部件標為 `needs_manual`，需要人工修補 | 人工修好後 `c2s prepare --replace` |
| K-05 | skirt 的次要動作沒有自動化測試 | 自動化 NOT_TESTED；真實角色預覽中目視可見裙擺擺動 | 與 hair 走同一段程式 | 需要時加一個帶裙擺的合成角色 |
| K-06 | `转场2.png` 是 AI 生成圖，有第三隻手（右側下垂） | 素材瑕疵 | 已獨立成 `arm_extra` 部件，跟著身體小幅擺動 | 美術在 Spine 刪除該插槽，或修圖後重跑 |
| K-07 | 真實角色有被大面積遮擋的部件（`人.png`：body、hair_back、leg_l、leg_r；`转场2.png`：body、hair_back、leg_l） | BLOCKED（需人工） | 目前用 OpenCV 填補草稿；在動作幅度內大多不會露出，但品質未經人工確認 | 依各工作目錄的 `repair_tasks.md` 補畫，`c2s prepare --replace` 匯回 |
| K-09 | 沒有透明度的圖片用邊界 flood fill 去背，容許差 14；灰階或與背景顏色接近的部件可能被一起去掉 | 設計限制 | 被去掉的部件會在 rig 階段以「缺少圖層」停下（結束碼 2） | 先提供帶透明度的 PNG，或用遮罩 |
| K-10 | 往返驗證用 `Spine -e json`（官方 CLI 頁的語法列有此寫法，但範例只示範 export settings 檔） | 無法驗證（需完整版） | 授權到位後若往返驗證 FAIL，先檢查是否需要改用 export settings 檔 | 看 `spine/spine_roundtrip.log` |
| K-11 | `test_skill_copies_identical` 在 `.claude`／`.codex` 複本不存在時只檢查正本；`test_no_character_specific_code` 只比對字串，無法抓到寫死的座標 | 測試限制（最終審查指出） | 座標寫死改以人工審查確認：兩次獨立審查都未發現 | — |
| K-12 | 自我修正只能降低動作幅度，不能修改部件範圍 | 設計限制 | 重疊不足造成的細縫（如 synth_b 手臂只重疊 2px）修不掉，判 BLOCKED | 依異常影格擴大相鄰部件的 polygon 讓它們多重疊 |
| K-13 | 補圖可靠度是保守判定：單色部件的輪廓被深度遮住也會判為不可靠，抬手露出後改為 needs_manual（synth_a、synth_b 的 body） | 設計取捨 | 真實角色的被遮輪廓確實是猜的，寧可多交給人 | 人工確認後用 `--replace` 匯回原圖層即可 |
| K-14 | 品質檢查以 10 fps、最長邊 480px 抽樣 | 設計限制 | 小於約 2px 的細縫、兩個抽樣點之間的瞬間問題可能漏掉 | 需要時提高 `quality.FPS` 或 `PREVIEW_MAX_SIDE` |
| K-15 | 部件的前後順序（z）是 parts.json 的語意判斷，程式無法自動驗證 | 設計限制（最終驗收審查指出） | 對調 z 時，重組與 setup_pose 仍會一致（像素依 z 分配）；只有穿插、露出等間接指標可能改變 | 寫 parts.json 後用 `layer_preview.png` 第三欄目視確認順序 |
| K-16 | 「逐位元組相同」只在同一台機器、同一路徑、相同套件版本下成立 | 範圍限制 | JSON 內含絕對路徑；OpenCV 版本不同時，量測值可能跨過門檻、讓 tuning 不同 | 用 `requirements-lock.txt` 安裝 |
| K-17 | 接觸約束只限制骨頭自身的旋轉幅度；為了保持接觸，抱吉他的手臂幅度只剩 0.018～0.07 倍，幾乎不動 | 設計取捨 | 手不會離開吉他，但撥弦動作很小 | 需要更明顯的手部動作時，改用 Spine 內的 IK（Professional），或人工加關鍵影格 |
| K-18 | 撥弦手的最大位移（5.1px）仍未達 13px 的目標 | NOT MET | 限制來源依序是：吉他後方的草稿（反事實實測：補好吉他後 9.5px、每秒 74px），其次是 9px 的接觸容許值（全部補好後 10.2px） | 依修補優先順序補畫吉他；全部補好後再試「容許位移改看道具內部空間」（H1，現在套用會先被草稿露出卡住） |
| K-20 | 露出量以面積比例計算，沿邊緣的細縫與整塊露出算法相同 | 量測限制（子代理觀察） | 細縫為主的部件可能排得比看起來高 | 看三格對照圖的第三格判斷 |
| K-08 | 部件邊界由 Agent 目測多邊形，交界處（頭髮捲曲邊緣、蕾絲）不是像素級精準 | 設計限制 | 動畫時交界可能出現細縫或多帶一點相鄰部件 | 需要精準時改用遮罩（`mask`），或人工修圖後 `--replace` |
| K-21 | Skill session 不確定格式時，會主動在專案裡找別的角色的 `parts.json` 當範例（四次實測都發生，含讀到舊角色 `转场2.parts.json`） | 已在 SKILL.md 禁止；保留集實測驗證是否遵守 | 參考別的角色的拆法、座標與 pivot | 見 `docs/GENERALIZATION_TEST_REPORT.md` 的 Skill 實測一節 |
| K-22 | 刪掉圖片旁的 `parts.json` 後重跑 `c2s analyze`，會默默沿用工作目錄裡上一次的正規化複本 | 未修正（設計上用來支援「只在工作目錄改」） | 以為重新分析，實際用的是舊答案 | 刪除 `output/<圖名>/` 後再分析 |
| K-23 | `attach` 與 `absent` 由分析的 Agent 自己宣告；宣告 attach 的手臂不受 2% 動作量下限檢查，宣告 absent 的部件不建骨頭也就量不到 | 評估限制（獨立審查 S2） | 開發集 D 第二次分析把兩手都 attach 到相機，動作只剩 0.7% 而不被自動量測判失敗 | 保留集預登記 expected_absent／attached_arms；持物手臂的下限留給下一階段 |
| K-29 | 自動檢查抓不到「坐姿角色只剩整體跳動」（手腳仍有 2%～5% 的小動作，不觸發 bounce_only）與「骨架父子顛倒」 | 未解決 | 保留集 H4、H2 的這兩個 BAD 只靠目視發現。H4 的 session 只提醒「跳起來對坐姿可能不自然」，沒有當成失敗；H2 的 session 完全沒提到 | 加入姿勢與階層的自動檢查，或讓 Skill 在回報前看驗收圖 |
| K-25 | 新角色的自我修正多半跑滿 3 輪仍有異常（最終輪 9 張中 7 張；×0.125 是 3 輪的下限 0.5³） | 量測事實 | 報告不能寫成「已自動修正」，只能寫「已降低」 | — |
| K-27 | 測試集角色多樣性有限：開發集 B、C 是同一個角色（Wikipe-tan）的不同畫作，D 與保留集多張屬同系列吉祥物；全部是 2D 動漫線稿，不是使用者實際的 3D 算圖風 Q 版 | 素材限制 | 結論不能外推到 3D 算圖風角色 | 使用者提供自己的角色圖放進 manifest 重跑 |
| K-31 | Skill 實測仍在同一台機器、同一個 Claude 帳號執行；已用 `--setting-sources project,local`、`--strict-mcp-config` 排除使用者層設定與 MCP，PATH 移除本專案，c2s 由 Skill 自己的 `.venv` 安裝 | 測試限制 | 全域 `~/.claude/CLAUDE.md` 等帳號層內容可能仍被載入；沒有在另一台機器驗證 | 在另一台電腦照 README 安裝一次 |
| K-33 | 雙手抱的道具帶著手臂，道具旋轉時肩膀也會被帶離身體 | 設計取捨（D-35／D-44） | ren 目前吉他只轉約 1.25°（×0.125），看不出來；道具幅度放大時會出現 | 需要時改用 Spine 的 IK |
| K-34 | 柔和投影的圖：上層部件邊緣的半透明陰影疊在下層不透明的補圖上，重組與原圖差異超過門檻 | 保留集 N4 FAIL（`setup_pose` 0.0226 > 0.02） | 畫面幾乎一樣，但驗證判 FAIL、結束碼 1 | 去掉投影再處理，或人工修補；不為了保留集放寬門檻 |
| K-35 | 泛化判定的「未分配前景」把與角色相連的特效算成漏切 | 評估限制 | N1 2.5% 判 FAIL，五個最大區塊都是法杖頂端的光芒（已正確排除在部件外）。yz 1.6% 則是真正的漏切（手鍊、花束邊緣），Agent 修正一輪後仍未補齊 | 判定改為排除特效前須先預登記，不在保留集執行後修改 |
| K-36 | Skill session 偶爾違反 Skill 規則：N1 中文提問卻用英文回報；N4 在沙盒外建診斷腳本追查原因 | 已補強 SKILL.md（語言規則移到開頭、禁止診斷程式），補強後的驗收兩次都遵守 | 回報語言不一致、留下沙盒外檔案 | — |
| K-37 | Happy 模板是站姿跳躍：跑步姿勢（rq）、坐姿（H4）只剩整體跳動 | 範圍限制 | 動作不自然；Skill 會在回報中說明 | 新增非站姿模板 |

| K-38 | 影子修正只清乾淨影子圖層本身；Agent 畫的腿、裙子多邊形若含有影子，那些灰色像素會跟著角色離地 | 未解決（三輪修正已用完） | C 裙下一條灰帶、E 與 N2 腳下淡灰殘邊跟著跳起（獨立目視 MINOR） | 影子多邊形與腿、裙子分界畫準；或人工修圖後 `--replace` |

## 已修正

2026-11-23 草稿第一次執行與獨立審查發現的問題，全部已修正並有回歸測試：

| 問題 | 回歸測試 |
|---|---|
| `setup_pose` 比對把白底一起平均，附件旋轉全部反向仍會 PASS | `test_validate_catches_flipped_rotations` |
| 骨架原點與外框受散落特效影響 | `test_stray_pixels_do_not_move_origin` |
| `role`／`motion` 沒有接上，手臂一律舉高 110°，沒有頭髮、裙擺、道具動作 | `test_motion_factor`、`test_secondary_motion_for_hair` |
| `--part` 沿用過期的 metadata，結果和完整重跑不同 | `test_partial_rerun_equals_full` |
| 尺寸錯誤的替換圖先被存進 `overrides/`，之後每次 prepare 都失敗 | `test_replace_wrong_size` |
| 圖片旁的 `parts.json` 會蓋掉使用者在工作目錄修改的版本 | `test_workdir_parts_json_wins_over_sidecar` |
| 工作目錄存相對路徑；`--workdir` 不更新「上一次使用的目錄」 | `test_run_with_workdir` |
| 明確指定 SpineTrial 時被當成完整版執行；執行檔不存在時崩潰 | `test_trial_blocked_even_when_given_explicitly`、`test_missing_exe_is_fail_not_crash` |
| `--motion idle` 一定驗證失敗；動畫檔殘留舊內容 | `test_idle_only_is_valid` |
| 可用 `root`／`hip` 當部件名稱、可有重複 z、多邊形格式不檢查 | `test_parts_format_errors` |
| 預覽沒有「Python Simulation Preview」標示；大圖角色的預覽記憶體用量可達 GB 級 | `test_preview_labelled_and_moving` |
| 擠壓伸展方向相反：Spine 的 scaleX 沿骨頭方向，直立的骨頭要對調 x／y（檢視主要角色預覽時發現） | `test_crouch_is_wider_on_screen` |
| **最終驗收審查**：`setup_pose` 拿匯出圖片跟自己比，換錯圖、翻轉都 PASS | `test_validate_catches_wrong_image_content`（已確認舊版會失敗） |
| **最終驗收審查**：parts.json 語法錯誤、型別錯誤時結束碼 1（應為 2） | `test_malformed_parts_json_is_needs_parts` |
| **最終驗收審查**：NaN／Infinity 座標被接受並寫進 Spine JSON | `test_malformed_parts_json_is_needs_parts`；`save_json` 拒絕 NaN |
| **最終驗收審查**：預覽標示、曲線數值、FAIL 結束碼、整體狀態的測試在功能壞掉時仍會通過 | 加強 `test_preview_labelled_and_moving`、`test_trial_environment_not_pass`；新增 `test_curve_values_are_absolute_bezier`、`test_validation_fail_exits_1_with_log` |
| **最終驗收審查**：驗證 FAIL 時沒有寫 `c2s_error.log`；成功後殘留過期的 log | `test_validation_fail_exits_1_with_log` |
| **最終驗收審查**：刪除部件後舊圖層殘留；rig 拒絕時留下舊 `rig.json` | `test_removed_part_leaves_no_stale_layer`、`test_missing_required_layer_refuses` |
| **quality-hardening 驗收審查**：穿插只是宣稱、沒有檢查 | `test_detects_interpenetration`（新增 intrude 檢查） |
| **quality-hardening 驗收審查**：不可靠補圖露出量在門檻內時，驗證完全不提 | `test_unreliable_exposure_within_threshold_is_reported` |
| **quality-hardening 驗收審查**：改了圖片旁的 parts.json 後直接 prepare，修改被默默忽略 | `test_sidecar_edit_requires_reanalyze` |
| **quality-hardening 驗收審查**：接觸基準量到 0 時檢查失效；各類違規單位不同卻直接加總；10 fps 抽樣漏掉 0.95、2.15 秒的關鍵影格；覆蓋人工修補圖沒有備份 | `test_override_backup`；其餘以程式修正，見 design.md §8 |
| **最終驗收審查**：1×1 圖片讓 OpenCV 崩潰（unexpected_error）；非圖片的 `--replace` 回報為 unexpected_error | `test_tiny_and_unreadable_inputs_are_clean_errors`、`test_replace_with_non_image` |
| **v1.0**：K-24 破洞誤判（初始就是背景的被圍區域、微動讓圍住與否翻轉）與縫隙量錯關節（手指碰角）。D-42、D-43 | `test_real_holes_only_count_what_a_departed_part_used_to_cover`、`test_gap_joint_follows_skeleton_not_largest_contact` |
| **v1.0**：K-28 單手拿的道具讓手臂掛在道具下、骨架上下顛倒；持物的手被多餘的接觸約束縮小（K-19）。D-44 | `test_single_hand_holds_prop_as_child`、`test_prop_carries_hugging_arms`、`test_carried_arm_strums` |
| **v1.0**：自我修正只會減半，三輪就縮到 ×0.125（過度縮小動作）。D-45 | `test_refine_does_not_over_reduce` |
| **v1.0**：K-30 Skill 引用專案內的 `scripts/visual_report.py`。D-47 | `tests/test_visual_report.py`（報告由 `c2s run` 產生） |
| **v1.0**：K-26 Skill 實測依賴本專案 `.venv`。改為打包安裝，c2s 由 Skill 自己的 `.venv` 提供。D-48 | 乾淨沙盒實測，見 `docs/SKILL_V1_REPORT.md` |
| **v1.0**：影子圖層混入腳尖、靴子、裙襬，角色跳起時留在地上（E、C、N2）。三輪修正：RGB 中位數 → 連通區塊 → 納入透明度並把被腳擋住的影子平塗。D-49 | `test_ground_shadow_keeps_only_shadow_pixels`、`test_ground_shadow_behind_feet_stays_shadow` |
