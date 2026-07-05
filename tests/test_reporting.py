"""Report parity: the shared writer produces the report tree for the CLI and the
programmatic API alike (#1037)."""

from types import SimpleNamespace

import pytest

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.reporting import write_report_tree


def _state():
    return {
        "market_report": "MKT",
        "sentiment_report": "SENT",
        "news_report": "NEWS",
        "fundamentals_report": "FUND",
        "investment_debate_state": {
            "bull_history": "BULL",
            "bear_history": "BEAR",
            "judge_decision": "RM PLAN",
        },
        "trader_investment_plan": "TRADE",
        "risk_debate_state": {
            "aggressive_history": "AGG",
            "conservative_history": "CONS",
            "neutral_history": "NEUT",
            "judge_decision": "PM DECISION",
        },
    }


@pytest.mark.unit
def test_write_report_tree_creates_files(tmp_path):
    out = write_report_tree(_state(), "AAPL", tmp_path)
    assert out.name.endswith(".md")
    assert out.name != "complete_report.md"
    assert (tmp_path / "1_analysts" / "market.md").read_text() == "MKT"
    assert (tmp_path / "1_analysts" / "sentiment.md").read_text() == "SENT"
    assert (tmp_path / "1_analysts" / "news.md").read_text() == "NEWS"
    assert (tmp_path / "1_analysts" / "fundamentals.md").read_text() == "FUND"
    assert (tmp_path / "2_research" / "bull.md").read_text() == "BULL"
    assert (tmp_path / "2_research" / "bear.md").read_text() == "BEAR"
    assert (tmp_path / "2_research" / "manager.md").read_text() == "RM PLAN"
    assert (tmp_path / "3_trading" / "trader.md").read_text() == "TRADE"
    assert (tmp_path / "4_risk" / "aggressive.md").read_text() == "AGG"
    assert (tmp_path / "4_risk" / "conservative.md").read_text() == "CONS"
    assert (tmp_path / "4_risk" / "neutral.md").read_text() == "NEUT"
    assert (tmp_path / "5_portfolio" / "decision.md").read_text() == "PM DECISION"
    assert sorted(
        str(path.relative_to(tmp_path))
        for path in tmp_path.rglob("*")
        if path.is_file()
    ) == [
        "1_analysts/fundamentals.md",
        "1_analysts/market.md",
        "1_analysts/news.md",
        "1_analysts/sentiment.md",
        "2_research/bear.md",
        "2_research/bull.md",
        "2_research/manager.md",
        "3_trading/trader.md",
        "4_risk/aggressive.md",
        "4_risk/conservative.md",
        "4_risk/neutral.md",
        "5_portfolio/decision.md",
        out.name,
    ]
    complete = out.read_text()
    assert "Trading Analysis Report: AAPL" in complete
    assert "MKT" in complete and "PM DECISION" in complete


@pytest.mark.unit
def test_write_report_tree_unescapes_markdown_newlines(tmp_path):
    state = _state()
    state["sentiment_report"] = "Line one\\n- bullet\\n\\nLine two"

    out = write_report_tree(state, "AAPL", tmp_path)

    sentiment = (tmp_path / "1_analysts" / "sentiment.md").read_text()
    complete = out.read_text()
    assert sentiment == "Line one\n- bullet\n\nLine two"
    assert "\\n" not in sentiment
    assert "Line one\n- bullet\n\nLine two" in complete


@pytest.mark.unit
def test_save_reports_explicit_path(tmp_path):
    # Unbound: with an explicit save_path, the method doesn't touch self/config.
    out = TradingAgentsGraph.save_reports(None, _state(), "AAPL", save_path=tmp_path)
    assert out.parent == tmp_path
    assert out.name.startswith("AAPL_")
    assert out.suffix == ".md"
    assert out.exists()


@pytest.mark.unit
def test_save_reports_defaults_under_results_dir(tmp_path):
    mock_self = SimpleNamespace(config={"results_dir": str(tmp_path)})
    out = TradingAgentsGraph.save_reports(mock_self, _state(), "AAPL")
    assert out.exists()
    assert out.parent.parent.name == "reports"  # results_dir/reports/AAPL_<stamp>/...
    assert out.parent.name.startswith("AAPL_")
    assert out.name == f"{out.parent.name.rsplit('_', 1)[0]}.md"
