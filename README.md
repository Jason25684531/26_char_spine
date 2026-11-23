# Character-to-Spine AI

把一張 2D 角色圖片（PNG／JPG）做成可在 Spine 內編輯的骨架動畫：透明分層 PNG、骨架、Idle 與 Happy 動畫、Spine JSON，並在有完整版 Spine 時匯入成 `.spine` 專案。

提供兩個入口，共用同一套 Python 核心：
- **CLI**：`c2s`。
- **Skill**：Claude Code 與 Codex 共用的 `character-to-spine`，Agent 看圖寫出部件描述，再呼叫 `c2s`。

## 安裝

```powershell
uv venv .venv --python 3.11
.venv\Scripts\python.exe -m ensurepip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\c2s.exe --version
```

### 安裝 Skill

正本在 `skills/character-to-spine/SKILL.md`。複製到 Agent 會讀取的位置：

```powershell
foreach ($d in ".claude\skills\character-to-spine", ".codex\skills\character-to-spine") {
  New-Item -ItemType Directory -Force $d | Out-Null
  Copy-Item skills\character-to-spine\SKILL.md $d\
}
```

### 完整版 Spine（選用）

建立 `.spine` 需要 Spine Essential 或 Professional。設定 `SPINE_EXE` 指向 `Spine.com`，或在 `c2s export` 加上 `--spine-exe`。只有試用版或沒有安裝時，匯入步驟會標示為 BLOCKED，其餘步驟照常執行。

## 使用

```powershell
# 1. 分析：沒有 parts.json 時結束碼 2，並輸出範本與座標格線圖
c2s analyze character.png

# 2. 看 output\character\grid_overlay.png，寫 output\character\parts.json（格式見 Skill）

# 3. 一次跑完
c2s run character.png --motion happy
```

也可以分步執行，後面的指令會接續同一個工作目錄：

```powershell
c2s analyze character.png
c2s prepare
c2s rig --preset humanoid-chibi
c2s animate --motion happy
c2s export --format spine
c2s validate
c2s preview
```

人工修補某個部件後匯回：

```powershell
c2s prepare --replace arm_l=fixed_arm.png
```

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
| `preview/*_python_simulation_preview.gif` | 用 Python 模擬的動畫預覽，**不是** Spine 算圖 |

## 限制

- 部件辨識靠 Agent 看圖，Python 本身不做語意辨識；邊界不準時要修正 `parts.json` 或改用遮罩。
- 被遮擋的區域只做 OpenCV 邊緣延伸，大面積遮擋會列為人工修補任務。不使用任何 AI 補圖。
- 第一版只支援人形／Q 版骨架；沒有 Mesh、IK、物理、表情切換。
- 沒有完整版 Spine 時，`.spine` 的建立與 Editor 內可編輯性都無法驗證。

## 開發

```powershell
.venv\Scripts\python.exe -m pytest -q
```

規格：`openspec/changes/character-to-spine-mvp/`。狀態與決策：`docs/`。
