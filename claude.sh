#!/usr/bin/env bash
# Run a TradingAgents analysis with Claude, or convert a report to PDF.
#
#   ./claude.sh AMD                 # analyze one ticker
#   ./claude.sh AMD NVDA MU         # several, run one after another
#   ./claude.sh MUU_20260922.md     # only convert an existing report to PDF
#   ./claude.sh last                # copy the newest run's report + PDF to the root
#
# After each analysis the complete report (<date>_<TICKER>.md) is copied to
# the project root and a PDF is rendered next to it.
# All analysis settings live below; only the symbol changes per run.
set -euo pipefail

# ---- analysis settings (edit here) ------------------------------------------
DATE="0"                          # 0 = today, -1 = yesterday, or YYYY-MM-DD
LANG_OUT="Chinese"                # report language
ANALYSTS="all"                    # or market,social,news,fundamentals
DEPTH="Deep"                      # Shallow / Medium / Deep, or a round count
PROVIDER="anthropic"
QUICK_LLM="claude-fable-5-2"
DEEP_LLM="claude-fable-5-2"
# -----------------------------------------------------------------------------

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

cd "$(dirname "$0")"

if [ $# -eq 0 ]; then
  echo "usage: $0 TICKER|REPORT.md [...]" >&2
  exit 1
fi

eval "$(conda shell.bash hook)"
conda activate tradingagents

# md_to_pdf FILE.md OUT.pdf
# pandoc turns the markdown into HTML; headless Chrome prints it to PDF.
# The body font is STHeiti on purpose: Chrome cannot embed PingFang SC as a
# real font subset and draws every glyph as a Type3 outline instead, which
# doubles the file size. STHeiti embeds as a normal subset.
md_to_pdf() {
  local md="$1" pdf="$2" base html css
  if [ ! -f "$md" ]; then
    echo "!! not found: $md" >&2
    return 1
  fi
  if ! command -v pandoc >/dev/null || [ ! -x "$CHROME" ]; then
    echo "!! pandoc or Google Chrome missing; cannot make PDF" >&2
    return 1
  fi
  base="$(basename "$md" .md)"
  html="$(mktemp -t "$base.XXXXXX").html"
  css="${html%.html}.css"
  cat > "$css" <<'CSS'
body { font-family: "STHeiti", "Songti SC", "Helvetica Neue", Arial, sans-serif; font-size: 11pt; line-height: 1.5; max-width: 900px; margin: 0 auto; padding: 24px; color: #222; }
h1 { font-size: 20pt; border-bottom: 2px solid #444; padding-bottom: 4px; }
h2 { font-size: 16pt; margin-top: 1.6em; border-bottom: 1px solid #999; }
h3 { font-size: 13pt; margin-top: 1.2em; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 10pt; }
th, td { border: 1px solid #bbb; padding: 4px 8px; text-align: left; vertical-align: top; }
th { background: #eee; }
code { font-family: Menlo, monospace; font-size: 9.5pt; background: #f4f4f4; padding: 0 3px; }
pre { background: #f4f4f4; padding: 8px; overflow-x: auto; white-space: pre-wrap; }
hr { border: 0; border-top: 1px solid #ccc; margin: 1.2em 0; }
blockquote { border-left: 3px solid #ccc; margin: 0; padding-left: 12px; color: #555; }
@page { size: A4; margin: 18mm 15mm; }
CSS
  pandoc -s -f gfm -t html5 --metadata title="$base" -c "$css" "$md" -o "$html"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
    --print-to-pdf="$(cd "$(dirname "$pdf")" && pwd)/$(basename "$pdf")" \
    "file://$html" >/dev/null 2>&1 || true
  rm -f "$html" "$css"
  if [ -s "$pdf" ]; then
    echo "Complete report: $pdf"
  else
    echo "!! PDF export failed for $md" >&2
    return 1
  fi
}

# publish_report [TICKER]
# Copy the newest run's complete report (for TICKER, or any ticker when
# omitted) to the project root and render its PDF. Runs are ordered by the
# timestamp in the directory name, not by mtime.
publish_report() {
  local ticker="${1:-}" dir md base run
  dir="$(ls -d "reports/${ticker}"*_*/ 2>/dev/null | sort -t_ -k2,3 | tail -1)"
  if [ -z "$dir" ]; then
    echo "!! no report directory found for $ticker" >&2
    return
  fi
  run="$(basename "$dir")"
  run="${run%_*}"
  base="${run##*_}_${run%_*}"
  md="$dir$base.md"
  if [ ! -f "$md" ]; then
    md="$(ls "$dir"*_*.md 2>/dev/null | grep -v complete_report | head -1)"
  fi
  if [ -z "$md" ]; then
    echo "!! no complete report found in $dir" >&2
    return
  fi
  cp "$md" "./$base.md"
  echo "Complete report: $base.md"
  md_to_pdf "./$base.md" "./$base.pdf" || true
}

# run_analysis TICKER
run_analysis() {
  local ticker="$1" preset
  preset="$(mktemp -t "tradingagents-$ticker.XXXXXX")"
  cat > "$preset" <<PRESET
symbol=$ticker
date=$DATE
lang=$LANG_OUT
analysts=$ANALYSTS
depth=$DEPTH
provider=$PROVIDER
quickLLM=$QUICK_LLM
deepLLM=$DEEP_LLM
PRESET
  echo "==> $ticker"
  tradingagents "$preset"
  rm -f "$preset"
  publish_report "$ticker"
}

for arg in "$@"; do
  case "$arg" in
    last) publish_report ;;
    *.md) md_to_pdf "$arg" "${arg%.md}.pdf" ;;
    *)    run_analysis "$(echo "$arg" | tr '[:lower:]' '[:upper:]')" ;;
  esac
done
