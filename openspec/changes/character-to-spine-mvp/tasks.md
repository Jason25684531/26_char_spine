每完成一組：更新本檔勾選、`docs/AGENT_STATE.md`、`docs/TEST_RESULTS.md`，並建立一個 Git commit。狀態只用 PASS／FAIL／BLOCKED／NOT_TESTED。

## 1. 專案基礎與架構審查

- [x] 1.1 `git init`，確認 `.gitignore` 沒有排除 `openspec/`、`docs/`、`examples/`、`tests/`，建立第一個 commit
- [x] 1.2 `uv venv` 建立虛擬環境並 `uv pip install -e ".[dev]"`，確認 `c2s --version` 可執行
- [x] 1.3 把 `src/` 下四張原始 PNG 複製到 `examples/real/`（原檔不動），記錄雜湊值
- [x] 1.4 pstack 架構審查：嘗試呼叫 `/architect` 與 `/interrogate`；不可用時讀取其 SKILL.md 並派獨立子代理審查 design.md 與程式草稿（pstack skill 只能由使用者呼叫；改由獨立子代理審查，見 design.md「工程審查結果」）
- [x] 1.5 把審查結果回寫到 design.md 與本檔，建立 `docs/ARCHITECTURE.md`（指向 design.md 的摘要）
- [x] 1.6 建立 `docs/AGENT_STATE.md`、`docs/KNOWN_ISSUES.md`、`docs/TEST_RESULTS.md`

## 2. 合成測試角色

- [x] 2.1 `scripts/make_synthetic.py`：角色 A（透明背景、遮罩定義部件、6 個必要部件）（實際放在 tests/synthetic.py，見 D-19）
- [x] 2.2 角色 B（不透明純色背景、多邊形定義、比例不同、多了 `hair_back` 與一個道具、含一個大面積遮擋的部件）
- [x] 2.3 每個合成角色輸出各部件的真實範圍，供測試比對

## 3. character-analyzer

- [x] 3.1 執行草稿的 `analyze`，修正發現的錯誤
- [x] 3.2 `parts.json` 檢查加入 `role`、`motion` 欄位的驗證
- [x] 3.3 測試：透明 PNG、不透明背景去背、圖片不存在、整張透明、原圖雜湊值不變
- [x] 3.4 測試：合法的 `parts.json`、各種格式錯誤、沒有 `parts.json`（範本與結束碼 2）、缺少部分必要部件

## 4. image-processor

- [x] 4.1 執行草稿的 `prepare`，修正發現的錯誤
- [x] 4.2 修正：骨架原點與外框改由部件範圍的聯集計算，未分配的前景像素不進入任何圖層
- [x] 4.3 測試：圖層位置與真實範圍相差不超過 2 像素、`recompose_mae` 低於 0.02、散落特效不影響原點
- [x] 4.4 測試：小面積遮擋為 `auto_repaired`、大面積為 `needs_manual`、完全遮住不輸出圖層
- [x] 4.5 測試：`missing_parts.json`、`repair_tasks.md`、`layer_preview.png` 的內容
- [x] 4.6 測試：遮罩定義的部件、`--part` 只重寫一個圖層、`--replace` 兩種尺寸與重跑後保留、尺寸錯誤的替換圖
- [x] 4.7 目視檢查兩個合成角色的 `layer_preview.png`

## 5. auto-rigging

- [x] 5.1 執行草稿的 `build_rig`，修正發現的錯誤
- [x] 5.2 測試：兩個合成角色的必要骨頭結構相同且位置對應各自的 pivot、自訂 pivot 生效
- [x] 5.3 測試：額外部件的骨頭與 parent、parent 不存在時報錯、插槽順序依 z、缺少必要圖層時拒絕並回結束碼 2

## 6. animation-builder

- [x] 6.1 執行草稿的 `build_animations`，修正發現的錯誤
- [x] 6.2 加入 `role` 與 `motion`：幅度係數、`hair`／`skirt` 的延遲次要擺動、`prop` 的跟隨動作
- [x] 6.3 測試：`happy` 不少於 2 秒且含指定的 timeline、首尾相接、關鍵影格數不超過 16、曲線數字個數
- [x] 6.4 測試：幅度隨角色高度縮放、左右手正負號相反、`motion` 0.2 的峰值、選用骨頭不存在時略過

