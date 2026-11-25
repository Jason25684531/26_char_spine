## ADDED Requirements

### Requirement: 產生 Idle 與 Happy 骨架動畫
系統 SHALL 產生 `idle` 與 `happy` 兩個動畫，內容 MUST 是骨頭的 rotate、translate、scale 關鍵影格。`happy` 的長度 MUST 至少 2 秒，且 MUST 包含身體上下跳動、身體擠壓伸展、頭部擺動與手臂動作。

#### Scenario: Happy 動畫內容
- **WHEN** 對完成骨架的角色執行 `c2s animate --motion happy`
- **THEN** `animations.json` 含有 `idle` 與 `happy`，`happy` 長度不少於 2 秒，且 `hip` 有 translate、`body` 有 scale、`head` 與手臂骨頭有 rotate 關鍵影格

#### Scenario: 首尾相接
- **WHEN** 檢查任一動畫每條 timeline 的第一格與最後一格
- **THEN** 兩者的值相同，動畫可以循環播放

### Requirement: 關鍵影格可在 Spine 編輯
每條 timeline 的關鍵影格 MUST 是稀疏的姿勢關鍵格，並使用 Spine 4.x 的曲線格式；系統 MUST NOT 以逐幀取樣或影片代替骨架動畫。

#### Scenario: 關鍵影格數量
- **WHEN** 檢查 `happy` 的任一條 timeline
- **THEN** 關鍵影格數不超過 16 個，時間遞增

#### Scenario: 曲線格式
- **WHEN** 關鍵影格帶有 bezier 曲線
- **THEN** rotate 的 `curve` 有 4 個數字，translate 與 scale 的 `curve` 有 8 個數字

### Requirement: 動作幅度隨角色與部件設定調整
位移幅度 SHALL 依角色高度換算，左右肢體的旋轉方向 SHALL 依其位於身體哪一側決定。每個部件的 `motion` 係數 SHALL 等比例縮放該骨頭的動作幅度，`role` SHALL 決定套用的動作類型。

#### Scenario: 不同大小的角色
- **WHEN** 兩個角色高度相差一倍
- **THEN** `hip` 跳躍位移的峰值也相差約一倍

#### Scenario: 左右對稱
- **WHEN** 檢查 `arm_l` 與 `arm_r` 在同一時間點的旋轉值
- **THEN** 兩者正負號相反

#### Scenario: 持物角色降低手臂幅度
- **WHEN** 手臂部件設定 `motion` 為 0.2
- **THEN** 該手臂旋轉的峰值是預設值的 0.2 倍

#### Scenario: 頭髮與裙擺的次要動作
- **WHEN** 角色有 `role` 為 `hair` 或 `skirt` 的部件
- **THEN** 這些骨頭在 `happy` 中有 rotate 或 scale 關鍵影格

#### Scenario: 骨頭不存在時略過
- **WHEN** 角色沒有某個選用的部件
- **THEN** 動畫不包含該骨頭的 timeline，其餘動畫正常產生
