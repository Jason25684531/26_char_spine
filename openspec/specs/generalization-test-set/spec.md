# generalization-test-set Specification

## Purpose
TBD - created by archiving change character-generalization. Update Purpose after archive.
## Requirements
### Requirement: 固定的五類測試集
系統 SHALL 以 `examples/generalization/manifest.json` 定義泛化測試集，至少包含 A 正面 Q 版人形、B 3/4 側面人形、C 手持道具、D 複雜遮擋、E 不同身形或非人形五個案例。每個案例 MUST 記錄來源類別（user／public／synthetic）、來源網址或提供者、授權、SHA-256、圖片特徵與預期範圍。

#### Scenario: 案例資料完整
- **WHEN** 執行 `scripts/generalization.py run`
- **THEN** 缺少來源、授權、雜湊或特徵任一欄位的案例被拒絕執行，並列出缺少的欄位

#### Scenario: 圖片內容被替換
- **WHEN** 案例圖片的 SHA-256 與 manifest 不同
- **THEN** 該案例不執行，結果標為 NOT_TESTED 並說明雜湊不符

### Requirement: 排除參與過開發的角色
測試集 MUST NOT 包含 `人.png`、`转场2.png`、`人物 拷贝.png`、`预中奖.png` 或它們的修改版。

#### Scenario: 放入既有角色
- **WHEN** manifest 中某案例的雜湊與 `examples/real/` 任一圖片相同
- **THEN** 執行器拒絕該案例並指出重複的檔案

### Requirement: 執行前凍結成功標準
每個案例的特徵與成功標準 MUST 在第一次對該圖執行 `c2s` 之前提交到版控。之後修改門檻 MUST 以 `criteria_changes` 記錄原值、新值與理由，報告 MUST 同時列出修改前後的判定。

#### Scenario: 事後修改門檻
- **WHEN** 某案例的 `criteria` 在已有執行結果後被修改，且沒有對應的 `criteria_changes`
- **THEN** 執行器回報錯誤，不產生該案例的判定

### Requirement: 素材不足時如實標示
缺少合適的真實圖片時，對應案例 SHALL 標為 BLOCKED。合成角色 MAY 作為輔助，但 MUST 標示為 synthetic，且 MUST NOT 計入真實角色的驗收張數。

#### Scenario: 只有合成角色
- **WHEN** 案例 E 只有程式生成的合成圖
- **THEN** 矩陣中 E 的真實素材欄為 BLOCKED，合成結果另列一欄並標示 SYNTHETIC

### Requirement: 使用者圖片不外傳
處理測試集的任何步驟 MUST NOT 把使用者提供的圖片傳送到外部服務。

#### Scenario: 執行完整測試
- **WHEN** 執行器處理 origin 為 user 的案例
- **THEN** 過程中沒有任何對外的網路請求

