# 測試結果

狀態只用 PASS／FAIL／BLOCKED／NOT_TESTED。每一筆都對應實際執行的指令與輸出。

## 執行紀錄

| 日期 | 指令 | 結果 |
|---|---|---|
| 2026-11-23 | `.venv\Scripts\python.exe -m pytest -q`（第一次，草稿原樣） | 47 passed、13 failed（失敗原因見 KNOWN_ISSUES「已修正」） |
| 2026-11-23 | 同上（修正後） | **68 passed** |
| 2026-11-23 | `c2s run examples\synthetic\synth_a.png --workdir output\synth_a` | 結束碼 0；驗證：bones／slots／image_references／animations／setup_pose／manual_repairs PASS，spine_import BLOCKED，spine_roundtrip、spine_editable NOT_TESTED |
| 2026-11-23 | `c2s run examples\synthetic\synth_b.png --workdir output\synth_b` | 結束碼 0；同上，但 manual_repairs BLOCKED（hair_back 被遮擋 >35%，符合預期） |
| 2026-11-23 | 目視檢查 `output\synth_b\layer_preview.png`、`happy` 預覽抽格 | 圖層位置、前後順序、pivot、跳躍與舉手方向正確；預覽帶有「Python Simulation Preview」標示 |

| 2026-11-23 | 修正擠壓伸展軸向後 `pytest -q` | **69 passed**（新增 `test_crouch_is_wider_on_screen`；拿掉修正時此測試失敗，已確認） |
| 2026-11-23 | `c2s run examples\real\人.png --parts examples\real\人.parts.json --workdir output\ren` | 結束碼 0；見下方「真實角色」 |
| 2026-11-23 | `c2s run examples\real\转场2.png --parts examples\real\转场2.parts.json --workdir output\zc2` | 結束碼 0；見下方「真實角色」 |

| 2026-11-23 | 最終驗收審查（獨立子代理）後修正 → `pytest -q` | **83 passed**（新增 14 個回歸測試；`test_validate_catches_wrong_image_content` 對舊版驗證器確認會失敗） |
| 2026-11-23 | 重跑兩組真實角色 | 結束碼 0；setup_pose 改與原圖比對後為 0.0019／0.0018 PASS；其餘狀態不變 |
| 2026-11-24 | 泛化階段開始前 `pytest -q` | **114 passed**（246 秒，`output/generalization/pytest_baseline.txt`） |
| 2026-11-24 | `test_scope.py` 實作前 | 5 failed（預期：結束碼不是 3、absent 不被接受）；實作後 5 passed |
| 2026-11-24 | `unsupported`／`absent` 後 `pytest -q` | **142 passed**；ren、zc2 的 Spine JSON 與驗證狀態與改前相同 |
| 2026-11-24 | `role: ground` 後 `pytest -q` | **147 passed**（274 秒）；ren、zc2 輸出仍相同 |
| 2026-11-24 | 泛化測試（`scripts/generalization.py`） | 開發集第一次盲測：成功 0/5、可處理 1/5；保留集：成功 0/4、可處理 1/4。詳見 `docs/GENERALIZATION_TEST_REPORT.md` |

環境：Windows 11、Python 3.11.9（`.venv`）、numpy 2.4.6、Pillow 13.0.0、opencv-python 5.1.0、pytest 9.2.0。Spine 只有試用版（Launcher 4.3.08）。

## Spec scenario 對照

測試皆在 `tests/`。合成角色由 `tests/synthetic.py` 產生，每個部件的真實範圍已知。

### character-analyzer

| Scenario | 證據 | 狀態 |
|---|---|---|
| 帶透明度的 PNG | `test_analyzer.py::test_transparent_png_keeps_original` | PASS |
| 不透明的純色背景圖片 | `test_opaque_background_flood_fill` | PASS |
| 圖片不存在或沒有前景 | `test_missing_or_empty_image` | PASS |
| 合法的 parts.json | `test_valid_parts_normalized` | PASS |
| 格式錯誤 | `test_parts_format_errors`（9 種）、`test_mask_size_mismatch`、`test_malformed_parts_json_is_needs_parts`（7 種） | PASS |
| 沒有 parts.json | `test_no_parts_json_template_and_exit_2` | PASS |
| 缺少部分必要部件 | `test_partial_required` | PASS |

