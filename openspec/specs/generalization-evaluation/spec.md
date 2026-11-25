# generalization-evaluation Specification

## Purpose
TBD - created by archiving change character-generalization. Update Purpose after archive.
## Requirements
### Requirement: 同一套流程處理所有案例
執行器 SHALL 對每個案例以及既有的 `人`、`转场2` 執行相同的 `c2s run`，不得為個別案例使用不同的程式路徑或參數。

#### Scenario: 一次執行
- **WHEN** 執行 `scripts/generalization.py run`
- **THEN** `output/generalization/results.json` 內每個案例與兩組既有角色各有一筆結果，並記錄所用的指令

### Requirement: 量測項目
每筆結果 MUST 包含：驗證器各項狀態、重組與原圖的差異、未分配前景比例、逐格品質的未解問題、每個肢體相對身體的動作量、是否只剩整體跳動、自我修正係數、各部件的補圖露出量、需人工處理的部件清單。

#### Scenario: 沒有持物的角色
- **WHEN** 案例沒有任何 `attach`
- **THEN** 結果仍包含每隻手臂與腿的動作量

#### Scenario: 既有量測不變
- **WHEN** 對 `人` 重新量測 attach 接觸點的位移
- **THEN** 數值與擴充前的 `motion_metrics.py` 相同

### Requirement: 六級判定
執行器 SHALL 依證據把每個案例判為 PASS、PARTIAL、FAIL、BLOCKED、UNSUPPORTED 或 NOT_TESTED，並列出判定理由。驗證器原有的狀態 MUST 原樣保留在結果中。

#### Scenario: 需要人工修補
- **WHEN** 流程完成、驗證器沒有 FAIL，但有 `needs_manual` 部件
- **THEN** 判定為 PARTIAL，理由列出這些部件

#### Scenario: 本應支援卻失敗
- **WHEN** 預期範圍是 supported 的案例結束碼為 1，或有登記門檻未達且不屬於素材限制
- **THEN** 判定為 FAIL

#### Scenario: 預期支援卻宣告超出範圍
- **WHEN** 預期範圍是 supported 的案例，其 `parts.json` 宣告 unsupported
- **THEN** 判定為 FAIL，不是 UNSUPPORTED

#### Scenario: 尚未執行
- **WHEN** 某案例沒有執行結果
- **THEN** 判定為 NOT_TESTED

### Requirement: 區分素材限制與演算法限制
未解的品質問題 MUST 標明是素材限制（被遮擋的部分不存在於原圖）或演算法限制（骨架、動畫或切圖規則造成）。

#### Scenario: 草稿露出
- **WHEN** 手臂動作因避免草稿露出而被縮小到登記的過度縮小門檻以下
- **THEN** 結果標記為過度縮小，並指出限制來源是哪個部件的草稿

### Requirement: 修改前後比較
每次核心修改前後 SHALL 各保存一份快照，包含所有案例的數據與圖片。任一既有角色的登記指標變差，或新案例的整體等級下降，該修改 MUST 回退。

#### Scenario: 修改造成退步
- **WHEN** 某次修改後 `转场2` 的補圖露出量超過修改前
- **THEN** 該修改被回退，嘗試與結果記入報告

#### Scenario: 三輪上限
- **WHEN** 同一問題已做三輪有實質差異的修正仍未解決
- **THEN** 停止修正，採用設計中的備案並在報告記為未解決

### Requirement: 報告與矩陣
系統 SHALL 產出 `docs/GENERALIZATION_TEST_REPORT.md` 與 `docs/GENERALIZATION_TEST_MATRIX.md`。矩陣由 `results.json` 產生。報告 MUST 涵蓋：五張圖的來源與類型、每張圖的處理結果、拆圖／骨架／動畫的成敗、自動與人工項目、前後比較、共通與特殊問題、已支援與未支援的角色類型、既有角色回歸結果、Skill v1.0 前待解問題。

#### Scenario: 數字可重算
- **WHEN** 重新執行 `scripts/generalization.py run` 再執行 `report`
- **THEN** 矩陣的數字與報告引用的數字一致

#### Scenario: 不寫成已完成
- **WHEN** 某項目是 BLOCKED、NOT_TESTED 或 FAIL
- **THEN** 報告以該狀態呈現，不使用「已完成」「已支援」等字眼

### Requirement: 視覺品質驗收
每個案例 SHALL 保存一張視覺驗收圖，包含原圖、圖層重組、骨架圖（骨頭、pivot、父子連線疊在原圖上），以及 Idle 與 Happy 的關鍵影格。視覺判斷 MUST 涵蓋分層品質、關節位置、動作自然度、遮擋補圖四項，每項記錄 OK、問題或無法判斷，並附一句依據。自動量測與目視判斷 MUST 分欄記錄，不得互相取代。目視者 MUST 標明身分：Agent 目視與使用者目視分開，使用者尚未確認的欄位標為 NOT_TESTED。

#### Scenario: 數值全過但目視有問題
- **WHEN** 某案例的自動量測全部在門檻內，但目視發現手臂 pivot 在手肘
- **THEN** 該案例不得判為 PASS，判定理由列出目視問題

#### Scenario: 缺少視覺驗收圖
- **WHEN** 某案例沒有視覺驗收圖或沒有目視紀錄
- **THEN** 該案例的判定上限為 NOT_TESTED

### Requirement: 誠實的成功率
報告 SHALL 以五個類別計數：支援並完成（PASS）、部分完成需人工修補（PARTIAL）、超出目前支援範圍（UNSUPPORTED）、技術失敗（FAIL）、缺少測試素材（BLOCKED）。成功率的分子 MUST 只計 PASS，「可處理率」的分子只計 PASS 與 PARTIAL；兩者分母都是實際執行的真實陌生角色數。UNSUPPORTED MUST NOT 計入分子。合成角色 MUST NOT 計入分子或分母。

#### Scenario: 兩張超出範圍
- **WHEN** 五張真實圖中一張 PASS、兩張 PARTIAL、一張 UNSUPPORTED、一張 FAIL
- **THEN** 報告寫成功率 1/5、可處理率 3/5，並另列 UNSUPPORTED 1、FAIL 1

#### Scenario: 合成角色全過
- **WHEN** 合成角色全部 PASS，但真實圖只有三張
- **THEN** 成功率的分母是 3，合成結果只出現在輔助欄位

