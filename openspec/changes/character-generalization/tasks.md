## 1. 基準與環境

- [x] 1.1 用 `.venv\Scripts\python.exe -m pytest -q` 跑完整測試，結果存到 `output/generalization/pytest_baseline.txt`
- [x] 1.2 對三個既有 change 與本 change 執行 `openspec validate --strict`，記錄結果
- [x] 1.3 重跑 `c2s run` 於 `人.png`、`转场2.png`，確認與現有 `output/ren`、`output/zc2` 的 Spine JSON 相同，作為回歸基準
- [x] 1.4 把審查時讀到的實況（preset、anchors、量測範圍、K-19）與先前報告不一致之處記入 `docs/AGENT_STATE.md`

## 2. 測試素材（三層備案）

- [x] 2.1 建立 `examples/generalization/`、`inbox/` 與 `manifest.json` 結構，寫入排除清單（四張既有圖的雜湊）
- [x] 2.2 檢查 `inbox/` 是否有使用者提供的圖，有就依類型歸到 A–E（skip：使用者沒有提供圖片，五類都找到公開授權素材，未建立 inbox）
- [x] 2.3 缺的類型搜尋公開授權（CC0 優先）角色圖，下載到各自資料夾，記錄網址、作者、授權、SHA-256；找不到的類型如實記錄搜尋過的來源
- [x] 2.4 仍缺的類型擴充 `tests/synthetic.py` 生成合成角色，標為 synthetic，該類型的真實素材格標 BLOCKED（skip：五類都有真實公開素材，不需要合成角色）
- [x] 2.5 為每個案例寫下圖片特徵、`expected_scope` 與成功標準
- [x] 2.6 在既有兩組角色與合成角色上量新門檻（手臂動作量 2%、整體跳動 0.5%、過度縮小 0.25），把依據寫入 `criteria_basis` 後定案
- [x] 2.7 提交 manifest（此提交即凍結點，之後才允許對新圖執行 `c2s`）

## 3. 執行器與量測

- [x] 3.1 `scripts/generalization.py run`：檢查 manifest 欄位與雜湊，對每個案例加既有兩組角色執行 `c2s run`，寫出 `results.json`
- [x] 3.2 擴充 `scripts/motion_metrics.py`：量每個肢體的肢端相對身體位移；加測試確認既有 attach 量測數值不變
- [x] 3.3 加入重組差異、未分配比例、循環首尾一致、只剩整體跳動、過度縮小的量測
- [x] 3.4 六級判定表與判定理由，附單元測試（每個等級至少一個案例，含「預期支援卻宣告超出範圍 = FAIL」）
- [x] 3.5 `snapshot <label>` 與兩個 label 的差異表
- [x] 3.6 `provenance`：多邊形雷同比對與座標範圍檢查，用複製 `人.parts.json` 的假案例確認會判 FAIL
- [x] 3.7 `report`：由 `results.json` 產生 `docs/GENERALIZATION_TEST_MATRIX.md`

## 4. Skill 實測與分析（真正的 Claude Code session）

- [x] 4.1 `scripts/generalization.py skill <id>`：以 `claude -p` 自然語言提示處理每張新圖，存下 stream-json
- [x] 4.2 案例 A 另以 `/character-to-spine` 觸發一次
- [x] 4.3 從紀錄判定：Skill 工具呼叫、`c2s` 執行、禁止路徑、失敗回報，寫入 `docs/generalization/<id>/skill_session.md`
- [x] 4.4 執行 `provenance` 查核，結果寫入 `results.json`
- [x] 4.5 凍結各案例的 `parts.json`（提交），之後的前後比較都用同一份
- [x] 4.6 Skill 入口若壞掉，只做最小修正並同步到 `.claude/`、`.codex/` 複本

## 4b. 視覺驗收

- [x] 4b.1 `sheet` 子命令產生每個案例的 `visual_sheet.png`（原圖、重組、骨架圖、Idle／Happy 關鍵影格）
- [x] 4b.2 Agent 逐張目視，寫入 `visual_review.json`（分層、關節、動作、遮擋補圖四項，各附依據）
- [x] 4b.3 判定表納入目視：任一 ISSUE 不得 PASS；沒有目視紀錄上限 NOT_TESTED

## 5. 基準執行

- [x] 5.1 以現況程式跑全部案例，`snapshot baseline`
- [x] 5.2 逐案例檢視 `layer_preview.png`、異常影格與預覽 GIF，把每個失敗歸類為 A 分析、B 拆圖、C 補圖、D 骨架、E 動畫，並標明素材限制或演算法限制
- [x] 5.3 列出跨案例重複出現的失敗，對應到設計 D7 的假設；沒有對應失敗的假設劃掉