### image-processor

| Scenario | 證據 | 狀態 |
|---|---|---|
| 位置資訊正確 | `test_layer_positions_match_truth[synth_a/b]` | PASS |
| 圖層重組等於原圖 | `test_recompose_matches_source[synth_a/b]` | PASS |
| 散落的特效不影響角色 | `test_stray_pixels_do_not_move_origin` | PASS |
| 小面積遮擋 | `test_small_occlusion_auto_repaired` | PASS |
| 大面積遮擋 | `test_large_occlusion_needs_manual` | PASS |
| 完全被遮住 | `test_fully_hidden_part` | PASS |
| 修補任務內容 | `test_large_occlusion_needs_manual` | PASS |
| 檢查圖 | `test_layer_preview` ＋ 目視 | PASS |
| 外部遮罩 | `test_layer_positions_match_truth[synth_a]`（synth_a 全部用遮罩） | PASS |
| 只重做一個部件 | `test_only_one_part`、`test_partial_rerun_equals_full` | PASS |
| 替換部件 | `test_replace_canvas_size_and_persist`、`test_replace_layer_size` | PASS |
| 替換圖尺寸無法定位 | `test_replace_wrong_size` | PASS |

### auto-rigging

| Scenario | 證據 | 狀態 |
|---|---|---|
| 兩個比例不同的角色 | `test_rig_animation.py::test_required_bones_follow_pivots` | PASS |
| 骨架初始姿勢還原圖層位置 | `test_validate_ok`（setup_pose）、`test_validate_catches_offset_attachment`、`test_validate_catches_flipped_rotations` | PASS |
| 自訂 pivot | `test_custom_pivot` | PASS |
| 帶頭髮與道具的角色 | `test_extra_parts_get_bones` | PASS |
| parent 不存在 | `test_unknown_parent` | PASS |
| 圖層順序 | `test_slot_order_by_z` | PASS |
| 缺少必要圖層 | `test_missing_required_layer_refuses`、`test_cli.py::test_wrong_order_exit_2` | PASS |

### animation-builder

| Scenario | 證據 | 狀態 |
|---|---|---|
| Happy 動畫內容 | `test_happy_contents` | PASS |
| 首尾相接 | `test_loops_and_keys_are_editable` | PASS |
| 關鍵影格數量 | `test_loops_and_keys_are_editable` | PASS |
| 曲線格式 | `test_loops_and_keys_are_editable` | PASS |
| 不同大小的角色 | `test_amplitude_scales_with_height` | PASS |
| 左右對稱 | `test_left_right_mirror` | PASS |
| 持物角色降低手臂幅度 | `test_motion_factor` | PASS |
| 頭髮與裙擺的次要動作 | `test_secondary_motion_for_hair`（只測 hair；skirt 由同一段程式處理，只有真實角色預覽的目視） | hair PASS；skirt 自動化 NOT_TESTED |
| 骨頭不存在時略過 | `test_absent_bones_skipped` | PASS |

### spine-exporter

| Scenario | 證據 | 狀態 |
|---|---|---|
| 結構完整 | `test_export_validate.py::test_structure_and_image_sizes` | PASS |
| 指定版本 | `test_spine_version_option` | PASS |
| 與官方匯出檔的鍵名一致 | `test_keys_exist_in_official_export`（固定資料 `tests/fixtures/spine43_keys.json`，取自官方 spine-runtimes 4.3 spineboy-pro.json） | PASS |
| 匯入成功 | 需要完整版 Spine | **BLOCKED** |
| 匯入失敗 | `test_cli_failure_is_fail_with_log`、`test_missing_exe_is_fail_not_crash`（以假執行檔測試包裝程式邏輯，**不是** Spine 匯入驗證） | PASS（包裝程式邏輯） |
| 往返驗證 | 需要完整版 Spine | **BLOCKED** |
| 沒有安裝 Spine | `test_no_spine_blocked` | PASS |
| 只有試用版 | `test_trial_blocked_even_when_given_explicitly`、`test_trial_environment_not_pass` | PASS |
| 輸出預覽 | `test_preview_labelled_and_moving` | PASS |
| 動畫確實在動 | `test_preview_labelled_and_moving` ＋ 目視 | PASS |

