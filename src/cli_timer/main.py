"""CLI entry point for the Pomodoro timer."""

from __future__ import annotations

import signal
import sys
from typing import Optional

import click
from rich.console import Console

from cli_timer.display import TimerDisplay
from cli_timer.timer import PomodoroTimer, SessionType, TimerConfig


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ð CLI Timer â A Pomodoro focus tool with rich terminal UI.

    Run a Pomodoro work session with `cli-timer start`, or customize
    your timer with `cli-timer start --work 30 --short-break 10`.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option("--work", "-w", default=25, type=int, help="Work session duration in minutes.")
@click.option("--short-break", "-s", default=5, type=int, help="Short break duration in minutes.")
@click.option("--long-break", "-l", default=15, type=int, help="Long break duration in minutes.")
@click.option("--sessions", "-n", default=4, type=int, help="Work sessions before a long break.")
@click.option("--cycles", "-c", default=1, type=int, help="Number of full Pomodoro cycles to run.")
def start(
    work: int,
    short_break: int,
    long_break: int,
    sessions: int,
    cycles: int,
) -> None:
    """Start a Pomodoro timer session.

    Runs work/break cycles according to the Pomodoro Technique.
    Press Ctrl+C to cancel the current session.
    """
    console = Console()
    display = TimerDisplay(console=console)

    try:
        config = TimerConfig(
            work_minutes=work,
            short_break_minutes=short_break,
            long_break_minutes=long_break,
            sessions_before_long_break=sessions,
        )
    except ValueError as e:
        display.show_error(str(e))
        raise SystemExit(1)

    timer = PomodoroTimer(
        config=config,
        on_tick=display.show_tick,
        on_session_complete=display.show_session_complete,
    )

    display.show_banner()

    total_work_sessions = sessions * cycles

    def handle_sigint(sig: int, frame: Optional[object]) -> None:
        timer.cancel()

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        while timer.work_sessions_completed < total_work_sessions:
            session_type = timer.get_next_session_type()
            duration_min = timer.get_duration_seconds(session_type) // 60
            display.show_session_start(session_type, duration_min)

            record = timer.run_session(session_type)

            if not record.completed:
                console.print("\n  Session cancelled by user.")
                break

            display.show_next_session(timer.get_next_session_type())

    except KeyboardInterrupt:
        console.print("\n\n  Goodbye! ð")

    display.show_stats(timer)


@cli.command()
def config() -> None:
    """Show default timer configuration."""
    console = Console()
    default = TimerConfig()
    console.print("\n[bold]Default Configuration:[/]\n")
    console.print(f"  Work session:      {default.work_minutes} minutes")
    console.print(f"  Short break:       {default.short_break_minutes} minutes")
    console.print(f"  Long break:        {default.long_break_minutes} minutes")
    console.print(f"  Sessions per cycle: {default.sessions_before_long_break}")
    console.print()


if __name__ == "__main__":
    cli()
