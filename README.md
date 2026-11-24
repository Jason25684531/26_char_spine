# Character-to-Spine AI

把一張 2D 角色圖片（PNG／JPG）做成可在 Spine 內編輯的骨架動畫：透明分層 PNG、骨架、Idle 與 Happy 動畫、Spine JSON，並在有完整版 Spine 時匯入成 `.spine` 專案。

支援範圍是人形／Q 版角色（頭、身體、兩手、兩腳，可拿或抱道具）。

## 新使用者：安裝 Claude Skill

需要：Claude Code、Python 3.11 以上（`python --version` 確認）、第一次使用時可連網（下載 numpy、Pillow、OpenCV）。不需要 API Key 或付費服務。

1. 解壓 `character-to-spine-skill-v1.0.0.zip`，得到 `character-to-spine/` 資料夾。
2. 放到下列其中一處：
   - 只給某個專案用：`<專案>\.claude\skills\character-to-spine\`
   - 所有專案都能用：`%USERPROFILE%\.claude\skills\character-to-spine\`（macOS／Linux：`~/.claude/skills/character-to-spine/`）

   ```powershell
   Expand-Archive character-to-spine-skill-v1.0.0.zip -DestinationPath .claude\skills
   ```
3. 把角色圖片放進專案資料夾，啟動 Claude Code，說一句話即可，例如：

   > 請將 hero.png 拆補圖、建立骨架，製作 Idle／Happy 動畫並輸出結果。

   也可以用 `/character-to-spine hero.png`。

Claude 會自己分析角色、寫部件描述、執行切圖到輸出的全部步驟，最後回報狀態、輸出位置與需要人工補畫的部件。你不需要執行任何 Python 指令。第一次使用時，Skill 會在自己的資料夾建立 `.venv` 安裝執行環境（約 1～3 分鐘），之後不再重裝。解除安裝就是刪掉 `character-to-spine/` 資料夾。

人工補畫好某個部件後，把 PNG 交給 Claude，說「用 fixed_body.png 取代 body」即可匯回並重新產生動畫。

### 完整版 Spine（選用）

建立 `.spine` 需要 Spine Essential 或 Professional。設定環境變數 `SPINE_EXE` 指向 `Spine.com` 後，同樣的流程會一併建立 `.spine` 專案。只有試用版或沒有安裝時，這一項標示為 BLOCKED，其餘輸出照常產生。輸出的 Spine JSON 可以用 Spine Editor 的「匯入資料」開啟。

## 開發者

```powershell
uv venv .venv --python 3.11
.venv\Scripts\python.exe -m ensurepip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest -q            # 回歸測試
.venv\Scripts\python.exe scripts\build_skill.py  # 產生 dist\character-to-spine\ 與 Skill zip
```

Skill 的正本在 `skills/character-to-spine/`（`SKILL.md`、`references/`、啟動器 `scripts/c2s.py`）。`build_skill.py` 把 Python Core 打成 wheel 放進 `core/`，再壓成 zip。在本專案用 Claude Code 測 Skill 時，把 `dist\character-to-spine\` 複製到 `.claude\skills\`。

## CLI 用法（開發與除錯）

```powershell
# 1. 分析：沒有 parts.json 時結束碼 2，並輸出範本與座標格線圖
c2s analyze character.png

# 2. 看 output\character\grid_overlay.png，在圖片旁寫 character.parts.json（格式見 Skill）

# 3. 一次跑完
c2s run character.png --motion happy
```

也可以分步執行，後面的指令會接續同一個工作目錄：

```powershell
c2s analyze character.png
c2s prepare
c2s rig --preset humanoid-chibi
c2s animate --motion happy
c2s refine            # 逐格品質檢查＋自動修正，結束時 export
c2s validate
c2s preview
```

人工修補某個部件後匯回（存到圖片旁的 `character.overrides/`，之後重建都會沿用）：

```powershell
c2s prepare --replace arm_l=fixed_arm.png
```

## 素材與產物

| 位置 | 內容 | 可刪除 |
|---|---|---|
| 圖片旁：`character.png`、`character.parts.json`、遮罩、`character.overrides/` | 永久素材（正式部件描述、人工修補圖） | 否 |
| `output/<圖片檔名>/` | 全部產物 | 可以，`c2s run character.png` 會重建出相同結果 |

結束碼：`0` 完成（各項狀態仍以 `validation_report.json` 為準）、`1` 失敗（看 `c2s_error.log`）、`2` 需要補資料後接續。

## 輸出（`output/<圖片檔名>/`）

| 檔案 | 內容 |
|---|---|
| `layers/*.png`、`metadata.json` | 透明分層 PNG 與每個部件的位置、尺寸、pivot、前後順序 |
| `layer_preview.png` | 原圖、圖層重組、部件標示三欄並排的檢查圖 |
| `missing_parts.json`、`repair_tasks.md` | 缺少的部件與需要人工修補的圖層，附接續指令 |
| `spine/character.json`、`spine/images/` | Spine JSON 與圖片（Spine 4.3 格式，`--spine-version` 可改） |
| `spine/character.spine` | 只有完整版 Spine 可用時才會產生 |
| `validation_report.json` | 每個檢查項目的 PASS／FAIL／BLOCKED／NOT_TESTED |
| `quality/quality_report.json`、`quality/round_N/*.png` | 動畫逐格品質檢查（破洞、關節縫隙、接觸分離、補圖露出）、每輪自動修正的紀錄與異常影格 |
| `tuning.json` | 自動修正後各骨頭的動作幅度係數 |
| `report/`（`python scripts/visual_report.py <工作目錄>`） | 修補優先順序 `repair_priority.md`、每個部件的三格對照圖、視覺驗收總覽 `visual_check.png` |
| `preview/*_python_simulation_preview.gif` | 用 Python 模擬的動畫預覽，**不是** Spine 算圖 |

## 限制

- 部件辨識靠 Agent 看圖，Python 本身不做語意辨識；邊界不準時要修正 `parts.json` 或改用遮罩。
- 被遮擋的區域只做 OpenCV 邊緣延伸，不使用任何 AI 補圖。以下情況列為人工修補任務：
  - 大面積遮擋（超過 35%）。
  - 實測為不可靠（紋理補不回來或輪廓靠猜），而且在動畫中露出的補圖。
- 自動修正只會降低動作幅度，不會修改部件範圍；修不掉的問題會標成 BLOCKED，並附上異常影格。
- 第一版只支援人形／Q 版骨架；沒有 Mesh、IK、物理、表情切換。
- 沒有完整版 Spine 時，`.spine` 的建立與 Editor 內可編輯性都無法驗證。

## 開發

```powershell
.venv\Scripts\python.exe -m pytest -q
```

規格：`openspec/changes/character-to-spine-mvp/`。狀態與決策：`docs/`。