## 7. spine-exporter 與預覽

- [x] 7.1 執行草稿的 `export`，修正發現的錯誤
- [x] 7.2 測試：JSON 結構、附件寬高等於 PNG 實際尺寸、`--spine-version`
- [x] 7.3 測試：輸出的鍵名都出現在官方 4.3 spineboy 匯出檔（把官方檔的鍵名清單存成測試固定資料，不存整個檔案）
- [x] 7.4 測試：找不到 Spine 時 BLOCKED、只有試用版時 BLOCKED 且沒有 `.spine`
- [x] 7.5 預覽加上「Python Simulation Preview」字樣；測試幀數大於 1、第一幀與中間幀不同
- [x] 7.6 目視檢查兩個合成角色的 `idle` 與 `happy` 預覽 GIF，確認動作方向與圖層順序合理
- [ ] 7.7 完整版 Spine CLI 匯入與往返驗證 —— BLOCKED：需要使用者安裝並啟用完整版授權。到位後執行並把指令與輸出記入 `docs/TEST_RESULTS.md`

## 8. skill-cli-integration

- [x] 8.1 以子行程實際執行 `c2s`：分步流程、`run`、`--workdir`、各種結束碼
- [x] 8.2 測試：未預期例外寫出 `c2s_error.log`
- [x] 8.3 撰寫 `skills/character-to-spine/SKILL.md` 與 `references/parts-json.md`（格式說明直接寫在 SKILL.md，不另開 references/）
- [x] 8.4 複製到 `.claude/skills/` 與 `.codex/skills/`，測試三份內容一致
- [x] 8.5 `README.md`：安裝、指令、流程、限制

## 9. 驗證器

- [x] 9.1 執行草稿的 `validate`，修正發現的錯誤
- [x] 9.2 測試：正常輸出各項 PASS；刪圖、錯誤的骨頭名稱、過短的 `happy`、偏移的附件各自觸發對應的 FAIL
- [x] 9.3 測試：試用版環境下 `spine_import` 為 BLOCKED、整體狀態不是 PASS；有 `needs_manual` 時 `manual_repairs` 為 BLOCKED

## 10. 真實角色

- [x] 10.1 檢視 `人.png`，撰寫 `examples/real/人.parts.json`（預計含 `hair_back`、`skirt`、`guitar`、`flower_crown` 等額外部件，手臂設定較低的 `motion`）
- [x] 10.2 執行 `c2s run`，檢視 `layer_preview.png` 並反覆修正 `parts.json`，最多三輪；仍不理想的部件改列人工修補任務
- [x] 10.3 檢視 `happy` 預覽，調整 pivot、`motion`、`role` 直到動作自然；記錄調整原因
- [x] 10.4 對 `转场2.png` 重複 10.1 到 10.3（只標角色本體，不含花瓣特效），期間不得修改 `src/character_to_spine/` 來遷就這張圖；若必須修改，要是對兩個角色都適用的通用修正
- [x] 10.5 檢查程式碼內沒有任何角色檔名或像素座標
- [x] 10.6 把兩組角色的驗證報告與待人工修補清單記入 `docs/TEST_RESULTS.md` 與 `docs/KNOWN_ISSUES.md`

## 11. 雙重驗收

- [ ] 11.1 pstack `/interrogate`（或等價的獨立子代理審查）：實際錯誤、未處理例外、寫死座標、缺少回歸測試、沒有證據的成功宣告
- [ ] 11.2 修正審查發現的問題並重跑全部測試
- [ ] 11.3 OpenSpec 驗收：逐條對照每個 Requirement 與 Scenario 的測試證據，寫入 `docs/TEST_RESULTS.md`；`openspec validate --strict` 通過
- [ ] 11.4 對 Definition of Done 表逐項給出狀態與證據

## 12. 交付

- [x] 12.1 安裝 python-pptx；`scripts/make_slides.py` 由實際輸出產生 `workflow.pptx`
- [x] 12.2 `scripts/package_deliverables.py` 組出 `Character-to-Spine-Deliverables/`
- [x] 12.3 測試：打包目錄結構、沒有 `.spine` 時 README 標明 BLOCKED 且目錄內沒有假檔案
- [ ] 12.4 依最終回報格式整理完成狀態、BLOCKED 項目與下一步
