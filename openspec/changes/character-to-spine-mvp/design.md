## Context

專案原本只有四張角色 PNG，沒有程式碼。2026-11-23 寫了一批 Python 草稿（`src/character_to_spine/`），從未執行過，依使用者決策視為未驗證初稿。

限制條件：

- 不用 API Key、不裝本地 AI 模型、不用第三方圖片服務。能「看圖」的只有已登入的 Claude Code／Codex。
- 這台機器只有 Spine 試用版（Launcher 4.3.08）。實測它的 CLI 沒有匯入匯出參數，也不能存檔。
- 官方 JSON 文件頁停在 3.8 格式，4.x 的格式以官方 spine-runtimes 的 spineboy 匯出檔（4.2.22、4.3.75-beta）為準。
- 主要角色 `人.png` 抱著吉他：吉他擋住身體，雙手在吉他前面。第二組真實角色 `转场2.png` 是站姿、沒有吉他、周圍有散落的花瓣特效。

## Goals / Non-Goals

**Goals:**

- 一張圖加一份 `parts.json`，就能用一個指令產出分層 PNG、Spine JSON、驗證報告與預覽。
- 同一套程式處理部件組成不同的角色，沒有任何寫死的角色座標。
- 每一步的輸出都落在工作目錄的檔案裡，可以從任何一步接續重跑。
- 做不到的事（AI 補圖、試用版存檔）明確標示，不用假資料充數。

**Non-Goals:**

- Mesh、IK、物理、表情切換、非人形骨架。
- 自動辨識部件的電腦視覺模型。
- 圖形化的修補介面：人工修補在使用者自己的繪圖軟體進行，用 `--replace` 匯回。

## Decisions

### 1. 語意分析與資料處理分離，`parts.json` 是唯一介面

Agent 看圖後寫 `parts.json`，Python 只讀它。

```json
{
  "version": 1,
  "image": "character.png",
  "preset": "humanoid-chibi",
  "parts": [
    {
      "name": "arm_l",
      "polygon": [[120, 400], [180, 395], [200, 520], [130, 530]],
      "z": 7,
      "pivot": [170, 410],
      "parent": "body",
      "role": "arm",
      "motion": 0.2
    },
    {"name": "guitar", "mask": "masks/guitar.png", "z": 6, "parent": "body", "role": "prop"}
  ]
}
```

- 座標是原圖像素，左上為原點。`polygon` 或 `mask`（與原圖同尺寸的灰階圖）擇一，範圍要包含被別的部件蓋住的部分。
- `z` 越大越前面。`_l`／`_r` 指畫面左右。
- `pivot`、`parent`、`role`、`motion` 都可省略；必要部件的 role 由名稱決定。
- 替代方案：讓 Python 呼叫視覺模型 API。不採用，因為不能要求 API Key。
- 替代方案：純 CV 啟發式切部件。不採用，對這種渲染風格的角色不可靠，而且會變成針對測試圖調參數。

### 2. 工作目錄即狀態

每個角色一個目錄 `output/<圖片檔名>/`，每一步讀前一步的檔案、寫自己的檔案：

| 步驟 | 讀 | 寫 |
|---|---|---|
| analyze | 原圖、`parts.json` | `source_rgba.png`、`analysis.json`、`parts.json`（正規化）或 `parts.template.json` |
| prepare | `source_rgba.png`、`parts.json`、`overrides/` | `layers/*.png`、`metadata.json`、`missing_parts.json`、`repair_tasks.md`、`layer_preview.png` |
| rig | `metadata.json`、`layers/` | `rig.json` |
| animate | `rig.json` | `animations.json` |
| export | `rig.json`、`animations.json`、`layers/` | `spine/character.json`、`spine/images/`、`spine/character.spine`（有完整版時）、`export_report.json` |
| validate | 以上全部 | `validation_report.json` |
| preview | `spine/` | `preview/*.gif` |

沒有資料庫、沒有隱藏狀態。替代方案是把狀態放在記憶體裡的 pipeline 物件，不採用，因為人工修補會中斷流程，必須能隔天接續。

### 3. 切圖：像素歸屬由 z 決定，被遮住的部分分級處理

