# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this repo is

A personal fork of [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents),
a multi-agent LLM stock-analysis framework (analysts → bull/bear researchers →
trader → risk team → portfolio manager). The fork adds a **preset-file runner**
so an analysis can be launched non-interactively from a small `key=value` file,
and keeps the generated reports in the repo.

- `origin`   → `cnshirui/TradingAgents` (this fork)
- `upstream` → `TauricResearch/TradingAgents` (currently merged through v0.5.0)

## Git workflow

- **Do not commit or push unless explicitly asked.** Make the change, report it,
  and leave git to the user.
- Merging upstream: `git fetch upstream && git merge upstream/main` on a branch,
  resolve, run tests, then fast-forward `main`. The fork-specific code that
  tends to conflict lives in `cli/main.py` (preset runner, report path) and
  `tradingagents/graph/checkpointer.py` (WAL-tuned SQLite connection).

## Environment

- Conda env: `conda activate tradingagents`
  (interpreter: `/opt/homebrew/Caskroom/miniconda/base/envs/tradingagents/bin/python`).
- The package is installed editable; after a merge that touches
  `pyproject.toml`, re-run `pip install -e .` in that env.
- API keys and `TRADINGAGENTS_*` settings live in `.env` (gitignored). Note that
  `.env` sets `TRADINGAGENTS_LLM_PROVIDER=ollama`, which makes the interactive
  CLI default to Ollama and causes two `tests/test_cli_prefs.py` tests to fail
  when run from the repo root.

## Running an analysis

The everyday entry point is `./gemini.sh`, which runs the Gemini pipeline for
one or more tickers:

```bash
./gemini.sh AMD
./gemini.sh AMD NVDA MU     # sequentially
```

All settings (date, language, analysts, depth, provider, quick/deep model) are
variables at the top of `gemini.sh`; edit them there. The script writes a
temporary `key=value` preset per ticker, activates the `tradingagents` conda
env if needed, and calls `tradingagents <preset>`.

The underlying preset format (`cli/utils.py: read_analysis_preset`) requires
`symbol, date, lang, analysts, depth, quickLLM, deepLLM`; `provider` and
`backend_url` are optional:

```
symbol=MU
date=0                          # 0 = today, -1 = yesterday, or YYYY-MM-DD
lang=Chinese
analysts=all                    # or market,social,news,fundamentals
depth=Deep                      # Shallow / Medium / Deep, or a round count
provider=google                 # inferred from model IDs when omitted
quickLLM=gemini-3.8-flash
deepLLM=gemini-3.1-pro-preview
```

Other ways to invoke the CLI (a preset path is looked up as given, then under
`./stocks/` if that directory exists):

```bash
tradingagents some/preset.txt            # bare path (routed by _PresetAwareGroup)
tradingagents --preset some/preset.txt
tradingagents analyze some/preset.txt
tradingagents                            # interactive prompts
tradingagents backtest MU --start 2026-06-01 --end 2026-08-01 --every 7
```

Group-level options placed before the path (`--checkpoint`, `--portfolio`,
`--clear-checkpoints`) are forwarded to the preset run.

A preset run saves automatically to `./reports/<TICKER>_<YYYYMMDD_HHMMSS>/`
(this fork deliberately keeps reports in the repo; upstream writes under
`~/.tradingagents/logs`). Each report directory has `1_analysts/`,
`2_research/`, `3_trading/`, `4_risk/`, `5_portfolio/` and a combined
`<TICKER>_<date>.md`.

Use exchange suffixes for non-US tickers (`0700.HK`, `600519.SS`) and
`BTC-USD` for crypto.

## Models

Current Gemini lineup in `gemini.sh`: `gemini-3.8-flash` (quick) and
`gemini-3.1-pro-preview` (deep). Check the live list before "upgrading":

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_API_KEY&pageSize=200"
```

The curated menu is in `tradingagents/llm_clients/model_catalog.py`.

## Code layout

- `cli/main.py` — Typer app. Bare command is a callback (`analyze`); `analyze`
  and `backtest` are subcommands. Preset parsing: `cli/utils.py`
  (`read_analysis_preset`, `AnalysisPreset`).
- `tradingagents/graph/` — LangGraph workflow, checkpointing, propagation.
- `tradingagents/agents/` — analyst / researcher / trader / risk / manager nodes.
- `tradingagents/dataflows/` — data vendors (yfinance, Alpha Vantage, SEC EDGAR,
  FRED, Reddit, StockTwits, Polymarket).
- `tradingagents/llm_clients/` — provider clients; Ollama uses
  `OllamaChatOpenAI` (subclass of `LocalCompatibleChatOpenAI`) for clearer
  missing-model errors.
- `tradingagents/reporting.py` — markdown report tree writer.
- `tradingagents/default_config.py` — all config keys and their env overrides.

## Tests

```bash
python -m pytest -q
```

Markers: `unit`, `integration`, `smoke`. Known failures that are **not**
regressions:

- `tests/test_ohlcv_cache_freshness.py` and `tests/test_ohlcv_latest_bar.py`
  (8 tests) are date-sensitive and fail identically on pristine upstream.
- `tests/test_cli_prefs.py` (2 tests) fail only because of the local `.env`
  provider setting; they pass with `.env` moved aside.

Fork-specific tests: `tests/test_cli_preset.py` (preset parsing and CLI
routing), the Gemini-switch case in `tests/test_cli_env_skip.py`, and the
Ollama missing-model case in `tests/test_ollama_base_url.py`.
