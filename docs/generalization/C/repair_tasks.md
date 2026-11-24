# 修補任務

由 `c2s prepare` 產生。修完後不需要重新分析，照下方指令接續即可。

## 畫面上看不到的必要部件（可選擇補畫）

parts.json 宣告這些部件在原圖完全看不到，目前沒有骨頭也沒有動畫。要讓它動，畫好後在 parts.json 加上該部件、從 absent 移除，再執行 `c2s run`。

- [ ] `leg_l`
- [ ] `leg_r`

## 需要人工修補的圖層

- [ ] `shadow`：被遮擋面積 82% 超過自動修補上限 35%，目前的填補只是草稿
  - 草稿圖層：`layers/shadow.png`
  - 修好後執行：`c2s prepare --replace shadow=<修好的.png>`（PNG 尺寸要等於整張畫布 500x843，或與草稿圖層相同）
- [ ] `hair_back`：被遮擋面積 90% 超過自動修補上限 35%，目前的填補只是草稿
  - 草稿圖層：`layers/hair_back.png`
  - 修好後執行：`c2s prepare --replace hair_back=<修好的.png>`（PNG 尺寸要等於整張畫布 500x843，或與草稿圖層相同）
- [ ] `body`：自動補圖不可靠（留出驗證誤差 0.1773、被遮輪廓 0.336），動畫中露出 2.1%（happy t=0.6s）
  - 草稿圖層：`layers/body.png`
  - 修好後執行：`c2s prepare --replace body=<修好的.png>`（PNG 尺寸要等於整張畫布 500x843，或與草稿圖層相同）

## 已自動填補（OpenCV 邊緣延伸）

- `staff`：可靠
- `skirt`：可靠
- `head`：**不可靠**（留出誤差 0.2011、被遮輪廓 0.3284），動畫中露出 0.8%（門檻內），建議目視
