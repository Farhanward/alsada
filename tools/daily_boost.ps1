<#  AL-SADA daily reputation booster wrapper (scheduled 09:00 and 21:00).
    Real GEO actions each run: IndexNow + generate assets + radar + measure. #>
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"
Set-Location "C:\Projects\alsada"
$log = "C:\Projects\alsada\reports\daily_boost.log"
"==== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') run ====" | Out-File -FilePath $log -Append -Encoding UTF8
python "C:\Projects\alsada\tools\daily_boost.py" *>&1 | Out-File -FilePath $log -Append -Encoding UTF8
exit $LASTEXITCODE
