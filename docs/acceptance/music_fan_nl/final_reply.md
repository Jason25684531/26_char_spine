## 結果：BLOCKED

所有輸出都產生了，Idle 和 Happy 動畫在品質檢查中也通過。不過整體狀態是 **BLOCKED**，原因有兩個：身體圖層需要人工補畫，以及這台電腦只有 Spine 試用版，無法建立 `.spine` 專案。

### `validation_report.json` 各項狀態
| 檢查項目 | 狀態 | 說明 |
|---|---|---|
| bones | PASS | 9 根骨頭，階層正確 |
| slots | PASS | 7 個插槽都對應到骨頭與圖片 |
| image_references | PASS | 圖片都存在，尺寸正確，不是空白 |
| animations | PASS | idle 2.0 秒、19 個關鍵影格；happy 2.4 秒、83 個關鍵影格 |
| setup_pose | PASS | 骨架初始姿勢與原圖的差異為 0.0015 |
| manual_repairs | **BLOCKED** | `body` 等待人工補畫 |
| animation_quality | PASS | 以 10 fps 逐格檢查，再加上所有關鍵影格，都在門檻內。有少量自動補的區域會露出：leg_l 1.9%、leg_r 2.0%、banner 0.9% |
| spine_import | **BLOCKED** | 偵測到 Spine 試用版，不能儲存或匯出專案，所以無法產生 `.spine` |
| spine_roundtrip | NOT_TESTED | 沒有 `.spine` 可以做往返驗證 |
| spine_editable | NOT_TESTED | 需要在 Spine Editor 裡手動開啟並修改，程式無法代為確認 |

### 輸出位置
以下都在 `output/music_fan/` 底下：
- `layers/`：7 個分層 PNG，包括 head、body、banner（布條）、arm_l、arm_r、leg_l、leg_r
- `spine/character.json`：Spine JSON
- `preview/idle_python_simulation_preview.gif`、`preview/happy_python_simulation_preview.gif`：這是 **Python Simulation Preview**，不是 Spine 算圖
- `validation_report.json`
- `report/visual_check.png`

部件設定存在圖片旁的 `music_fan.parts.json`。

### 拆圖和綁骨架的做法
- 角色用兩手拉著「Rock 'N Roll Rules!」布條，所以布條設成兩手共同拿著的道具。動畫中布條會帶著雙手一起擺動。
- 第一輪檢查發現頭髮左上、布條右下緣、右鞋邊和右手指尖有沒分配到部件的像素，已經擴大多邊形修正。
- 現在沒分配到的像素只有飄在空中的音符，以及布條左緣一條約 33px 的細線。音符是特效，本來就不屬於角色部件。

### 需要人工補畫的部件
依 `report/repair_priority.md` 的順序：

1. **body（中）**：身體約 90% 被頭和布條擋住，目前的填補只是草稿。動畫中最多露出 1.07%（happy t=1.8s）。對照圖：`report/repair_body.png`。
2. 下面三個是自動補的，結果不可靠，建議也一起補：
   - **leg_r（中，露出 2.0%）**：對照圖 `report/repair_leg_r.png`
   - **leg_l（中，露出 1.9%）**：對照圖 `report/repair_leg_l.png`
   - **banner（中，露出 0.9%，被雙手擋住的部分）**：對照圖 `report/repair_banner.png`

自動補上的區域在 `output/music_fan/repair_masks/`，文字版的待修清單在 `output/music_fan/repair_tasks.md`。

### 修好後怎麼匯回
把補好的 PNG 給我就可以。我會執行 `c2s prepare --replace body=<修好的.png>`，再跑一次 `c2s run music_fan.png` 重新產生所有輸出，不需要你自己下指令。

### 自動檢查沒抓到的地方
我看過 `report/visual_check.png`：
- 雙手在 Idle 和 Happy 的每一格都抓著布條，沒有分開。
- 跳起來的時候，頭、身體和腳一起移動，沒有破圖。
- 原圖中手臂幾乎全被布條擋住，只看得到兩隻手掌，所以 `arm_l`、`arm_r` 圖層實際上只有手掌，以肩膀為轉動中心。這個角色看起來沒問題。但如果之後要做把布條放下的動作，就得補畫整隻手臂。