#!/usr/bin/env bash
# Run a TradingAgents analysis with Gemini for one or more tickers.
#
#   ./gemini.sh AMD            # one ticker
#   ./gemini.sh AMD NVDA MU    # several, run one after another
#
# All settings live below; only the symbol changes per run.
# Reports land in ./reports/<TICKER>_<timestamp>/.
set -euo pipefail

# ---- analysis settings (edit here) ------------------------------------------
DATE="0"                          # 0 = today, -1 = yesterday, or YYYY-MM-DD
LANG_OUT="Chinese"                # report language
ANALYSTS="all"                    # or market,social,news,fundamentals
DEPTH="Deep"                      # Shallow / Medium / Deep, or a round count
PROVIDER="google"
QUICK_LLM="gemini-3.8-flash"
DEEP_LLM="gemini-3.1-pro-preview"
# -----------------------------------------------------------------------------

cd "$(dirname "$0")"

if [ $# -eq 0 ]; then
  echo "usage: $0 TICKER [TICKER ...]" >&2
  exit 1
fi

eval "$(conda shell.bash hook)"
conda activate tradingagents

for raw in "$@"; do
  ticker="$(echo "$raw" | tr '[:lower:]' '[:upper:]')"
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
done