- 一個像素屬於「範圍涵蓋它、z 最大」的部件。部件範圍內被更高 z 部件蓋住的區域就是「被遮擋區」。
- 被遮擋區用 OpenCV Telea 修補，只拿這個部件自己看得見的像素當來源，避免染到別的部件的顏色。
- 被遮擋面積占部件 35% 以下：狀態 `auto_repaired`。超過：仍然產生填補草稿讓動畫不破洞，但狀態是 `needs_manual`，寫進修補任務，驗證器把 `manual_repairs` 標成 BLOCKED。35% 是起始值，跑過真實角色後再調整並記錄。
- 完全看不見的部件不產生圖層，直接列為人工任務。
- 人工修好的圖放進 `overrides/<name>.png`，之後每次 prepare 都優先使用，重跑不會被覆蓋。
- 骨架原點與角色外框由「所有部件範圍的聯集」決定，不是整張圖的前景，這樣散落的特效不會影響骨架位置。不屬於任何部件的前景像素會被丟棄，比例寫進報告。
- 修補函式放在 `providers`，介面是 `repair(rgb, unknown) -> rgb`。目前只有 OpenCV 一個實作；不預先寫其他 Provider。

### 4. 骨架：位置全部由 metadata 推算

- preset `humanoid-chibi` 定義必要骨頭的父子關係：`root → hip → body → head / arm_l / arm_r`，`hip → leg_l / leg_r`。`hip` 是虛擬骨頭，位置取 `body` 的 pivot。
- 其他部件各自一根骨頭，父骨頭由 `parts.json` 的 `parent` 指定，預設 `body`。
- 關節位置取 `parts.json` 的 `pivot`；沒寫就用 preset 的預設比例（例如頭在圖層下緣中央、手在靠身體側的上緣）。
- 骨頭方向從關節指向圖層重心，在 Spine 裡看起來會順著肢體；附件用反向旋轉抵銷，圖片不會歪。
- 每個部件一個插槽，順序即 z 順序。

### 5. 動畫：模板 × 角色尺寸 × role／motion

- 模板用「相對量」描述：位移是角色高度的比例，旋轉是角度，方向依肢體在身體的哪一側決定。
- 每個部件的 `role` 決定套用哪一組動作：`head`、`body`、`arm`、`leg`、`hair`、`skirt`、`prop`、`accessory`。`motion`（預設 1.0）是幅度係數。
- 主要角色的手臂設 `motion` 約 0.2：手留在吉他上只做小幅撥弦，不會舉手露出沒畫的區域。空手的角色用預設值就會舉手歡呼。
- `hair`、`skirt` 做跟隨主體、時間稍微延後的次要擺動；`prop` 跟著父骨頭並加一點點反向旋轉。
- Idle 2.0 秒循環：呼吸、輕微點頭、手臂微擺。Happy 2.4 秒循環：兩次蹲、跳、落地，身體擠壓伸展，頭與手隨節奏擺動。
- 關鍵影格之間用平切線 bezier（緩入緩出），格式是 4.x 的絕對座標，每個 channel 四個數字。
- 替代方案：每幀取樣成密集關鍵影格。不採用，那樣在 Spine 裡無法編輯。

### 6. Spine 匯出與授權狀態

- JSON 只用 4.2 與 4.3 共通的子集。`skeleton.spine` 預設 `4.3.08`，`--spine-version` 可改。
- 尋找 Spine 執行檔的順序：`--spine-exe`、環境變數 `SPINE_EXE`、PATH、預設安裝路徑。
- 找到完整版：執行 `Spine.com -i character.json -o character.spine -r character`，檢查檔案存在且非空；再用 `-e json` 匯出回來，比對骨頭、插槽、動畫名稱。
- 只找到試用版或都沒找到：`spine_import` 為 BLOCKED，附上原因與解除方式。不產生任何假的 `.spine`。
- 「在 Editor 內可編輯」只能由人確認，驗證器固定回報 NOT_TESTED，等使用者實際操作後手動記錄到 `docs/TEST_RESULTS.md`。
- Spine CLI 的包裝程式在這台機器上無法實測。這一段會維持 NOT_TESTED，不用模擬程式的結果當作通過證據。

### 7. 自寫算圖器同時是驗證工具與預覽工具

一個小的骨架求值器讀 Spine JSON、算出某一時間點的畫面。

- 驗證：算出初始姿勢，和「直接把圖層疊起來」比對，差異要低於門檻。這能抓到座標換算、骨頭旋轉、圖層順序的錯誤，不需要 Spine。
- 預覽：輸出 GIF，畫面上與檔名都標示「Python Simulation Preview」。
- 它只支援本專案會輸出的功能（rotate／translate／scale、平切線 bezier），不是通用的 Spine 執行環境。