### skill-cli-integration

| Scenario | 證據 | 狀態 |
|---|---|---|
| 分步執行 | `test_cli.py::test_step_by_step`（子行程） | PASS |
| 一次跑完 | `test_run_with_workdir` | PASS |
| 指定工作目錄 | `test_run_with_workdir` | PASS |
| 圖片尚未分層 | `test_run_without_parts_exit_2` | PASS |
| 步驟順序錯誤 | `test_wrong_order_exit_2` | PASS |
| 未預期的例外 | `test_unexpected_error_logged`、`test_tiny_and_unreadable_inputs_are_clean_errors` | PASS |
| 驗證 FAIL 的結束碼與 log | `test_validation_fail_exits_1_with_log` | PASS |
| Skill 內容一致 | `test_skill_copies_identical` | PASS |
| Skill 說明完整流程 | `test_skill_copies_identical`（關鍵字）；Claude Code 依 Skill 的步驟處理兩組真實角色（grid_overlay → parts.json → run → 檢查圖 → 修正），但不是在全新 session 透過 Skill 呼叫 | Claude Code 依步驟 PASS；Codex NOT_TESTED |

### delivery-validation

| Scenario | 證據 | 狀態 |
|---|---|---|
| 正常輸出 | `test_validate_ok` | PASS |
| 抓到被破壞的輸出 | `test_validate_catches_missing_image`、`_bad_bone`、`_short_happy` | PASS |
| 抓到錯誤的圖層位置 | `test_validate_catches_offset_attachment`、`_flipped_rotations` | PASS |
| 抓到錯誤的圖片內容 | `test_validate_catches_wrong_image_content` | PASS |
| 沒有完整版 Spine | `test_trial_environment_not_pass` | PASS |
| 有待人工修補的圖層 | `test_manual_repairs_blocked` | PASS |
| 測試結果紀錄 | 本文件 | PASS |
| 兩組真實角色 | 見下方「真實角色」；兩組只有圖片與 parts.json 不同，處理第二組期間沒有修改程式 | PASS（Spine 匯入 BLOCKED） |
| 程式沒有寫死座標 | `test_no_character_specific_code` | PASS |
| 打包內容 | `test_delivery.py::test_package_from_real_outputs`（合成角色）；實際打包 `Character-to-Spine-Deliverables/`（兩組真實角色，01～07 與 README） | PASS |
| 缺少 .spine 時的標示 | 同上測試；實際交付目錄 `.spine` 檔案數 0，README 開頭標明兩個角色 BLOCKED 與解除方式 | PASS |
| 簡報內容來自實際輸出 | 同上測試；`05_Presentation/workflow.pptx` 由 `scripts/make_slides.py` 讀取工作目錄與 pytest junit 產生，`validate.py` 結構檢查通過 | PASS |

## 真實角色（2026-11-23）

parts.json 由 Claude Code 依 `grid_overlay.png` 目測撰寫，依 `layer_preview.png`（洋紅＝未分配像素）與 `unassigned` 區塊清單修正。

