"""Tests for the CLI interface."""

from click.testing import CliRunner

from cli_timer.main import cli


class TestCLI:
    """Tests for click CLI commands."""

    def test_help_shows_description(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Pomodoro" in result.output

    def test_config_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "25 minutes" in result.output
        assert "5 minutes" in result.output
        assert "15 minutes" in result.output

    def test_start_invalid_work_minutes(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["start", "--work", "0"])
        assert result.exit_code == 1