### 8. 測試策略

- 合成角色：`scripts/make_synthetic.py` 用程式畫出兩個比例不同的 Q 版角色，每個部件的真實範圍已知，其中一個用遮罩、一個用多邊形、一個是不透明背景。回歸測試用它們。
- 真實角色：`人.png` 與 `转场2.png` 各有一份由 Agent 看圖寫成的 `parts.json`，放在 `examples/real/`，跑完整流程並目視檢查 `layer_preview.png` 與預覽 GIF。
- 每個 spec scenario 對應至少一個測試或一份有檔案證據的手動檢查，對照表寫在 `docs/TEST_RESULTS.md`。

### 9. Skill

`skills/character-to-spine/SKILL.md` 是唯一的內容來源，描述流程：看圖 → 寫 `parts.json` → `c2s run` → 看 `layer_preview.png` → 修 `parts.json` 或處理修補任務 → 重跑。`.claude/skills/` 與 `.codex/skills/` 各放一份相同內容的複本（Windows 上符號連結需要額外權限），由一個測試確認三份一致。

### 10. pstack 審查

本 session 可呼叫的 skill 清單裡沒有 `pstack:architect`、`pstack:interrogate`（磁碟上有檔案）。執行階段先試著呼叫；不行就讀取它們的 SKILL.md、派獨立的子代理依其內容審查，審查結果回寫到這份 design 與 tasks。不會因為外掛叫不動而跳過審查。

## 工程審查結果（2026-11-23）

獨立子代理審查（只給程式碼與設計文件）實際執行了座標換算與 JSON 格式，確認正確；另外找到 1 個 Critical、7 個 Major、8 個 Minor 問題。全部已修正並有回歸測試，清單見 `docs/KNOWN_ISSUES.md`「已修正」。對設計的影響：

- 決策 3 補充：`prepare` 每次重算全部部件、只寫入有變的檔案；`--part` 改為強制重寫指定部件（D-20）。
- 決策 7 補充：初始姿勢比對只在前景範圍內計算（D-21）。
- 決策 2 補充：工作目錄內的 `parts.json` 優先於圖片旁的版本；工作目錄存絕對路徑。
- 新增 `grid_overlay.png` 協助 Agent 讀出座標（D-22）。

## 草稿已知問題

寫提案時重讀草稿發現的問題（皆已修正，見上方審查結果）：

- 骨架原點與外框用整張圖的前景計算，散落特效會把它帶偏（違反決策 3）。
- 動畫模板沒有 `role`／`motion`，手臂一律舉高 110°（違反決策 5）。
- 沒有 `hair`、`skirt`、`prop` 的次要動作。
- 預覽沒有「Python Simulation Preview」標示。
- 多邊形完全靠 Agent 目測，沒有任何貼合邊緣的輔助。
- 全部程式從未執行，可能有尚未發現的錯誤。

## Risks / Trade-offs

- [Agent 目測的多邊形不夠準，部件交界切得不好] → `layer_preview.png` 讓 Agent 自己看結果並反覆修正；交界複雜的部件改用外部遮罩；最後手段是人工修圖後 `--replace`。這是整個流程裡品質最不確定的一環，簡報會標為半自動。
- [主要角色被吉他擋住的身體與裙子無法自動補出來] → 吉他掛在身體骨頭下一起動，手臂小幅度擺動，盡量不露出被擋的區域；露出的部分列為人工修補任務。
- [完整版 Spine 匯入時拒絕我們的 JSON] → 授權到位後第一件事就是實測；錯誤訊息會寫進 `spine_import.log`；格式只用官方匯出檔出現過的鍵。在那之前這個風險無法消除。
- [試用版 4.3 與使用者最後取得的授權版本不同] → `--spine-version` 可切換，往返驗證會比對內容。
- [自寫算圖器與 Spine 的實際算圖有差異] → 只把它當成自我檢查與示意，所有輸出都標示來源。
- [35% 的自動修補門檻不適合所有角色] → 是具名常數，跑真實角色後調整並把依據記在 `docs/DECISIONS.md`。

## Open Questions

- 試用版的 Import Data（圖形介面）能不能匯入我們的 JSON 讓使用者目視確認？需要使用者手動操作一次才知道。
- 使用者最後取得的是 Essential 還是 Professional？本 change 不用 Mesh／IK，兩者都夠用。
