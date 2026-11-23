# 決策紀錄

格式：編號、日期、決策、原因。使用者決策標示「使用者」，其餘為 Agent 自行決定的技術決策。

## 使用者決策（Grill Me，2026-11-23）

| 編號 | 題目 | 決策 |
|---|---|---|
| D-01 | Q1 圖片交給 Claude 分析 | 有條件同意。僅限 Claude Code 在本專案內分析使用者有權使用及傳送的素材；不得上傳到其他第三方服務、公開平台或未授權的儲存位置。 |
| D-02 | Q2 analyze 職責切分 | 同意。Skill（Agent）負責語意分析並寫出 `parts.json`；Python Core 只做資料處理。`parts.json` 是 Claude／Codex／CLI 共用的交換格式。 |
| D-03 | Q3 本地模型 | 選 (a)。第一階段不安裝任何本地 AI 模型，用 Python、OpenCV 與外部遮罩匯入。保留 Provider 介面，但不預先開發用不到的功能。 |
| D-04 | Q4 遮擋修補 | (b)+(a)。簡單缺口、小面積由 Python 自動處理；大範圍遮擋或無法可靠修復的區域產生修補任務與可編輯素材，交人工精修。不正確的自動補圖不得視為完成。 |
| D-05 | Q5 合成測試角色 | 同意用於單元測試、骨架驗證、回歸測試。但通用性驗收仍需至少兩種不同的真實角色素材，合成角色不能取代。 |
| D-06 | Q6 Spine 授權 | (a)+(c)。正式交付以 Essential／Professional 授權為目標；授權到位前繼續所有不依賴正式版的開發與測試，需要授權的項目標 BLOCKED。Agent 不得自行購買授權。 |
| D-07 | Q7 真實素材 | 有條件授權。`src/` 下四張圖可用於本專案的角色分析、拆圖規劃與動畫參考，不得另外上傳。由 Agent 選定主要角色並記錄原因（見 D-13）。不同姿勢的圖不得當成同一骨架的連續影格。 |
| D-08 | Q8 草稿與 .gitignore | 保留程式草稿，但全部視為未驗證初稿，先經 pstack／OpenSpec 審查架構，再逐步測試修正。`.gitignore` 保留合理規則，不可把必要的測試圖片、素材或 OpenSpec 文件排除。 |
| D-09 | Q9 Spine 版本 | 預設 4.3，支援 `--spine-version`。實際版本以正式授權環境為準，並保留版本相容性驗證。 |
| D-10 | Q10 部件粒度 | 6 個基本部件是最低要求，不是上限。吉他、頭髮、裙擺、配件等會影響動畫品質的元素要依需求增加部件與骨頭。Happy 動畫的自然度與可編輯性優先。 |
| D-11 | Q11 預覽 | 授權到位前可用 Python 產生 GIF，必須標示「Python Simulation Preview」，不可當成 Spine 算圖或匯出驗證。授權到位後補做實際匯入與動畫驗收。 |
| D-12 | 流程 | 先提案、使用者確認後才執行。之後除授權、付費、未同意的資料外傳、重大不可逆操作外，技術決策由 Agent 自行處理並記錄於此。 |

## Agent 技術決策

| 編號 | 日期 | 決策 | 原因 |
|---|---|---|---|
| D-13 | 2026-11-23 | 主要角色用 `人.png`；`转场2.png` 作為第二組真實角色（通用性驗收）；`人物 拷贝.png`、`预中奖.png` 只當姿勢與動作參考。 | `人.png` 是四張裡唯一的正面圖，左右對稱、角色佔滿畫面（630×887）、沒有散落的花瓣特效，最適合建立骨架。`转场2.png` 是站姿、沒有吉他、手勢不同，部件組成與主要角色不同，能真正考驗通用性。另外兩張是跑步與拋花的 3/4 側面動態姿勢，肢體重疊多，不適合當骨架基礎。 |
| D-14 | 2026-11-23 | 一個 OpenSpec change（`character-to-spine-mvp`）內含 7 個 capability spec，而不是 7 個獨立 change。 | 七個功能共用同一套資料格式與流程，拆成七個 change 會有七份重複的 design 與互相依賴的 tasks。capability 名稱沿用原本建議的七個名字，之後要拆開也容易。 |
| D-15 | 2026-11-23 | Spine JSON 只使用官方 4.2 與 4.3 spineboy 匯出檔中結構相同的子集：bones、slots、region attachment、rotate／translate／scale timeline、絕對座標 bezier。 | 官方 JSON 文件頁停在 3.8 格式（rotate 用 `angle`），不能當 4.x 依據。實際比對 4.2.22 與 4.3.75-beta 匯出檔：rotate 用 `value`，curve 每個 channel 四個數字 `[t1, v1, t2, v2]`，兩版一致。 |
| D-16 | 2026-11-23 | 改寫 `.gitignore`。追蹤 `openspec/`、`docs/`、`examples/`（含真實素材）、`skills/`、`src/`、`tests/`；忽略 `output/`、交付打包目錄、虛擬環境、快取、工具資料庫，以及 `src/*.png`（原始檔留在原地，另複製到 `examples/real/` 追蹤）。 | 舊檔來自其他專案，會忽略 `openspec/*` 與 `docs/*`。真實素材已獲授權在專案內使用，測試需要它們才能重現；repo 只在本機，不推送到公開遠端。 |
| D-17 | 2026-11-23 | `_l`／`_r` 一律指畫面左／右，不是角色自己的左右。 | 寫 `parts.json` 的人（或 Agent）是看著圖片標的，用畫面方向不會搞混。 |
| D-18 | 2026-11-23 | 動畫幅度由每個部件的 `role` 與 `motion` 係數決定，不寫死在模板裡。 | 主要角色雙手抱著吉他，手臂如果照一般模板舉高 110°，手會離開吉他並露出沒畫的部分。同一份模板要能適用「空手」與「持物」的角色。 |

