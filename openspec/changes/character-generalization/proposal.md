## Why

系統目前只在同一個角色的兩張圖（`人.png`、`转场2.png`）上開發、調參與回歸。`examples/real/` 另外兩張圖（`人物 拷贝.png`、`预中奖.png`）也是同一個角色，不能當成新角色。現有證據無法回答「給一張陌生角色圖，系統能做到哪裡、會在哪裡誠實停下」。

審查程式後確認三個會直接影響泛化的結構性事實：

- 只有一個 preset（`humanoid-chibi`），六個必要部件缺一不可。3/4 側面看不到的手、非人形角色，目前只會得到結束碼 2「還缺資料」，沒有「超出支援範圍」這條路。
- `scripts/motion_metrics.py` 只量 `attach` 接觸點，且假設有 `body` 骨頭。沒有持物的角色量不到手臂動作量，也無法判斷「是否只剩整體上下跳」。
- 沒有機制能證明新角色的 `parts.json` 是 Agent 看新圖寫出來的，而不是沿用舊角色的座標。

## What Changes

- 建立固定的泛化測試集（A 正面 Q 版、B 3/4 側面、C 持道具、D 複雜遮擋、E 不同身形或非人形），每張圖在執行前凍結來源、授權、雜湊、圖片特徵與成功標準。
- 新增一支泛化測試執行器 `scripts/generalization.py`：對每張圖跑同一套 `c2s run`，彙整拆圖重組、逐格品質、動作幅度、補圖露出，輸出六級判定（PASS／PARTIAL／FAIL／BLOCKED／UNSUPPORTED／NOT_TESTED），同時保留驗證器原有的狀態。
- 新增 `parts.json` 來源驗證：每張新圖由沒有舊答案的獨立子代理依 `SKILL.md` 分析，並用程式比對座標是否與既有 `parts.json` 雷同。
- 擴充動作量測到所有肢體（不只 attach 接觸點），加入「只剩整體跳動」與「自我修正過度縮小」兩個判定。
- 讓系統能誠實指出限制：`parts.json` 可宣告「超出支援範圍」與「看不到的必要部件」，流程以明確狀態結束，不再卡在結束碼 2。
- 依泛化測試的失敗證據改善共通演算法（部件歸屬與邊緣、pivot 推算、露出與幅度的取捨）。每項修改先有失敗證據與假設，最多三輪，退步就回退。**不預先承諾改哪一段**，由測試結果決定。
- 確認 Skill 基本入口：自然語言能觸發、Agent 能呼叫 `c2s`、失敗能回報、使用者不必手寫 `parts.json`。只修到能用，不重新包裝。
- 產出 `docs/GENERALIZATION_TEST_REPORT.md`、`docs/GENERALIZATION_TEST_MATRIX.md` 與每張圖的輸入、分析、輸出、異常影格與修補清單。

不做：Skill 全面標準化、Web UI、MCP、付費影像 API、本地生成模型、合併到 `main`。

## Capabilities

### New Capabilities

- `generalization-test-set`：固定測試集的組成、素材來源與授權規則、執行前凍結的特徵與成功標準、素材不足時的 BLOCKED 規則。
- `generalization-evaluation`：執行器、量測項目、六級判定規則、前後比較、報告與矩陣的內容。
- `analysis-provenance`：新角色 `parts.json` 的產生方式與來源驗證。
- `scope-handling`：超出支援範圍與缺少可見部件時的宣告方式、流程行為與回報。

### Modified Capabilities

無。`openspec/specs/` 目前沒有已封存的規格；既有三個 change 的需求不變，既有兩組角色的行為以回歸測試守住。

## Impact

- 新增：`scripts/generalization.py`、`examples/generalization/`（素材、`manifest.json`、各圖的 `parts.json`）、`docs/GENERALIZATION_TEST_REPORT.md`、`docs/GENERALIZATION_TEST_MATRIX.md`、`docs/generalization/`（保留的預覽與異常影格）。
- 可能修改（依失敗證據）：`analyzer.py`、`rig_builder.py`、`image_processor.py`、`animation_builder.py`、`quality.py`、`validator.py`、`scripts/motion_metrics.py`、`skills/character-to-spine/SKILL.md`（僅最小修正）。
- 測試：既有 114 個測試必須全數通過；每項核心修改附回歸測試。
- 相依套件：不新增。只用已安裝的 OpenCV、NumPy、Pillow。
- 對外行為：下載公開授權素材（只進不出）。使用者圖片不上傳任何外部服務。
- 版控：只在 `feat/character-to-spine-mvp` 上作業，不合併、不推送。
