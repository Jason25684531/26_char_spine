每完成一組：更新本檔、`docs/AGENT_STATE.md`、`docs/TEST_RESULTS.md`，並建立 Git commit。

## 1. 資料管理（asset-persistence）

- [x] 1.1 analyze：來源優先順序改為 --parts > 圖片旁 > 工作目錄；正規化複本記錄 `source`
- [x] 1.2 prepare／--replace：修補圖改存 `<圖名>.overrides/`
- [x] 1.3 未分配像素輸出區塊清單與最近的部件（missing_parts.json），取代 output 內的開發腳本
- [x] 1.4 開發用腳本移出 output（版面預覽 → scripts/qa_slides.py），刪除其餘暫存
- [x] 1.5 測試：來源優先順序、修補圖位置、刪除工作目錄後重建結果相同

## 2. 補圖風險（repair-risk）

- [x] 2.1 `_cut` 量測 holdout_error、contour_hidden、occluders，輸出 repair_masks
- [x] 2.2 測試：單色可靠、條紋不可靠、輪廓被遮
- [x] 2.3 以實測分布校準門檻並記錄

## 3. 動畫品質（animation-quality）

- [x] 3.1 preview.py 抽出 slot_transforms，render 改用它（既有測試不變）
- [x] 3.2 quality.py：破洞、關節縫隙、attach 重疊、補圖露出；異常影格
- [x] 3.3 測試：正常無異常、刻意製造縫隙、刻意製造露出

## 4. 接觸約束（motion-constraints）

- [x] 4.1 parts.json `attach` 驗證，傳到 metadata 與 rig
- [x] 4.2 測試：不存在的 attach、分離被偵測

## 5. 自我修正（self-correction）

- [x] 5.1 tuning.json 套用到 animate；refine 迴圈與歸因修正
- [x] 5.2 refine 後不可靠且露出的補圖改 needs_manual，重寫修補任務
- [x] 5.3 validate 新增 animation_quality；c2s refine 指令；run 串入
- [x] 5.4 測試：修正後通過、三輪仍失敗為 BLOCKED、確定性

## 6. 真實角色與驗收

- [x] 6.1 兩組真實角色加上 attach，刪除 output 後重建並檢查報告與異常影格
- [ ] 6.2 獨立子代理工程審查並修正
- [ ] 6.3 Skill、README、docs、簡報、交付打包更新
- [ ] 6.4 OpenSpec 驗收、`openspec validate --strict`