| D-19 | 2026-11-23 | 合成角色產生器放在 `tests/synthetic.py`（測試直接 import，也可當腳本執行），不另開 `scripts/make_synthetic.py`。 | 只有測試用到它，少一個檔案、少一層 import 路徑處理。 |
| D-20 | 2026-11-23 | `prepare` 每次都重算全部部件，只寫入內容有變的圖層檔；`--part` 是「強制重寫這個部件」。 | 部件之間的遮擋互相影響，只重算一個部件會留下過期的結果（獨立審查實測）。全部重算在角色大小的圖上只需數秒。 |
| D-21 | 2026-11-23 | `setup_pose` 與 `recompose_mae` 只在前景範圍內計算差異，門檻 0.02。 | 原本整張畫布平均，白底把差異稀釋到連旋轉全部反向都能通過（獨立審查實測 0.019）。 |
| D-22 | 2026-11-23 | `c2s analyze` 額外輸出 `grid_overlay.png`（每 50 像素一條標了座標的格線）。 | 部件多邊形由 Agent 看圖估計，沒有座標參考時誤差大；這是拆圖品質最大的風險（design 風險第 1 項）。 |
| D-23 | 2026-11-23 | 預覽 GIF 以角色外框為範圍、縮到最長邊 480 像素。 | 原本以整張畫布全尺寸算圖，大圖角色的 48 幀約需 0.5～1 GB 記憶體（獨立審查估算）。預覽只用來看動作。 |
| D-24 | 2026-11-23 | pstack 審查改由獨立子代理進行。 | `pstack:tdd`、`poteto-mode` 等 skill 設定為只能由使用者親自輸入，Agent 呼叫被拒，且被要求不要模仿其流程。 |
| D-25 | 2026-11-23 | 驗證器只強制要求 `idle`；`happy` 存在時檢查至少 2 秒。`animations.json` 每次從頭重建。 | `--motion idle` 原本必定驗證失敗；合併舊檔會殘留以舊骨架算出的動畫。交付時一律用 `--motion happy`，兩個動畫都會產生。 |

| D-26 | 2026-11-23 | `skeleton.spine` 預設 `4.3.26`。 | 原本的 `4.3.08` 是 Launcher 版本；試用版實際下載的 Editor 是 4.3.26（`~/SpineTrial/updates/4.3.26`）。正式授權環境用 `--spine-version` 配合實際 Editor。 |
| D-27 | 2026-11-23 | 指定 `--workdir` 時仍在 `./output/.current` 記錄最後使用的工作目錄；spec 文字配合修改。 | 不記錄的話，下一個不帶參數的指令會回到舊目錄（第一次審查的發現）。這是唯一寫在工作目錄外的檔案。 |
| D-28 | 2026-11-23 | `setup_pose` 改為「骨架初始姿勢算圖」對「原圖在部件範圍內的像素」比對。 | 最終驗收審查實測：舊版拿匯出圖片跟自己比，換成純色或翻轉都 PASS。和原圖比可同時抓到座標、順序與圖片內容的錯誤。 |

## 已確認的環境事實

| 項目 | 事實 | 證據 |
|---|---|---|
| Spine | 只有試用版：`C:\Program Files\Spine Trial\SpineTrial.com`，Launcher 4.3.08，下載的 Editor 4.3.26（更新通道 latestbeta） | `--help` 輸出、`~/SpineTrial/updates/`、`version.txt` |
| 試用版 CLI | `--help` 與 `--advanced` 都沒有 `-i/-o/-r/-e`；實際執行匯入指令 120 秒逾時、沒有產生檔案 | 2026-11-23 實測 |
| 試用版限制 | 官方下載頁：試用版不含「saving projects, texture packing, and exporting animation data, images and video」 | esotericsoftware.com/spine-download |
| 完整版 CLI 語法 | 匯入：`Spine -i <json> -o <project.spine> -r [name]`；匯出：`Spine -i <project.spine> -o <dir> -e json`；Windows 用 `Spine.com` | esotericsoftware.com/spine-command-line-interface |
| 工具鏈 | Python 3.11.9、uv 0.11.28、Git 2.52、Node 24.11.1、OpenSpec 1.3.0、Codex CLI 0.170.0、Claude Code 2.1.322 | 子代理調查 |
| Python 套件 | 已有 Pillow 11.0.0、numpy 1.26.4、opencv-python 4.13.0.92、pytest 9.0.2；沒有 python-pptx | 子代理調查 |
| pstack | 0.15.36 已安裝，`architect`、`arena`、`tdd`、`interrogate` 在磁碟上；本 session 的可呼叫 skill 清單裡只有 `pstack:setup-pstack` | 子代理調查、session skill 清單 |
