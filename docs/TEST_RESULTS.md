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
| 格式錯誤 | `test_parts_format_errors`（9 種）、`test_mask_size_mismatch` | PASS |
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
| 頭髮與裙擺的次要動作 | `test_secondary_motion_for_hair`（只測了 hair；skirt 由同一段程式處理，尚無合成角色帶裙擺） | PASS（skirt NOT_TESTED） |
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
| 未預期的例外 | `test_unexpected_error_logged` | PASS |
| Skill 內容一致 | `test_skill_copies_identical` | PASS |
| Skill 說明完整流程 | `test_skill_copies_identical`（關鍵字）；實際由 Agent 依 Skill 處理真實角色 | 關鍵字 PASS；實際使用 NOT_TESTED |

### delivery-validation

| Scenario | 證據 | 狀態 |
|---|---|---|
| 正常輸出 | `test_validate_ok` | PASS |
| 抓到被破壞的輸出 | `test_validate_catches_missing_image`、`_bad_bone`、`_short_happy` | PASS |
| 抓到錯誤的圖層位置 | `test_validate_catches_offset_attachment`、`_flipped_rotations` | PASS |
| 沒有完整版 Spine | `test_trial_environment_not_pass` | PASS |
| 有待人工修補的圖層 | `test_manual_repairs_blocked` | PASS |
| 測試結果紀錄 | 本文件 | PASS |
| 兩組真實角色 | 尚未進行（tasks 第 10 組） | NOT_TESTED |
| 程式沒有寫死座標 | `test_no_character_specific_code` | PASS |
| 打包內容、缺少 .spine 時的標示、簡報內容 | 尚未進行（tasks 第 12 組） | NOT_TESTED |
