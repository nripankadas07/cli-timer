"""Core timer engine for the Pomodoro CLI."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class SessionType(Enum):
    """Type of Pomodoro session."""
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


@dataclass
class TimerConfig:
    """Configuration for the Pomodoro timer."""
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4

    def __post_init__(self) -> None:
        if self.work_minutes <= 0:
            raise ValueError("work_minutes must be positive")
        if self.short_break_minutes <= 0:
            raise ValueError("short_break_minutes must be positive")
        if self.long_break_minutes <= 0:
            raise ValueError("long_break_minutes must be positive")
        if self.sessions_before_long_break <= 0:
            raise ValueError("sessions_before_long_break must be positive")


@dataclass
class SessionRecord:
    """Record of a completed Pomodoro session."""
    session_type: SessionType
    duration_seconds: int
    completed: bool
    timestamp: float = field(default_factory=time.time)


class PomodoroTimer:
    """Pomodoro timer engine that manages work/break cycles.

    Args:
        config: Timer configuration. Uses defaults if not provided.
        on_tick: Optional callback invoked each second with (remaining_seconds, session_type).
        on_session_complete: Optional callback invoked when a session finishes.
        time_func: Time function for testing (defaults to time.time).
        sleep_func: Sleep function for testing (defaults to time.sleep).
    """

    def __init__(
        self,
        config: Optional[TimerConfig] = None,
        on_tick: Optional[Callable[[int, SessionType], None]] = None,
        on_session_complete: Optional[Callable[[SessionRecord], None]] = None,
        time_func: Callable[[], float] = time.time,
        sleep_func: Callable[[float], None] = time.sleep,
    ) -> None:
        self.config = config or TimerConfig()
        self.on_tick = on_tick
        self.on_session_complete = on_session_complete
        self._time = time_func
        self._sleep = sleep_func

        self._work_sessions_completed: int = 0
        self._history: list[SessionRecord] = []
        self._running: bool = False
        self._cancelled: bool = False

    @property
    def work_sessions_completed(self) -> int:
        """Number of work sessions completed in the current cycle."""
        return self._work_sessions_completed

    @property
    def history(self) -> list[SessionRecord]:
        """List of all completed session records."""
        return list(self._history)

    @property
    def is_running(self) -> bool:
        """Whether the timer is currently running."""
        return self._running

    def get_next_session_type(self) -> SessionType:
        """Determine the next session type based on completed work sessions."""
        if self._work_sessions_completed == 0 or self._history and self._history[-1].session_type != SessionType.WORK:
            return SessionType.WORK
        if self._work_sessions_completed % self.config.sessions_before_long_break == 0:
            return SessionType.LONG_BREAK
        return SessionType.SHORT_BREAK

    def get_duration_seconds(self, session_type: SessionType) -> int:
        """Get the duration in seconds for a given session type."""
        durations = {
            SessionType.WORK: self.config.work_minutes * 60,
            SessionType.SHORT_BREAK: self.config.short_break_minutes * 60,
            SessionType.LONG_BREAK: self.config.long_break_minutes * 60,
        }
        return durations[session_type]

    def cancel(self) -> None:
        """Cancel the currently running session."""
        self._cancelled = True

    def run_session(self, session_type: Optional[SessionType] = None) -> SessionRecord:
        """Run a single timer session.

        Args:
            session_type: Type of session to run. Auto-detects if not provided.

        Returns:
            A SessionRecord describing the completed (or cancelled) session.
        """
        if self._running:
            raise RuntimeError("A session is already running")

        if session_type is None:
            session_type = self.get_next_session_type()

        total_seconds = self.get_duration_seconds(session_type)
        self._running = True
        self._cancelled = False
        elapsed = 0

        try:
            while elapsed < total_seconds and not self._cancelled:
                remaining = total_seconds - elapsed
                if self.on_tick:
                    self.on_tick(remaining, session_type)
                self._sleep(1.0)
                elapsed += 1

            completed = not self._cancelled
            record = SessionRecord(
                session_type=session_type,
                duration_seconds=elapsed,
                completed=completed,
            )

            if completed and session_type == SessionType.WORK:
                self._work_sessions_completed += 1

            self._history.append(record)

            if self.on_session_complete:
                self.on_session_complete(record)

            return record
        finally:
            self._running = False
            self._cancelled = False

    def format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS string.

        Args:
            seconds: Number of seconds to format.

        Returns:
            Formatted time string like '25:00'.
        """
        minutes, secs = divmod(max(0, seconds), 60)
        return f"{minutes:02d}:{secs:02d}"

    def get_stats(self) -> dict[str, int]:
        """Get summary statistics for the current session history.

        Returns:
            Dictionary with total_work_sessions, total_break_sessions,
            total_work_minutes, and total_break_minutes.
        """
        work_records = [r for r in self._history if r.session_type == SessionType.WORK and r.completed]
        break_records = [r for r in self._history if r.session_type != SessionType.WORK and r.completed]
        return {
            "total_work_sessions": len(work_records),
            "total_break_sessions": len(break_records),
            "total_work_minutes": sum(r.duration_seconds for r in work_records) // 60,
            "total_break_minutes": sum(r.duration_seconds for r in break_records) // 60,
        }
