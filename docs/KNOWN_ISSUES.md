# 已知問題

## 未解決

| # | 問題 | 狀態 | 影響 | 解除方式 |
|---|---|---|---|---|
| K-01 | 只有 Spine 試用版，CLI 沒有匯入參數也不能存檔 | BLOCKED | 無法產生 `.spine`、無法往返驗證與 Editor 可編輯性驗證 | 使用者取得完整版授權後，設定 `SPINE_EXE` 指向 `Spine.com` 並重跑 `c2s export` |
| K-02 | 使用者把 `.claude/*`、`.codex/*` 加入 `.gitignore`（同時移除了先前加入的 `openspec`） | 已接受 | Skill 只有 `skills/character-to-spine/` 這份正本進版控；clone 後需要自行複製到 `.claude/skills/`、`.codex/skills/` | 見 README「安裝 Skill」 |
| K-03 | Python Simulation Preview 只支援本專案輸出的功能（rotate／translate／scale、平切線 bezier） | 設計限制 | 在 Spine 裡手動改成其他曲線後，預覽會不準 | 預覽只用於自我檢查，正式預覽以 Spine 為準 |
| K-04 | 自動填補只用 OpenCV Telea 邊緣延伸 | 設計限制 | 大面積遮擋的部件標為 `needs_manual`，需要人工修補 | 人工修好後 `c2s prepare --replace` |
| K-05 | skirt 的次要動作沒有專門的測試角色 | NOT_TESTED | 與 hair 走同一段程式 | 真實角色（裙擺）跑通後補上 |

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