| 項目 | `人.png`（主要角色） | `转场2.png`（第二組） |
|---|---|---|
| 尺寸 | 630×887 | 942×1246 |
| 部件 | 10：hair_back、leg_l/r、body、skirt、head、flower_crown、guitar、arm_l/r | 11：hair_back、arm_extra、leg_l/r、body、skirt、head、flower_crown、arm_l、petals、arm_r |
| parts.json 修正輪數 | 3（未分配像素 0.63% → 0.01%） | 2（角色本體無漏畫；其餘 12.4% 全是散落特效） |
| 圖層重組差異 `recompose_mae` | 0.0014 | 0.0014 |
| 骨架初始姿勢差異 `setup_pose`（與原圖比對） | 0.0019 PASS | 0.0018 PASS |
| bones／slots／image_references／animations | PASS（12 骨、10 槽；idle 2.0 秒、happy 2.4 秒） | PASS（13 骨、11 槽；idle 2.0 秒、happy 2.4 秒） |
| manual_repairs | BLOCKED：body（被吉他擋 87%）、hair_back（75%）、leg_l（56%）、leg_r（60%） | BLOCKED：body（55%）、hair_back（68%）、leg_l（50%） |
| spine_import | BLOCKED（試用版） | BLOCKED（試用版） |
| spine_roundtrip、spine_editable | NOT_TESTED | NOT_TESTED |
| 目視（Python Simulation Preview 4 個關鍵影格） | 蹲、跳、落地方向正確；雙手留在吉他上；頭髮、裙擺、花冠跟隨擺動 | 同左；舉高的手在跳躍頂點往上揮；花瓣跟著捧花的手 |

動畫參數調整原因：

- `人.png`：手臂抱著吉他，`arm_l` motion 0.1（撥弦）、`arm_r` 0.05（握琴頸），避免手離開吉他、露出被擋住的軀幹；`guitar` 0.2 只做輕微晃動；`skirt` 掛在 `hip`，不隨上身傾斜。
- `转场2.png`：`arm_l` 已經舉高，照預設往外轉 110° 會甩過頭頂，motion 0.25 變成揮手；`arm_r` 0.15 捧著花瓣；`petals` 掛在 `arm_r`。
- 第一次檢視主要角色時發現擠壓伸展方向相反（通用錯誤，已修正並加測試，見 KNOWN_ISSUES）。

## OpenSpec 規格驗收（2026-11-23，tasks 11.3）

- `openspec validate character-to-spine-mvp --strict`：valid。
- 7 個 capability、26 條 Requirement、65 個 Scenario，每個 Scenario 在上方對照表都有一列（以程式比對名稱，0 個遺漏）。
- 狀態統計（對照表 66 列，多出的 1 列是補充的「驗證 FAIL 的結束碼與 log」）：
  - 60 列 PASS。
  - 2 列 BLOCKED：Spine 匯入成功、往返驗證，需要完整版授權。
  - 4 列部分通過：
    - 包裝程式邏輯 PASS，但不是 Spine 驗證。
    - hair PASS、skirt 自動化 NOT_TESTED。
    - Skill 由 Claude Code 依步驟執行 PASS，Codex NOT_TESTED。
    - 兩組真實角色 PASS，但 Spine 匯入 BLOCKED。
- 未完成的 task：7.7（BLOCKED，需完整版 Spine）。
- 結論：**不可封存（archive）**。7.7 與 Spine 相關 scenario 仍是 BLOCKED，等授權到位、實測後再封存。

## Definition of Done（tasks 11.4）

