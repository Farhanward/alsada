# AL-SADA — scheduled re-measurement (#2 wait for re-crawl, #3 re-measure).
# Probes the AI engines again and compares against the previous run to prove movement.
# Configured to run weekly via Windows Task Scheduler.
$ErrorActionPreference = 'Continue'
$proj = 'C:\Projects\alsada'
$env:PYTHONPATH = $proj

# load local secrets/config (OpenRouter key, base url, model)
$envFile = Join-Path $proj '.env.local'
if (Test-Path $envFile) {
  Get-Content $envFile -Encoding utf8 | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
      [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
  }
}
$model = if ($env:ALSADA_MODEL) { $env:ALSADA_MODEL } else { 'perplexity/sonar' }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force -Path (Join-Path $proj 'reports') | Out-Null
$log = Join-Path $proj ("reports\scheduled_$stamp.log")

"== AL-SADA scheduled re-measure $stamp (model=$model) ==" | Out-File -FilePath $log -Encoding utf8
& python -m alsada.cli run --engine openrouter --model $model 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
& python -m alsada.cli compare 2>&1 | Out-File -FilePath $log -Append -Encoding utf8
"done $stamp" | Out-File -FilePath $log -Append -Encoding utf8
