"""Rich terminal display for the Pomodoro timer."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text

from cli_timer.timer import PomodoroTimer, SessionRecord, SessionType


# Color themes per session type
THEMES = {
    SessionType.WORK: {"color": "red", "emoji": "ð", "label": "WORK"},
    SessionType.SHORT_BREAK: {"color": "green", "emoji": "â", "label": "SHORT BREAK"},
    SessionType.LONG_BREAK: {"color": "blue", "emoji": "ð´", "label": "LONG BREAK"},
}


class TimerDisplay:
    """Rich-based terminal display for the Pomodoro timer.

    Args:
        console: Rich Console instance. Creates one if not provided.
    """

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def show_banner(self) -> None:
        """Display the application banner."""
        banner = Text("ð CLI Timer â Pomodoro Focus Tool", style="bold white")
        self.console.print(Panel(banner, border_style="red", padding=(1, 2)))

    def show_session_start(self, session_type: SessionType, duration_minutes: int) -> None:
        """Display session start information.

        Args:
            session_type: The type of session starting.
            duration_minutes: Duration of the session in minutes.
        """
        theme = THEMES[session_type]
        self.console.print(
            f"\n{theme['emoji']}  Starting [bold {theme['color']}]{theme['label']}[/] "
            f"session â {duration_minutes} minutes\n"
        )

    def show_tick(self, remaining_seconds: int, session_type: SessionType) -> None:
        """Display the current timer state (called each second).

        Args:
            remaining_seconds: Seconds remaining in the session.
            session_type: Current session type.
        """
        theme = THEMES[session_type]
        minutes, seconds = divmod(remaining_seconds, 60)
        self.console.print(
            f"\r  â±  [{theme['color']}]{minutes:02d}:{seconds:02d}[/] remaining",
            end="",
        )

    def show_session_complete(self, record: SessionRecord) -> None:
        """Display session completion message.

        Args:
            record: The completed session record.
        """
        theme = THEMES[record.session_type]
        if record.completed:
            self.console.print(
                f"\n\n  â  [{theme['color']}]{theme['label']}[/] session complete!"
            )
        else:
            self.console.print(
                f"\n\n  â¹  [{theme['color']}]{theme['label']}[/] session cancelled "
                f"after {record.duration_seconds}s"
            )

    def show_stats(self, timer: PomodoroTimer) -> None:
        """Display session statistics in a table.

        Args:
            timer: The PomodoroTimer instance to read stats from.
        """
        stats = timer.get_stats()
        table = Table(title="ð Session Stats", border_style="dim")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white", justify="right")
        table.add_row("Work sessions", str(stats["total_work_sessions"]))
        table.add_row("Break sessions", str(stats["total_break_sessions"]))
        table.add_row("Work time", f"{stats['total_work_minutes']} min")
        table.add_row("Break time", f"{stats['total_break_minutes']} min")
        self.console.print()
        self.console.print(table)

    def show_next_session(self, session_type: SessionType) -> None:
        """Display what the next session will be.

        Args:
            session_type: The next session type.
        """
        theme = THEMES[session_type]
        self.console.print(
            f"\n  Next: {theme['emoji']}  [bold {theme['color']}]{theme['label']}[/]"
        )

    def show_error(self, message: str) -> None:
        """Display an error message.

        Args:
            message: Error text to display.
        """
        self.console.print(f"\n  [bold red]Error:[/] {message}")
