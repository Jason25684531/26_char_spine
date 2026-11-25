# B Skill 實測（自然語言）

同模型、全新的 Claude Code headless session（`claude -p`），不是跨模型驗證。

- 提示：`幫我把這張角色圖做成 Spine 動畫：examples/generalization/B/gen_b.png`
- 結束碼：0
- Skill 工具呼叫 `character-to-spine`：是
- slash command 展開（直接證據）：否
- slash 間接證據（指令可用，且第一個動作就是 c2s analyze）：否
- 觸發後執行 c2s：是（4 次）
- 讀取禁止路徑：0 次
- 工具呼叫次數：{'Bash': 3, 'PowerShell': 2, 'Read': 3, 'Skill': 1}

## c2s 指令

- `.venv\Scripts\c2s.exe analyze examples/generalization/B/gen_b.png; "exit=$LASTEXITCODE"; Get-ChildItem examples/generalization/B`
- `cat > examples/generalization/B/gen_b.parts.json <<'EOF'
{
  "version": 1,
  "preset": "humanoid-chibi",
  "parts": [
    {"name": "leg_l", "z": 0, "pivot": [500, 665], "motion": 0.4,
     "polygon": [[545,650],[430,660],[250,705],[120,790],[45,880],[80,1030],[210,1080],[330,1168],[545,1168]]},
    {"name": "leg_r", "z": 1, "pivot": [560, 665], "motion": 0.4,
     "polygon": [[520,650],[620,650],[690,730],[760,900],[850,1050],[790,1120],[700,1168],[520,1168]]},
    {"name": "body", "z": 2,
     "polygon": [[410,395],[600,395],[690,400],[705,470],[700,550],[640,600],[625,650],[600,675],[500,675],[450,665],[440,600],[420,540],[410,480]]},
    {"name": "hair_l", "z": 3, "parent": "head", "role": "hair", "pivot": [425, 300],
     "polygon": [[285,365],[330,320],[350,215],[405,200],[415,340],[440,395],[458,452],[420,458],[375,440],[350,400],[320,372]]},
    {"name": "hair_r", "z": 4, "parent": "head", "role": "hair", "pivot": [665, 300],
     "polygon": [[650,360],[690,330],[690,230],[750,260],[822,350],[762,372],[752,452],[700,462],[650,458]]},
    {"name": "head", "z": 5, "pivot": [510, 395],
     "polygon": [[400,200],[420,130],[500,92],[600,88],[660,130],[690,200],[690,330],[650,360],[600,390],[570,402],[440,397],[410,340]]},
    {"name": "puzzle_l", "z": 6, "parent": "head", "role": "accessory", "pivot": [430, 190],
     "polygon": [[350,100],[440,105],[445,150],[430,200],[400,215],[352,218]]},
    {"name": "puzzle_r", "z": 7, "parent": "head", "role": "accessory", "pivot": [670, 190],
     "polygon": [[648,70],[730,68],[770,130],[765,190],[720,235],[665,200]]},
    {"name": "arm_l", "z": 8, "pivot": [435, 545],
     "polygon": [[420,520],[458,560],[450,610],[340,675],[300,708],[240,712],[245,682],[330,640],[410,585]]},
    {"name": "arm_r", "z": 9, "pivot": [690, 525],
     "polygon": [[665,530],[705,530],[740,500],[742,452],[770,428],[806,470],[796,512],[745,600],[705,662],[670,640],[664,600]]}
  ]
}
EOF
.venv/Scripts/c2s.exe run examples/generalization/B/gen_b.png --motion happy; echo exit=$?`
- `.venv/Scripts/python.exe -c "
import json,sys
from shapely.geometry import Polygon
p='examples/generalization/B/gen_b.parts.json'
d=json.load(open(p))
for x in d['parts']:
    g=Polygon(x['polygon']).buffer(10,join_style=2,mitre_limit=2)
    x['polygon']=[[round(a),round(b)] for a,b in list(g.exterior.coords)[:-1]]
json.dump(d,open(p,'w'),indent=1)
" && .venv/Scripts/c2s.exe run examples/generalization/B/gen_b.png --motion happy | .venv/Scripts/python.exe -c "
import json,sys
r=json.load(sys.stdin);print(r['status']);print(r['steps']['prepare']['unassigned_ratio'],r['steps']['prepare']['needs_manual']);print(r['steps']['refine']['unresolved'])
for c in r['steps']['validate']['checks']:print(c['check'],c['status'])"`
- `.venv/Scripts/python.exe -c "
import json,math
p='examples/generalization/B/gen_b.parts.json'
d=json.load(open(p))
for x in d['parts']:
    P=x['polygon'];cx=sum(a for a,b in P)/len(P);cy=sum(b for a,b in P)/len(P)
    o=[]
    for a,b in P:
        l=math.hypot(a-cx,b-cy) or 1
        o.append([round(a+(a-cx)/l*10),round(b+(b-cy)/l*10)])
    x['polygon']=o
json.dump(d,open(p,'w'),indent=1)
" && .venv/Scripts/c2s.exe run examples/generalization/B/gen_b.png --motion happy | .venv/Scripts/python.exe -c "
import json,sys
r=json.load(sys.stdin);print(r['status']);print(r['steps']['prepare']['unassigned_ratio'],r['steps']['prepare']['needs_manual']);print(r['steps']['refine']['unresolved'])
for c in r['steps']['validate']['checks']:print(c['check'],c['status'],c['detail'][:150])"`

