#!/bin/bash
# 포트폴리오(.key·PDF)와 이력서(PDF)를 다시 만든다. macOS 전용 (Keynote, Google Chrome, uv 필요).
# 사용법: ./build.sh            → 둘 다
#         ./build.sh portfolio  → 포트폴리오만
#         ./build.sh resume     → 이력서만
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$(dirname "$HERE")"                       # 결과물은 TechnicalInterview/ 에 저장
KEY="$OUT/2026-11-17-포트폴리오-v6.key"
PPDF="$OUT/2026-11-17-포트폴리오-v6-미리보기.pdf"
RPDF="$OUT/2026-11-09-이력서.pdf"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
WHAT="${1:-all}"

if [[ "$WHAT" == all || "$WHAT" == portfolio ]]; then
  # 사내망 인증서 때문에 --system-certs 필요 (안 되면 --native-tls)
  uv run --system-certs --with python-pptx python "$HERE/build_portfolio.py" "$TMP/portfolio.pptx"
  osascript <<OSA
tell application "Keynote"
  set doc to open POSIX file "$TMP/portfolio.pptx"
  delay 2
  save doc in POSIX file "$KEY"
  export doc to POSIX file "$PPDF" as PDF
  close doc saving no
end tell
OSA
  echo "포트폴리오: $KEY / $PPDF"
fi

if [[ "$WHAT" == all || "$WHAT" == resume ]]; then
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
    --no-pdf-header-footer --print-to-pdf="$RPDF" "file://$HERE/resume.html" 2>/dev/null
  echo "이력서: $RPDF"
fi