| 項目 | 驗收標準 | 狀態 | 證據 |
|---|---|---|---|
| CLI | 可以執行核心工作流程 | PASS | `test_cli.py` 子行程測試；兩組真實角色 `c2s run` 結束碼 0 |
| Skill | Claude／Codex 使用共用 Python 核心 | Claude PASS／Codex NOT_TESTED | SKILL.md 只呼叫 `c2s`，三份內容一致；Claude Code 依 Skill 步驟處理兩組真實角色；未在 Codex 實際執行 |
| 角色處理 | 輸出可用分層 PNG 與 Metadata | PASS（人工修補 BLOCKED） | 兩組 `recompose_mae` 0.0014；被大面積遮擋的部件只有填補草稿，列在 `repair_tasks.md` |
| 通用性 | 至少兩組不同角色使用相同流程 | PASS | `人.png`（10 部件）、`转场2.png`（11 部件）；處理第二組期間沒有修改程式 |
| 骨架 | Bones、Slots、Attachments 正確 | PASS（Spine 內 NOT_TESTED） | 驗證器 bones／slots／image_references PASS；初始姿勢與原圖差異 0.0019／0.0018 |
| 動畫 | 至少完成 Idle／Happy | PASS（Spine 內播放 NOT_TESTED） | idle 2.0 秒、happy 2.4 秒；關鍵影格格式對照官方 4.3 匯出檔鍵名；Python Simulation Preview 目視 |
| Spine | `.spine` 可開啟、可編輯 | **BLOCKED** | 只有試用版（Launcher 4.3.08／Editor 4.3.26），CLI 無匯入參數、不能存檔 |
| pstack | 工程審查通過 | 等價審查 PASS／pstack 本身 NOT_TESTED | pstack skill 只能由使用者呼叫；兩次獨立子代理審查，Critical 1、Major 10 全部修正並有回歸測試 |
| OpenSpec | 規格驗收通過 | 部分（Spine 相關 BLOCKED） | 見上一節 |
| 文件 | 使用方式與技術限制記錄完整 | PASS | `README.md`、`docs/`、交付目錄 `README.md` |

**整體：不能標記為完成。** Spine 可編輯專案（交付物 A）在完整版授權到位前是 BLOCKED。其餘可在本機驗證的項目都已通過並有證據。

## quality-hardening（2026-11-23）

| 指令 | 結果 |
|---|---|
| `.venv\Scripts\python.exe -m pytest -q` | **108 passed**（約 3 分鐘）。新增 `tests/test_quality.py` 23 個、analyzer 3 個；既有測試全數保留 |
| 改壞驗證：在暫存複本中逐一改壞 6 處，只跑對應的測試 | 6 個全部被抓到，見下表 |
| 兩組真實角色刪除工作目錄後 `c2s run` 兩次，比對雜湊 | `spine/character.json`、`tuning.json`、`metadata.json`、`quality_report.json`、`validation_report.json`、全部 `layers/*.png` 逐位元組相同（同一台機器、同一路徑、`requirements-lock.txt` 的版本；JSON 內含絕對路徑） |

### 改壞驗證（回應最終驗收審查 M4）

| 改壞的地方 | 抓到它的測試 |
|---|---|
| animate／prepare 不刪除舊的品質報告 | `test_stale_report_after_prepare_and_animate` |
| 破洞偵測永遠回傳空 | `test_real_holes_ignore_background_enclosed_by_new_contact` |
| 接觸約束算了但沒套用 | `test_contact_limit_is_applied` |
| refine 不重設 tuning | `test_refine_is_deterministic_with_fixes`（第一版沒抓到，加強斷言後抓到） |
| 不檢查穿插 | `test_detects_interpenetration` |
| prepare 不檢查來源是否更新 | `test_sidecar_edit_requires_reanalyze` |

### 真實角色的品質檢查（parts.json 在 `examples/real/`，加上 attach）

