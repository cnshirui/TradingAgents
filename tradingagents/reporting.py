"""Reusable report-tree writer shared by the CLI and the programmatic API.

Writes a run's per-section markdown (analysts, research, trading, risk,
portfolio) plus a consolidated ``<TICKER>_<YYYYMMDD>.md`` under ``save_path``.
The CLI and ``TradingAgentsGraph.save_reports`` both call this, so a headless /
API run produces the same on-disk report tree a CLI run does.
"""

import re
from datetime import datetime
from pathlib import Path


_RUN_DIR_RE = re.compile(r"^.+_(?P<date>\d{8})_\d{6}$")
_TICKER_PATH_RE = re.compile(r"^[A-Za-z0-9._\-\^=+]+$")


def normalize_markdown_text(text) -> str:
    """Convert escaped line breaks in generated reports back to Markdown lines."""
    if isinstance(text, list):
        text = "\n".join(str(item) for item in text)
    return str(text).replace("\\n", "\n")


def _safe_ticker_component(value: str, *, max_len: int = 32) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"ticker must be a non-empty string, got {value!r}")
    if len(value) > max_len:
        raise ValueError(f"ticker exceeds {max_len} chars: {value!r}")
    if not _TICKER_PATH_RE.fullmatch(value):
        raise ValueError(
            f"ticker contains characters not allowed in a filesystem path: {value!r}"
        )
    if set(value) == {"."}:
        raise ValueError(f"ticker cannot consist solely of dots: {value!r}")
    return value


def complete_report_path(ticker: str, save_path: Path) -> Path:
    """Return the consolidated report path for a run directory."""
    match = _RUN_DIR_RE.match(save_path.name)
    report_date = match.group("date") if match else datetime.now().strftime("%Y%m%d")
    return save_path / f"{_safe_ticker_component(ticker)}_{report_date}.md"


def write_report_tree(final_state: dict, ticker: str, save_path) -> Path:
    """Save a completed run's reports to ``save_path``; return the complete-report path."""
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    sections = []

    # 1. Analysts
    analysts_dir = save_path / "1_analysts"
    analyst_parts = []
    if final_state.get("market_report"):
        market_report = normalize_markdown_text(final_state["market_report"])
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "market.md").write_text(market_report, encoding="utf-8")
        analyst_parts.append(("Market Analyst", market_report))
    if final_state.get("sentiment_report"):
        sentiment_report = normalize_markdown_text(final_state["sentiment_report"])
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "sentiment.md").write_text(sentiment_report, encoding="utf-8")
        analyst_parts.append(("Sentiment Analyst", sentiment_report))
    if final_state.get("news_report"):
        news_report = normalize_markdown_text(final_state["news_report"])
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "news.md").write_text(news_report, encoding="utf-8")
        analyst_parts.append(("News Analyst", news_report))
    if final_state.get("fundamentals_report"):
        fundamentals_report = normalize_markdown_text(final_state["fundamentals_report"])
        analysts_dir.mkdir(exist_ok=True)
        (analysts_dir / "fundamentals.md").write_text(fundamentals_report, encoding="utf-8")
        analyst_parts.append(("Fundamentals Analyst", fundamentals_report))
    if analyst_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in analyst_parts)
        sections.append(f"## I. Analyst Team Reports\n\n{content}")

    # 2. Research
    if final_state.get("investment_debate_state"):
        research_dir = save_path / "2_research"
        debate = final_state["investment_debate_state"]
        research_parts = []
        if debate.get("bull_history"):
            bull_history = normalize_markdown_text(debate["bull_history"])
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bull.md").write_text(bull_history, encoding="utf-8")
            research_parts.append(("Bull Researcher", bull_history))
        if debate.get("bear_history"):
            bear_history = normalize_markdown_text(debate["bear_history"])
            research_dir.mkdir(exist_ok=True)
            (research_dir / "bear.md").write_text(bear_history, encoding="utf-8")
            research_parts.append(("Bear Researcher", bear_history))
        if debate.get("judge_decision"):
            judge_decision = normalize_markdown_text(debate["judge_decision"])
            research_dir.mkdir(exist_ok=True)
            (research_dir / "manager.md").write_text(judge_decision, encoding="utf-8")
            research_parts.append(("Research Manager", judge_decision))
        if research_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in research_parts)
            sections.append(f"## II. Research Team Decision\n\n{content}")

    # 3. Trading
    if final_state.get("trader_investment_plan"):
        trader_investment_plan = normalize_markdown_text(final_state["trader_investment_plan"])
        trading_dir = save_path / "3_trading"
        trading_dir.mkdir(exist_ok=True)
        (trading_dir / "trader.md").write_text(trader_investment_plan, encoding="utf-8")
        sections.append(f"## III. Trading Team Plan\n\n### Trader\n{trader_investment_plan}")

    # 4. Risk Management
    if final_state.get("risk_debate_state"):
        risk_dir = save_path / "4_risk"
        risk = final_state["risk_debate_state"]
        risk_parts = []
        if risk.get("aggressive_history"):
            aggressive_history = normalize_markdown_text(risk["aggressive_history"])
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "aggressive.md").write_text(aggressive_history, encoding="utf-8")
            risk_parts.append(("Aggressive Analyst", aggressive_history))
        if risk.get("conservative_history"):
            conservative_history = normalize_markdown_text(risk["conservative_history"])
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "conservative.md").write_text(conservative_history, encoding="utf-8")
            risk_parts.append(("Conservative Analyst", conservative_history))
        if risk.get("neutral_history"):
            neutral_history = normalize_markdown_text(risk["neutral_history"])
            risk_dir.mkdir(exist_ok=True)
            (risk_dir / "neutral.md").write_text(neutral_history, encoding="utf-8")
            risk_parts.append(("Neutral Analyst", neutral_history))
        if risk_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in risk_parts)
            sections.append(f"## IV. Risk Management Team Decision\n\n{content}")

        # 5. Portfolio Manager
        if risk.get("judge_decision"):
            portfolio_decision = normalize_markdown_text(risk["judge_decision"])
            portfolio_dir = save_path / "5_portfolio"
            portfolio_dir.mkdir(exist_ok=True)
            (portfolio_dir / "decision.md").write_text(portfolio_decision, encoding="utf-8")
            sections.append(f"## V. Portfolio Manager Decision\n\n### Portfolio Manager\n{portfolio_decision}")

    # Write consolidated report
    header = f"# Trading Analysis Report: {ticker}\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report_path = complete_report_path(ticker, save_path)
    report_path.write_text(header + "\n\n".join(sections), encoding="utf-8")
    return report_path
