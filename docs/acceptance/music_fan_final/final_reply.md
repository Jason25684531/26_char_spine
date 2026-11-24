`music_fan.png` 的拆圖、骨架和 Idle／Happy 動畫都做出來了，Spine JSON 和預覽動畫可以用。但還不算全部完成：有 3 個部件要人工補畫，`.spine` 專案也做不出來，因為這台電腦上只有 Spine 試用版。

## 各項驗證狀態（`validation_report.json`）

| 項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 9 根骨頭，上下層級正確 |
| slots | PASS | 7 個插槽都對應到骨頭和圖片 |
| image_references | PASS | 所有圖層圖片都在，尺寸正確 |
| animations | PASS | Idle 2.0 秒；Happy 2.4 秒 |
| setup_pose | PASS | 初始姿勢跟原圖幾乎一樣（差異 0.0007） |
| animation_quality | PASS | 每一格都在門檻內（用第 3 輪自動修正的結果）；橫幅有少量自動補圖露出（0.7%） |
| manual_repairs | **BLOCKED** | body、leg_l、leg_r 要人工補畫 |
| spine_import | **BLOCKED** | 試用版不能存檔或匯出，所以沒有 `.spine` 專案 |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine`，無法測試匯入再匯出 |
| spine_editable | NOT_TESTED | 要在 Spine 裡實際打開才能確認能不能編輯 |

## 拆圖方式
拆成 7 個部件：頭（含頭髮）、身體、左右腳、雙手，再加一個「Rock 'N Roll Rules!」橫幅（當成兩手一起拿的道具）。橫幅擺動時兩隻手跟著動，關鍵影格裡手和橫幅都沒有分開。背景的音符是特效，沒有放進任何部件。

修了兩輪：
- **第 1 輪：**頭髮頂端和左側、橫幅右下角、右鞋邊緣有像素沒分到部件，另外右手在 Happy 2.2 秒時跟橫幅中間出現縫隙。
- **第 2 輪：**左側頭髮還有一小塊漏掉，補上後重跑，現在沒有遺漏的像素。

## 輸出位置（`output/music_fan/` 底下）
- 分層 PNG：`layers/`
- Spine JSON：`spine/character.json`
- 預覽動畫：`preview/idle_python_simulation_preview.gif`、`preview/happy_python_simulation_preview.gif`（這是 Python Simulation Preview，不是 Spine 算出來的畫面）
- `validation_report.json`、`report/visual_check.png`

## 需要人工補畫的部件
順序照 `report/repair_priority.md`：

1. **leg_l（高）**：被橫幅遮住約 42%，Happy 跳起時最多露出 2.43%。對照圖：`report/repair_leg_l.png`
2. **leg_r（高）**：被遮住約 42%，最多露出 2.37%。對照圖：`report/repair_leg_r.png`
3. **body（中）**：被遮住約 85%，最多露出 0.99%。對照圖：`report/repair_body.png`
4. **banner（中，自動補圖不可靠）**：手後面那一小塊，最多露出 0.73%。對照圖：`report/repair_banner.png`

自動補上的區域在 `repair_masks/`，文字版的待修清單在 `repair_tasks.md`。目前這幾塊都只是自動補的草稿，還沒有修好。

**修好後怎麼匯回：**把畫好的 PNG 給我就行，我會跑 `c2s prepare --replace <部件>=<檔案>` 再重跑 `c2s run`。

## 我看圖發現、自動檢查沒抓到的地方
- **手臂只有手掌在動：**原圖的手臂幾乎都被橫幅擋住，只看得到手掌，所以 `arm_l`／`arm_r` 只有手掌的部分，轉動中心放在手掌下緣，不是肩膀。動畫裡主要是橫幅擺動帶著手，看不到手臂揮動。
- **Happy 是原地跳躍：**是站姿跳躍的模板，這張圖用起來還算合適；只是動作時橫幅會移開，下方的腿和身體露出補圖，所以上面腿的補畫最優先。
- **有完整版 Spine 時：**設定環境變數 `SPINE_EXE` 指向 `Spine.com` 再重跑，就能產生 `.spine` 專案。