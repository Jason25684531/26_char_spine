## ADDED Requirements

### Requirement: 由 metadata 建立人形骨架
系統 SHALL 依 preset `humanoid-chibi` 與 `metadata.json` 建立骨架：`root → hip → body → head / arm_l / arm_r`、`hip → leg_l / leg_r`。所有骨頭位置 MUST 由部件的 pivot 與圖層資料推算，程式中 MUST NOT 含有特定角色的座標。

#### Scenario: 兩個比例不同的角色
- **WHEN** 對兩個尺寸與比例不同的角色各自執行 rig
- **THEN** 兩者都產生結構相同的必要骨頭，骨頭位置各自對應自己的 pivot

#### Scenario: 骨架初始姿勢還原圖層位置
- **WHEN** 用產生的骨頭、插槽、附件資料重新算出初始姿勢
- **THEN** 與直接疊圖層的結果平均差異低於 0.02

#### Scenario: 自訂 pivot
- **WHEN** `parts.json` 為某個部件指定 `pivot`
- **THEN** 該骨頭的世界座標等於指定的 pivot 換算後的位置

### Requirement: 額外部件各自成為骨頭
6 個必要部件以外的每個部件，系統 SHALL 為它建立一根骨頭與一個插槽，父骨頭取自 `parts.json` 的 `parent`（預設 `body`）。部件數量 MUST NOT 有上限。

#### Scenario: 帶頭髮與道具的角色
- **WHEN** `parts.json` 另外定義了 `hair_back`（parent 為 `head`）與 `guitar`（parent 為 `body`）
- **THEN** 骨架多出這兩根骨頭，父子關係與指定相同，各有一個插槽

#### Scenario: parent 不存在
- **WHEN** 某個部件的 `parent` 指向不存在的骨頭
- **THEN** 系統回報錯誤並指出是哪個部件

### Requirement: 插槽順序反映前後關係
系統 SHALL 為每個有圖層的部件建立一個插槽，插槽順序 MUST 依 z 由後到前排列。

#### Scenario: 圖層順序
- **WHEN** 部件的 z 值為 body 2、head 5、arm_l 7
- **THEN** 插槽順序為 body、head、arm_l

### Requirement: 圖層不齊時拒絕綁定
缺少任何必要部件的圖層時，系統 MUST 拒絕建立骨架，並列出缺少的部件與補齊方式。

#### Scenario: 缺少必要圖層
- **WHEN** `metadata.json` 中 `leg_r` 沒有圖層
- **THEN** rig 不產生 `rig.json`，訊息列出 `leg_r` 並指向 `repair_tasks.md`，CLI 結束碼為 2
