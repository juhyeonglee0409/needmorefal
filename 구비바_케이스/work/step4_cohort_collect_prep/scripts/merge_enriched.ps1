# 구비바 §4 — 다회차 enrichment 병합
#
# 여러 enrichment 라운드의 CSV를 channelId 기준으로 병합.
# 동일 channelId가 양쪽에 있으면 나중 것(신규)을 우선.

param(
    [Parameter(Mandatory=$true)]
    [string[]]$InputFiles,
    [string]$OutFile = "gubiba_enriched_merged.csv"
)

$allRows = @{}
$header = $null

foreach ($file in $InputFiles) {
    if (-not (Test-Path $file)) {
        Write-Host "[merge] SKIP: $file not found"
        continue
    }
    $csv = Import-Csv $file
    if (-not $header -and $csv.Count -gt 0) {
        $header = ($csv[0].PSObject.Properties | ForEach-Object { $_.Name }) -join ','
    }
    foreach ($row in $csv) {
        $allRows[$row.channelId] = $row
    }
    Write-Host "[merge] $file : $($csv.Count) rows loaded"
}

$merged = @($allRows.Values) | Sort-Object { [int]$_.peak_viewers } -Descending
$merged | Export-Csv -Path $OutFile -NoTypeInformation -Encoding utf8
Write-Host "[merge] Output: $OutFile ($($merged.Count) unique rows)"

# 검증
$platformValues = @()
$csvText = Get-Content -LiteralPath $OutFile -Raw
if ($csvText -match '"naverchzzk"') { $platformValues += 'naverchzzk' }
if ($csvText -match '"soop"') { $platformValues += 'soop' }
$platforms = if ($platformValues.Count -gt 0) { $platformValues -join ', ' } else { '(none)' }
$peaks = @($merged | ForEach-Object { $_.PSObject.Properties['peak_viewers'].Value } | Where-Object { $_ -match '^\d+$' } | ForEach-Object { [int]$_ })
$peakStats = $peaks | Measure-Object -Minimum -Maximum
$ggCounts = @{}
foreach ($row in $merged) {
    $gg = [string]$row.PSObject.Properties['is_general_game'].Value
    if (-not $gg) { $gg = '(blank)' }
    if (-not $ggCounts.ContainsKey($gg)) { $ggCounts[$gg] = 0 }
    $ggCounts[$gg]++
}
$ggDist = @($ggCounts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" })
Write-Host "[verify] Platforms: $platforms"
Write-Host "[verify] Peak range: $($peakStats.Minimum)-$($peakStats.Maximum)"
Write-Host "[verify] is_general_game: $($ggDist -join ', ')"