## 禁止路徑

- 無

## 全部工具呼叫

1. Skill：`{"skill": "character-to-spine", "args": "examples/generalization/B/gen_b.png"}`
2. PowerShell：`{"command": ".venv\\Scripts\\c2s.exe analyze examples/generalization/B/gen_b.png; \"exit=$LASTEXITCODE\"; Get-ChildItem examples/generalization/B", "description": "Run c2s analyze on the image"}`
3. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_b\\grid_overlay.png"}`
4. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_b\\parts.template.json"}`
5. Bash：`{"command": "cat > examples/generalization/B/gen_b.parts.json <<'EOF'\n{\n  \"version\": 1,\n  \"preset\": \"humanoid-chibi\",\n  \"parts\": [\n    {\"name\": \"leg_l\", \"z\": 0, \"pivot\": [500, 665], \"motion\": 0.4,\n     \"polygon\": [[545,650],[430,660],[250,705],[120,790],[45,880],[80,1030],[`
6. Read：`{"file_path": "D:\\01_Project\\26_char_spine\\output\\gen_b\\layer_preview.png"}`
7. PowerShell：`{"command": ".venv\\Scripts\\python.exe scripts/visual_report.py output/gen_b; Get-Content output/gen_b/report/repair_priority.md -TotalCount 40; Get-Content output/gen_b/missing_parts.json -TotalCount 60", "description": "Generate visual report and read repair priorities"}`
8. Bash：`{"command": ".venv/Scripts/python.exe -c \"\nimport json,sys\nfrom shapely.geometry import Polygon\np='examples/generalization/B/gen_b.parts.json'\nd=json.load(open(p))\nfor x in d['parts']:\n    g=Polygon(x['polygon']).buffer(10,join_style=2,mitre_limit=2)\n    x['polygon']=[[round(a),round(b)] for`
9. Bash：`{"command": ".venv/Scripts/python.exe -c \"\nimport json,math\np='examples/generalization/B/gen_b.parts.json'\nd=json.load(open(p))\nfor x in d['parts']:\n    P=x['polygon'];cx=sum(a for a,b in P)/len(P);cy=sum(b for a,b in P)/len(P)\n    o=[]\n    for a,b in P:\n        l=math.hypot(a-cx,b-cy) or 1`

## 最後回覆（原文）

我已經把 `gen_b.png` 跑完 c2s 流程（寫 parts.json、切圖、建骨架、產生 Idle/Happy 動畫、驗證）。結果是 **BLOCKED**，因為還有兩部件要人工修補，而且這台機器沒有可匯出的完整版 Spine。

**驗證結果（`validation_report.json`）**

| 項目 | 狀態 |
|---|---|
| bones、slots、image_references、animations | PASS |
| setup_pose | PASS（和原圖差異 0.0021） |
| animation_quality | PASS（逐格檢查破洞、關節縫隙、接觸分離，都在門檻內） |
| manual_repairs | BLOCKED |
| spine_import | BLOCKED |
| spine_roundtrip、spine_editable | NOT_TESTED |

**待人工處理**
- `leg_l` 和 `body` 被標為 `needs_manual`。這兩部件被遮住的區域是自動補的，動畫中露出太多，自動補的圖不可靠。
- 這兩部件各自的清單和對照圖在 `output/gen_b/report/repair_priority.md` 與 `repair_tasks.md`。
- 修好後用 `c2s prepare --replace <部件>=<修好的.png>`，再跑 `c2s run`。

**Spine 匯入**
- 偵測到的是 Spine 試用版，不能儲存專案或匯出，所以沒有產生 `.spine`。
- 這是 BLOCKED，不是完成。

**部件和切圖調整**
- 我把角色拆成 10 個部件：`head`、`body`、`arm_l`、`arm_r`、`leg_l`、`leg_r`、`hair_l`、`hair_r`、`puzzle_l`、`puzzle_r`。
- 圖上看不到腿，所以 `leg_l`、`leg_r` 是以裙子左右各半代替。
- 第一次切圖有 2.1% 的像素漏在部件外，我把所有多邊形往外擴約 10 像素，降到 0.55%。
- 擴大後我沒有再看一次 `layer_preview.png`，也沒有看新的動畫預覽。

**預覽與檔案**
- 預覽 GIF 是 Python Simulation Preview，不是 Spine 算圖，在 `output/gen_b/preview/`。
- parts.json 在 `examples/generalization/B/gen_b.parts.json`。
- 這次沒有 commit。