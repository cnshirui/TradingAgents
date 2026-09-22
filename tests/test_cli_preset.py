from datetime import date

import pytest

from cli.models import AnalystType
from cli.utils import read_analysis_preset


def test_read_analysis_preset_maps_interactive_choices(tmp_path):
    preset_file = tmp_path / "MU.txt"
    preset_file.write_text(
        "\n".join(
            [
                "symbol=MU",
                "date=0",
                "lang=Chinese",
                "analysts=all",
                "depth=Deep",
                "quickLLM=qwen2.5:7b",
                "deepLLM=deepseek-r1:14b",
            ]
        ),
        encoding="utf-8",
    )

    preset = read_analysis_preset(preset_file, today=date(2026, 6, 25))

    assert preset.symbol == "MU"
    assert preset.analysis_date == "2026-06-25"
    assert preset.output_language == "Chinese"
    assert preset.analysts == [
        AnalystType.MARKET,
        AnalystType.SOCIAL,
        AnalystType.NEWS,
        AnalystType.FUNDAMENTALS,
    ]
    assert preset.research_depth == 5
    assert preset.quick_llm == "qwen2.5:7b"
    assert preset.deep_llm == "deepseek-r1:14b"


def test_read_analysis_preset_supports_yesterday_and_us_date(tmp_path):
    yesterday = tmp_path / "yesterday.txt"
    yesterday.write_text(
        "symbol=SPY\ndate=-1\nlang=English\nanalysts=market,news\n"
        "depth=Medium\nquickLLM=fast\ndeepLLM=slow\n",
        encoding="utf-8",
    )
    explicit = tmp_path / "explicit.txt"
    explicit.write_text(
        "symbol=SPY\ndate=06/24/2026\nlang=English\nanalysts=market\n"
        "depth=1\nquickLLM=fast\ndeepLLM=slow\n",
        encoding="utf-8",
    )

    assert (
        read_analysis_preset(yesterday, today=date(2026, 6, 25)).analysis_date
        == "2026-06-24"
    )
    assert (
        read_analysis_preset(explicit, today=date(2026, 6, 25)).analysis_date
        == "2026-06-24"
    )


def test_read_analysis_preset_rejects_unknown_keys(tmp_path):
    preset_file = tmp_path / "bad.txt"
    preset_file.write_text(
        "symbol=SPY\ndate=0\nlang=English\nanalysts=all\n"
        "depth=Deep\nquickLLM=fast\ndeepLLM=slow\nsurprise=true\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unknown preset key"):
        read_analysis_preset(preset_file, today=date(2026, 6, 25))


def test_read_analysis_preset_rejects_future_date(tmp_path):
    preset_file = tmp_path / "future.txt"
    preset_file.write_text(
        "symbol=SPY\ndate=1\nlang=English\nanalysts=all\n"
        "depth=Deep\nquickLLM=fast\ndeepLLM=slow\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="future"):
        read_analysis_preset(preset_file, today=date(2026, 6, 25))


def test_bare_preset_path_runs_an_analysis(monkeypatch, tmp_path):
    """``tradingagents stocks/google/MU.txt`` must keep working now that the app
    is a command group with a ``backtest`` subcommand."""
    from typer.testing import CliRunner

    import cli.main as m

    calls = []
    monkeypatch.setattr(m, "run_analysis", lambda **kw: calls.append(kw))
    preset = tmp_path / "MU.txt"
    preset.write_text("symbol=MU\n", encoding="utf-8")

    result = CliRunner().invoke(m.app, [str(preset)])

    assert result.exit_code == 0, result.output
    assert calls == [{"checkpoint": None, "portfolio": None, "preset_file": preset}]


def test_unknown_command_is_still_reported(monkeypatch):
    from typer.testing import CliRunner

    import cli.main as m

    monkeypatch.setattr(m, "run_analysis", lambda **kw: None)
    result = CliRunner().invoke(m.app, ["frobnicate"])

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_group_options_reach_a_bare_preset_run(monkeypatch, tmp_path):
    from typer.testing import CliRunner

    import cli.main as m

    calls = []
    monkeypatch.setattr(m, "run_analysis", lambda **kw: calls.append(kw))
    preset = tmp_path / "MU.txt"
    preset.write_text("symbol=MU\n", encoding="utf-8")

    result = CliRunner().invoke(m.app, ["--checkpoint", str(preset)])

    assert result.exit_code == 0, result.output
    assert calls[0]["checkpoint"] is True
    assert calls[0]["preset_file"] == preset
