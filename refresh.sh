#!/bin/bash
# EPE Network — refresh site data from downloaded Google Sheets CSVs
#
# USAGE:
#   1. From each Google Sheet: File → Download → CSV  (save anywhere in data/)
#   2. Run this script: ./refresh.sh
#
# The script auto-finds the newest CSV matching "center" and "scholar" in data/,
# rebuilds centers.json and individuals.json, commits, and pushes to GitHub Pages.

set -e
cd "$(dirname "$0")"

echo ""
echo "══════════════════════════════════════════"
echo "  EPE Network — Site Refresh"
echo "══════════════════════════════════════════"

# ── Synthesize JSON from CSV ──────────────────────────────────────────────────
python3 scripts/synthesize.py

# ── Commit and push ───────────────────────────────────────────────────────────
echo ""
echo "Committing data files…"
git add data/centers.json data/individuals.json

if git diff --cached --quiet; then
  echo "No data changes — nothing to commit."
else
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
  git commit -m "data: refresh from form responses ($TIMESTAMP)"
  echo ""
  echo "Pushing to GitHub Pages…"
  git push origin main
  echo ""
  echo "✓ Site will update in ~30 seconds."
  echo "  https://proflouishyman.github.io/epe_network/"
fi

echo ""