| 項目 | `人.png` | `转场2.png` |
|---|---|---|
| 自我修正 | 第 0 輪：吉他補圖露出 2.48%（歸因 arm_l）、頭髮離開肩膀的細縫 0.0031（歸因 hair_back）→ 第 1 輪 0 異常 | 第 0 輪：leg_r 露出 12.4%（歸因 skirt）、細縫 0.0046 → 3 輪後只剩 leg_r 露出 2.03% |
| 最終 tuning | happy：arm_l ×0.5、hair_back ×0.5 | happy：skirt ×0.125、hair_back ×0.5 |
| 接觸（重疊相對初始的最低值） | 左手與吉他 95.5%、右手與吉他 89.1% | 右手與花瓣 93.4% |
| 穿插（新重疊 ÷ 較小部件，最大值） | 1.8%（右手與頭，門檻 2%） | 0% |
| 接觸約束自動算出的幅度上限 | arm_l 0.036、arm_r 0.144、guitar 0.274。手臂幾乎不動，以保持接觸 | — |
| 補圖降級為 needs_manual | 無 | leg_r（留出誤差 0.089、被遮輪廓 32%、露出 2.03%） |
| 不可靠、門檻內但有露出（報告列為建議目視） | guitar 1.7%、head 1.0%、skirt 0.7% | petals 1.9%、head 1.2%、skirt 0.4% |
| `animation_quality` | PASS（detail 附建議目視清單） | PASS（detail 附需人工與建議目視清單） |
| 整體驗證 | BLOCKED（manual_repairs、spine_import） | BLOCKED（同左） |
| 目視 | Happy 四個關鍵影格雙手都在吉他上；擠壓伸展與跳躍保留 | 第 0 輪破洞影格目視為頭髮與袖子間的真實細縫 |

### Spec scenario 對照（quality-hardening）

| Capability | Scenario | 證據 | 狀態 |
|---|---|---|---|
| asset-persistence | 圖片旁的 parts.json 是正式來源 | `test_analyzer.py::test_sidecar_is_the_source_of_truth`、`test_workdir_parts_json_used_without_sidecar`、`test_invalid_source_removes_stale_normalized_copy`、`test_quality.py::test_sidecar_edit_requires_reanalyze` | PASS |
| asset-persistence | 人工修補圖存到永久位置 | `test_replace_goes_to_permanent_overrides`、`test_override_backup` | PASS |
| asset-persistence | 重建包含人工修補 | `test_rebuild_after_deleting_output`；真實角色重建比對 | PASS |
| repair-risk | 單色部件可靠 | `test_solid_fill_is_reliable` | PASS |
| repair-risk | 高紋理部件不可靠 | `test_stripes_are_unreliable` | PASS |
| repair-risk | 被遮住的輪廓 | `test_hidden_contour_is_unreliable` | PASS |
| repair-risk | 不可靠補圖露出 | `test_detects_unreliable_repair_exposure`、`test_unreliable_exposure_within_threshold_is_reported`；转场2 leg_r | PASS |
| animation-quality | 正常動畫沒有異常 | `test_clean_character_has_no_anomalies` | PASS |
| animation-quality | 抓到關節縫隙 | `test_detects_joint_gap_and_attributes_it` | PASS |
| animation-quality | 抓到補圖露出 | `test_detects_unreliable_repair_exposure`、`test_refine_fixes_and_records_rounds` | PASS |
| animation-quality | 輸出異常影格 | `test_detects_unreliable_repair_exposure`、`test_unfixable_is_blocked_with_evidence` | PASS |
| animation-quality | （破洞） | `test_real_holes_ignore_background_enclosed_by_new_contact`；真實角色第 0 輪 | PASS |
| motion-constraints | 宣告不存在的部件 | `test_attach_to_unknown_part_is_rejected` | PASS |
| motion-constraints | 手離開道具 | `test_separation_detected_without_constraint`、`test_contact_limit_is_applied`、`test_attach_without_contact_refuses_rig` | PASS |
| motion-constraints | 道具揮進臉 | `test_detects_interpenetration` | PASS |
| motion-constraints | 頭髮背景層不算穿插 | `test_detects_interpenetration` | PASS |
| self-correction | 修正後通過 | `test_refine_fixes_and_records_rounds` | PASS |
| self-correction | 修正後仍失敗 | `test_unfixable_is_blocked_with_evidence`、`test_detects_joint_gap_and_attributes_it` | PASS |
| self-correction | 確定性 | `test_refine_is_deterministic_with_fixes`、`test_rebuild_after_deleting_output` | PASS |
| self-correction | 尚未執行 refine | `test_stale_quality_report_is_not_trusted`、`test_stale_report_after_prepare_and_animate` | PASS |
## animation-liveliness（2026-11-23）

