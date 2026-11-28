<#
Character-to-Spine 一鍵安裝（Windows PowerShell 5.1 以上，不需要系統管理員權限）。

  powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1              安裝或更新
  powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Uninstall   移除

只寫入三個位置：<SkillRoot>\character-to-spine（Codex）、<ClaudeSkillRoot>\character-to-spine（該資料夾已存在時，Claude Code）、
<RuntimeRoot>（共用執行環境）。不下載或安裝 Spine、Codex，不更改執行原則或任何安全設定。
#>
param(
    [string]$SkillRoot = (Join-Path $HOME '.agents\skills'),
    [string]$ClaudeSkillRoot = (Join-Path $HOME '.claude\skills'),
    [string]$RuntimeRoot = (Join-Path $env:LOCALAPPDATA 'character-to-spine\runtime'),
    [switch]$Uninstall,
    [switch]$SkipRuntime
)

# 被代理工具擷取輸出時統一用 UTF-8，與 c2s 的輸出一致（直接在主控台執行時不動）
if ([Console]::IsOutputRedirected) { [Console]::OutputEncoding = [Text.Encoding]::UTF8 }

$Name = 'character-to-spine'
$Src = $PSScriptRoot

if ($Uninstall) {
    foreach ($p in @((Join-Path $SkillRoot $Name), (Join-Path $ClaudeSkillRoot $Name))) {
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force; Write-Host "已移除 $p" }
    }
    # 只刪自己建立的 .venv，RuntimeRoot 被指到別的資料夾時不會連帶刪掉其他檔案
    $venv = Join-Path $RuntimeRoot '.venv'
    if (Test-Path -LiteralPath $venv) { Remove-Item -LiteralPath $venv -Recurse -Force; Write-Host "已移除 $venv" }
    if ((Test-Path -LiteralPath $RuntimeRoot) -and -not (Get-ChildItem -LiteralPath $RuntimeRoot -Force)) { Remove-Item -LiteralPath $RuntimeRoot }
    Write-Host '移除完成。專案資料夾、圖片與輸出沒有變動。'
    exit 0
}

function Find-Python {
    foreach ($c in 'py -3', 'python') {
        $exe = ($c -split ' ')[0]
        $pre = @($c -split ' ' | Select-Object -Skip 1)
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        $out = & $exe @pre -c "import sys; print(sys.executable if sys.version_info >= (3, 11) else '')"
        if ($LASTEXITCODE -eq 0 -and $out) { return "$($out | Select-Object -Last 1)".Trim() }
    }
    return $null
}

$py = Find-Python
if (-not $py) {
    Write-Host '找不到 Python 3.11 以上。請從 https://www.python.org/downloads/ 安裝（安裝時勾選「Add python.exe to PATH」），再重新執行本指令。'
    exit 1
}
Write-Host "Python：$py"

$targets = @(Join-Path $SkillRoot $Name)
if (Test-Path -LiteralPath $ClaudeSkillRoot -PathType Container) { $targets += Join-Path $ClaudeSkillRoot $Name }
foreach ($t in $targets) {
    # /MIR 讓重複安裝與更新得到和來源相同的內容；不複製開發用的環境與暫存
    $null = robocopy $Src $t /MIR /XD .venv __pycache__ .c2s-runtime /XF .c2s-write-test /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) { Write-Host "複製 Skill 到 $t 失敗（robocopy 結束碼 $LASTEXITCODE）"; exit 1 }
    Write-Host "Skill 已安裝到 $t"
}

if ($SkipRuntime) {
    Write-Host '已略過執行環境（-SkipRuntime）：第一次執行 c2s 時啟動器會自行建立。'
    exit 0
}

$whl = Get-ChildItem -LiteralPath (Join-Path $Src 'core') -Filter *.whl -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if (-not $whl) {
    Write-Host "$Src\core 裡沒有 c2s 的 .whl：Skill 套件不完整，請重新下載解壓後再安裝。"
    exit 1
}
$venv = Join-Path $RuntimeRoot '.venv'
$vpy = Join-Path $venv 'Scripts\python.exe'
$stamp = Join-Path $venv 'c2s-installed.txt'
if ((Test-Path -LiteralPath $vpy) -and (Test-Path -LiteralPath $stamp) -and (Get-Content -Raw -LiteralPath $stamp).Trim() -eq $whl.Name) {
    Write-Host "執行環境已是最新（$($whl.Name)）：$venv"
} else {
    Write-Host "建立執行環境 $venv（約 1～3 分鐘，需要網路下載 numpy、Pillow、OpenCV）"
    & $py -m venv --clear $venv
    if ($LASTEXITCODE) { Write-Host "建立虛擬環境失敗：確認 $RuntimeRoot 可寫入，且沒有其他 c2s 正在執行"; exit 1 }
    & $vpy -m pip install --disable-pip-version-check -q -c (Join-Path $Src 'core\constraints.txt') $whl.FullName
    if ($LASTEXITCODE) {
        Write-Host '釘選版本安裝失敗，改裝與這個 Python 相容的最新版本'
        & $vpy -m pip install --disable-pip-version-check -q $whl.FullName
        if ($LASTEXITCODE) { Write-Host '套件安裝失敗：請確認網路連線（或 pip 的 proxy 設定）後重新執行本指令。'; exit 1 }
    }
    [IO.File]::WriteAllText($stamp, $whl.Name)  # 不帶 BOM：啟動器以 UTF-8 讀取並比對 wheel 檔名
}

$default = Join-Path $env:LOCALAPPDATA 'character-to-spine\runtime'
if ($RuntimeRoot.TrimEnd('\') -ne $default) {
    Write-Host "執行環境不在預設位置：請把使用者環境變數 C2S_RUNTIME 設為 $RuntimeRoot，啟動器才找得到。"
    $env:C2S_RUNTIME = $RuntimeRoot  # 只影響下面這次 doctor
}
Write-Host ''
Write-Host '環境檢查（c2s doctor）：'
& $vpy -m character_to_spine.cli doctor
exit 0
