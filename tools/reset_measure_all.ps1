<#  AL-SADA post-quota-reset GEO measurement for BOTH entities.
    Scheduled daily at 11:20 Asia/Kuwait — just after the Gemini free-tier quota
    resets at midnight Pacific (10:00 Kuwait in PDT, 11:00 Kuwait in PST), so the
    probe always runs with a fresh quota instead of hitting 429.
    Runs CarbonFlow first, waits, then byfatmalens (staggered so they don't
    collide on the shared Gemini key's per-minute limit). #>
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"; $env:ALSADA_PROBE_DELAY = "6"
Set-Location "C:\Projects\alsada"
$log = "C:\Projects\alsada\reports\reset_measure_all.log"
"==== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') post-quota-reset run ====" | Out-File -FilePath $log -Append -Encoding UTF8

# ---------- 1) CarbonFlow (default dirs) ----------
Remove-Item Env:ALSADA_CONFIG_DIR, Env:ALSADA_DATA_DIR, Env:ALSADA_REPORTS_DIR, Env:ALSADA_GENERATED_DIR, Env:ALSADA_BOOST_URLS -ErrorAction SilentlyContinue
$env:ALSADA_BOOST_HOST = "www.carbonflows.store"
$env:ALSADA_BOOST_INDEXNOW_KEY = "cf3ab927d4e11b2a9f7c85d6e40821fc"
python tools\geo_boost.py *>&1 | Out-File -FilePath $log -Append -Encoding UTF8

Start-Sleep -Seconds 90   # spacing so the byfatmalens probe doesn't collide on RPM

# ---------- 2) byfatmalens (isolated profile dirs) ----------
$env:ALSADA_CONFIG_DIR = "C:\Projects\alsada\profiles\byfatmalens\config"
$env:ALSADA_DATA_DIR = "C:\Projects\alsada\profiles\byfatmalens\data"
$env:ALSADA_REPORTS_DIR = "C:\Projects\alsada\profiles\byfatmalens\reports"
$env:ALSADA_GENERATED_DIR = "C:\Projects\alsada\profiles\byfatmalens\generated"
$env:ALSADA_BOOST_HOST = "byfatmalens.space"
$env:ALSADA_BOOST_INDEXNOW_KEY = "8ca5433a89554140b67d46eb9fc9a8ca"
$env:ALSADA_BOOST_URLS = "https://byfatmalens.space/"
python tools\geo_boost.py *>&1 | Out-File -FilePath $log -Append -Encoding UTF8

exit 0