量測工具 `scripts/motion_metrics.py` 量的是接觸點跟著手臂骨頭、扣掉身體移動後的位置。

- **最大位移**：相對原位的最大距離。
- **每秒路徑**：每秒走過的路徑長度。
- **草稿露出**：所有有補圖的部件，草稿在動畫中被看見的最大比例。

流程是確定性的，同一份輸入重跑數字完全相同，所以每個數字都是單次量測，不需要取多次中位數。

量測快照存在 `.audit/`（不進版控），有兩個例外：

- H1 只有當時的輸出，沒有存快照，事後無法重現（H1 已回退）。
- 反事實估算是在已刪除的複本上做的。

| 假設 | 結果 | 處理 |
|---|---|---|
| H1：容許位移改看道具內部空間 | 撥弦手 4.4→6.1px，但握琴頸的手 8.8→4.4px，總和 13.2→10.5px | 回退 |
| H2：道具帶動抱著它的手 | 第一版讓转场2 捧花手 8.6→38.3px、身體草稿 3.5%→12.3%（退步）；限縮後转场2 不變，人.png 總和 13.2→17.9px | 保留限縮版 |
| H3：撥弦節奏（單獨） | 人.png 撥弦手每秒 14.2→38.8px，但後髮草稿 3.51%→5.36%（目視可見） | 回退 |
| H4：需人工草稿也納入自我修正（單獨） | 腿草稿 14%→3.4%，但手路徑約減半 | 單獨不採用 |
| H3＋H4 | 人.png 撥弦手每秒 14.2→37.5px、握琴頸 34.1→39.8px；腿草稿 14.1%→3.4%、身體 2.6%→2.0%。**代價**：吉他擺幅約減半（轉角 2.74°→1.25°、相對身體位移 8.9→4.0px），握琴頸的手最大轉角 15.8°→7.9°，裙擺與腿的幅度也被降低（tuning：skirt ×0.25、leg ×0.5）。转场2：草稿變少，但捧花手 8.6→2.2px、每秒 15.7→3.9px（約 −75%） | 保留（取捨見 DECISIONS D-36） |

反事實估算（複本中把部件標為已補好，重跑自我修正）：

| 情境 | 撥弦手最大位移 | 撥弦手每秒路徑 |
|---|---|---|
| 目前 | 5.1px | 37.5px |
| 吉他補好 | 9.5px | 74.3px |
| 全部補好 | 10.2px | 75.0px |

完成條件「撥弦手最大位移 ≥13px」**NOT MET**（量到 5.1px，基準 4.4px，+16%），限制來源見 KNOWN_ISSUES K-18。改善主要表現在每秒路徑（撥弦節奏），不是最大位移。

需人工草稿露出的 2% 門檻在 3 輪修正後仍未全部達到：

- 人.png：後髮 3.2%、腿 3.4%、3.2%。
- 转场2.png：第三隻手 7.2%、腿 10.2%、舉高的手 4.1%。

這些部件都在修補清單上，不算未解決的動畫異常。

回歸測試：在改動前的程式（git worktree 取出 `527b7e4`）上執行，3 個新測試全部失敗，輸出存於 `.audit/fail_before_527b7e4.txt`；改動後通過。測試清單：

- `test_prop_carries_attached_arm`（改動前：手臂的父骨頭是 body）。
- `test_needs_manual_drafts_are_kept_out_of_view`。
- `test_carried_arm_strums`（改動前：轉角只變號 3 次）。
- 修補報告 `tests/test_visual_report.py` 3 個。
- 打包時的 Spine 匯入說明（`test_delivery.py`）。

整套測試 114 passed。

目視：

- 最終狀態的 `Character-to-Spine-Deliverables/02_Layered_Assets/<角色>/report/visual_check.png`（打包時產生）：兩個角色的接觸點都在圈中央、沒有破圖。
- `output/ren_strum_strip.png`：雙手在吉他上、沒有破圖。
- 修補三格對照圖：子代理與我各自看過。
