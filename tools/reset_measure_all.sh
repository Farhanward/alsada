#!/bin/sh
# AL-SADA post-quota-reset GEO measurement for BOTH entities (server / Alpine).
# Cron: 20 11 * * *  (Asia/Riyadh = just after the Gemini free-tier quota reset).
# Runs CarbonFlow first, waits 90s (RPM spacing), then byfatmalens.
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8 ALSADA_PROBE_DELAY=6
BASE=/opt/carbonflow/alsada
cd "$BASE" || exit 1
LOG="$BASE/reports/reset_measure_all.log"
echo "==== $(date '+%Y-%m-%d %H:%M:%S') post-quota-reset run ====" >> "$LOG"

# 1) CarbonFlow (default dirs)
unset ALSADA_CONFIG_DIR ALSADA_DATA_DIR ALSADA_REPORTS_DIR ALSADA_GENERATED_DIR ALSADA_BOOST_URLS
export ALSADA_BOOST_HOST="www.carbonflows.store"
export ALSADA_BOOST_INDEXNOW_KEY="cf3ab927d4e11b2a9f7c85d6e40821fc"
python3 tools/geo_boost.py >> "$LOG" 2>&1

sleep 90

# 2) byfatmalens (isolated profile dirs)
export ALSADA_CONFIG_DIR="$BASE/profiles/byfatmalens/config"
export ALSADA_DATA_DIR="$BASE/profiles/byfatmalens/data"
export ALSADA_REPORTS_DIR="$BASE/profiles/byfatmalens/reports"
export ALSADA_GENERATED_DIR="$BASE/profiles/byfatmalens/generated"
export ALSADA_BOOST_HOST="byfatmalens.space"
export ALSADA_BOOST_INDEXNOW_KEY="8ca5433a89554140b67d46eb9fc9a8ca"
export ALSADA_BOOST_URLS="https://byfatmalens.space/"
python3 tools/geo_boost.py >> "$LOG" 2>&1
exit 0
