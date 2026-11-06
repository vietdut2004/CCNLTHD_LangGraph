$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'Bao_cao_ca_nhan_LangGraph_Giu_mau_goc'
foreach ($file in (Get-ChildItem -LiteralPath $out -Filter '*.docx')) {
    $wordReports = New-Object -ComObject Word.Application
    $wordReports.Visible = $false
    $wordReports.DisplayAlerts = 0
    try {
        $report = $wordReports.Documents.Open($file.FullName)
        try {
            $report.Fields.Update() | Out-Null
            foreach ($toc in $report.TablesOfContents) { $toc.Update() }
            $report.Repaginate()
            foreach ($toc in $report.TablesOfContents) { $toc.UpdatePageNumbers() }
            $report.Save()
            $pdf = [IO.Path]::ChangeExtension($file.FullName, '.pdf')
            $report.ExportAsFixedFormat($pdf, 17)
            Write-Output ($file.Name + ': ' + $report.ComputeStatistics(2) + ' pages')
        } finally { try { $report.Close(0) } catch {} }
    } finally { try { $wordReports.Quit() } catch {} }
}
