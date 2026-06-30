# 구비바 §4 — CLI Companion: Downloads → Codex_Workspace
#
# 브라우저 Blob download가 Downloads 폴더에 떨어진 후 실행.
# 단일 파일(*_full.csv) 또는 청크(*_chunk_*.csv)를
# Codex_Workspace 내 프로젝트 경로로 이동 + 검증.
#
# v3: downloadPrefix가 동적 (gubiba_30d | gubiba_20240101_20260615 등)

param(
    [string]$DownloadsDir = "$env:USERPROFILE\Downloads",
    [string]$TargetDir = "D:\Codex_Workspace\Streamer Consulting Project\구비바_CASE_PACKAGE_v3_20260611\data\cohort\collected",
    [string]$Prefix = "gubiba_*"
)

# 대상 디렉토리 생성
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    Write-Host "[pickup] Created: $TargetDir"
}

# 파일 탐색 (다운로드 확인 팝업 대기: 최대 3회 × 30초)
$maxAttempts = 3
$waitSec = 30
$fullFile = $null
$chunkFiles = $null

for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    $fullFile = Get-ChildItem "$DownloadsDir\${Prefix}_full.csv" -ErrorAction SilentlyContinue
    $chunkFiles = Get-ChildItem "$DownloadsDir\${Prefix}_chunk_*.csv" -ErrorAction SilentlyContinue | Sort-Object Name
    if ($fullFile -or ($chunkFiles -and $chunkFiles.Count -gt 0)) {
        break
    }
    if ($attempt -lt $maxAttempts) {
        Write-Host "[pickup] Attempt $attempt/$maxAttempts : no files yet (prefix=$Prefix). Waiting ${waitSec}s..."
        Start-Sleep -Seconds $waitSec
    }
}

if ($fullFile) {
    Write-Host "[pickup] Found: $($fullFile.Name) ($([math]::Round($fullFile.Length/1024, 1))KB)"
    Copy-Item $fullFile.FullName "$TargetDir\$($fullFile.Name)"
    Write-Host "[pickup] Copied to: $TargetDir\$($fullFile.Name)"

    # 기본 검증
    $csv = Import-Csv "$TargetDir\$($fullFile.Name)"
    Write-Host "[verify] Rows: $($csv.Count)"
    Write-Host "[verify] Platforms: $(($csv | Select-Object -ExpandProperty platform -Unique) -join ', ')"
    $peaks = $csv | ForEach-Object { [int]$_.peak_viewers }
    Write-Host "[verify] Peak range: $($peaks | Measure-Object -Minimum | Select-Object -ExpandProperty Minimum)-$($peaks | Measure-Object -Maximum | Select-Object -ExpandProperty Maximum)"
    $ggDist = $csv | Group-Object is_general_game | ForEach-Object { "$($_.Name)=$($_.Count)" }
    Write-Host "[verify] is_general_game: $($ggDist -join ', ')"
    $dupes = ($csv | Group-Object channelId | Where-Object { $_.Count -gt 1 }).Count
    Write-Host "[verify] Duplicate channelIds: $dupes"

} elseif ($chunkFiles -and $chunkFiles.Count -gt 0) {
    Write-Host "[pickup] Found $($chunkFiles.Count) chunks"

    # 청크 병합
    $merged = @()
    $header = $null
    foreach ($chunk in $chunkFiles) {
        $lines = Get-Content $chunk.FullName -Encoding utf8
        if (-not $header -and $lines.Count -gt 0 -and $lines[0] -match '^name,') {
            $header = $lines[0]
            $merged += $lines
        } else {
            # 헤더 행 건너뛰기 (첫 청크 이후)
            $dataLines = $lines | Where-Object { $_ -notmatch '^name,' }
            $merged += $dataLines
        }
        Write-Host "[pickup] $($chunk.Name): $($lines.Count) lines"
        Copy-Item $chunk.FullName "$TargetDir\$($chunk.Name)"
    }

    # 병합 파일 저장 — prefix 기반 이름
    $mergedName = ($chunkFiles[0].Name -replace '_chunk_\d+', '_merged')
    $mergedPath = "$TargetDir\$mergedName"
    $merged | Out-File -FilePath $mergedPath -Encoding utf8
    Write-Host "[pickup] Merged: $mergedPath ($($merged.Count) lines)"

    # 검증
    $csv = Import-Csv $mergedPath
    Write-Host "[verify] Rows: $($csv.Count)"
    $dupes = ($csv | Group-Object channelId | Where-Object { $_.Count -gt 1 }).Count
    Write-Host "[verify] Duplicate channelIds: $dupes"

} else {
    Write-Host "[pickup] No files found in $DownloadsDir matching ${Prefix}_full.csv or ${Prefix}_chunk_*.csv"
    Write-Host "[pickup] Usage: .\pickup_downloads.ps1 -Prefix 'gubiba_20240101_20260615'"
    Write-Host "[pickup]        .\pickup_downloads.ps1                 # default: gubiba_*"
    exit 1
}

Write-Host ""
Write-Host "[done] Files in $TargetDir :"
Get-ChildItem "$TargetDir\${Prefix}*" | ForEach-Object { Write-Host "  $($_.Name) ($([math]::Round($_.Length/1024, 1))KB)" }
