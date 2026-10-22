#!/usr/bin/env bash
# 분석보고서.html → ../이태희_분석보고서.pdf
# 필요: Chromium, 같은 폴더에 NotoSansKR.ttf
#   curl -L -o NotoSansKR.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"
set -e
cd "$(dirname "$0")"
CHROME=${CHROME:-$(command -v chromium || command -v google-chrome || ls /opt/pw-browsers/chromium-*/chrome-linux/chrome | head -1)}
"$CHROME" --headless --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf="../이태희_분석보고서.pdf" "file://$PWD/분석보고서.html"
