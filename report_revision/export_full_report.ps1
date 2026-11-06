param([string]$FileBase = 'Bao_cao_nhom_15_LangGraph_day_du')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$docPath = Join-Path $root ($FileBase + '.docx')
$pdfPath = Join-Path $root ($FileBase + '.pdf')
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $report = $word.Documents.Open($docPath)
    $report.TablesOfContents.Item(1).Update()
    $report.Fields.Update() | Out-Null
    $report.Repaginate()
    $pages = $report.ComputeStatistics(2)
    $report.Save()
    $report.ExportAsFixedFormat($pdfPath, 17)
    $report.Close(0)
    Write-Output "Pages: $pages"
} finally {
    try { $word.Quit() } catch { Write-Output 'Word export completed; application already closed.' }
}