## 6. 範圍處理（unsupported、absent）

- [x] 6.1 先寫失敗測試：`unsupported` 結束碼 3 且不產生 `rig.json`、`absent` 的部件不建骨頭、`head`／`body` 不可缺席、宣告與部件矛盾、舊輸出失效、既有角色輸出不變
- [x] 6.2 實作於 `analyzer.py`、`rig_builder.py`、`pipeline.py`、`validator.py`、`cli.py`
- [x] 6.3 `SKILL.md` 加入兩個欄位與結束碼 3 的說明，同步複本
- [x] 6.4 需要的案例由新的子代理重新分析（規則同第 4 組），重跑後 `snapshot scope`

## 7. 技術審查

- [x] 7.1 獨立子代理對抗式審查設計、判定表與基準結果（門檻能否事後操弄、`unsupported` 是否成為逃生門、量測是否量到別的東西）
- [x] 7.2 處理審查意見，逐條記錄採納或不採納的理由

## 7b. 審查後追加

- [x] 7b.1 撤回事後放寬的素材豁免，所有評估變更登記於 manifest 的 criteria_changes，並列新舊判定
- [x] 7b.2 凍結目視判準，目視紀錄綁定驗收圖 sha256，矩陣加使用者目視欄
- [x] 7b.3 Skill 沙盒移到 repo 外；開發集每案例只採用該輪第一次有效執行，所有執行都保留紀錄
- [x] 7b.4 凍結保留集 H1–H4（預登記 expected_scope、expected_absent、expected_attached_arms、不同的觸發語句），所有修改完成前不執行
- [x] 7b.5 所有修改完成後，保留集各跑一次 Skill 實測（第一次有效執行），再執行 run、目視、判定

## 8. 共通問題修正（每個假設一輪，依基準結果決定做哪些）

- [x] 8.1 對每個被選中的假設：寫下失敗原因與假設，加一個用合成角色重現的失敗測試
- [x] 8.2 只改必要模組，跑完整 pytest
- [x] 8.3 跑全部案例加既有兩組角色，`snapshot roundN`，產生差異表
- [x] 8.4 既有角色指標變差或新案例等級下降就回退該提交，並記錄
- [x] 8.5 同一問題三輪未解即停止，採用設計表中的備案（H8 一輪即被 zc2 反例否定並回退；H9 判為特殊案例不做；K-24、K-28 留待下一階段，因保留集已用目前程式執行）
- [x] 8.6 擴充 `test_no_character_specific_code`，把測試集的檔名與案例 id 加入禁用字串

## 9. 補圖匯回與露出

- [x] 9.1 挑一個有 `needs_manual` 部件的新案例，用程式產生的替代圖層執行 `c2s prepare --replace`，確認匯回後重跑結果更新（只驗證匯回機制，不宣稱補圖品質）
- [x] 9.2 用 `scripts/visual_report.py` 產生每個案例的 `repair_priority.md` 與三格對照圖，確認露出量排序與動畫實際露出一致

## 10. 獨立驗證

- [x] 10.1 完整 pytest、`openspec validate --strict`
- [x] 10.2 獨立 QA 子代理重算 `report` 與 `provenance`、比對報告數字並抽查證據（不重跑 `run`：重跑會重產驗收圖、讓綁定 sha256 的目視紀錄失效）
- [x] 10.3 確認既有兩組角色的各項指標不低於任務 1.3 的基準

## 11. 交付

- [x] 11.1 `docs/GENERALIZATION_TEST_MATRIX.md`（由 `report` 產生）
- [x] 11.2 `docs/GENERALIZATION_TEST_REPORT.md`（十個指定章節，依證據分類，另列驗證器原有狀態；成功率只計 PASS，可處理率計 PASS＋PARTIAL，UNSUPPORTED 與合成角色不進分子）
- [x] 11.3 `docs/generalization/<id>/`：分層預覽、Idle／Happy 預覽、異常影格、修補清單、分析紀錄
- [x] 11.4 更新 `docs/KNOWN_ISSUES.md`、`docs/TEST_RESULTS.md`、`docs/AGENT_STATE.md`、`docs/DECISIONS.md`
- [x] 11.5 Git 變更摘要與 Skill v1.0 標準化建議（寫在報告第 10 節）
- [x] 11.6 確認分支仍是 `feat/character-to-spine-mvp`，沒有合併或推送
