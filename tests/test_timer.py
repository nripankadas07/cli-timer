"""Tests for the Pomodoro timer engine."""

import pytest

from cli_timer.timer import PomodoroTimer, SessionRecord, SessionType, TimerConfig


class TestTimerConfig:
    """Tests for TimerConfig validation."""

    def test_default_config(self) -> None:
        config = TimerConfig()
        assert config.work_minutes == 25
        assert config.short_break_minutes == 5
        assert config.long_break_minutes == 15
        assert config.sessions_before_long_break == 4

    def test_custom_config(self) -> None:
        config = TimerConfig(work_minutes=30, short_break_minutes=10)
        assert config.work_minutes == 30
        assert config.short_break_minutes == 10

    def test_invalid_work_minutes(self) -> None:
        with pytest.raises(ValueError, match="work_minutes must be positive"):
            TimerConfig(work_minutes=0)

    def test_invalid_short_break(self) -> None:
        with pytest.raises(ValueError, match="short_break_minutes must be positive"):
            TimerConfig(short_break_minutes=-1)

    def test_invalid_long_break(self) -> None:
        with pytest.raises(ValueError, match="long_break_minutes must be positive"):
            TimerConfig(long_break_minutes=0)

    def test_invalid_sessions_before_long_break(self) -> None:
        with pytest.raises(ValueError, match="sessions_before_long_break must be positive"):
            TimerConfig(sessions_before_long_break=0)


class TestPomodoroTimer:
    """Tests for the PomodoroTimer engine."""

    def _make_timer(self, **kwargs) -> PomodoroTimer:
        """Create a timer with instant sleep for testing."""
        config = TimerConfig(work_minutes=1, short_break_minutes=1, long_break_minutes=1)
        return PomodoroTimer(
            config=config,
            sleep_func=lambda _: None,  # instant sleep
            **kwargs,
        )

    def test_initial_state(self) -> None:
        timer = self._make_timer()
        assert timer.work_sessions_completed == 0
        assert timer.history == []
        assert not timer.is_running

    def test_first_session_is_work(self) -> None:
        timer = self._make_timer()
        assert timer.get_next_session_type() == SessionType.WORK

    def test_work_session_completes(self) -> None:
        timer = self._make_timer()
        record = timer.run_session(SessionType.WORK)
        assert record.completed is True
        assert record.session_type == SessionType.WORK
        assert record.duration_seconds == 60  # 1 minute
        assert timer.work_sessions_completed == 1

    def test_short_break_after_work(self) -> None:
        timer = self._make_timer()
        timer.run_session(SessionType.WORK)
        assert timer.get_next_session_type() == SessionType.SHORT_BREAK

    def test_long_break_after_four_work_sessions(self) -> None:
        config = TimerConfig(
            work_minutes=1, short_break_minutes=1,
            long_break_minutes=1, sessions_before_long_break=4,
        )
        timer = PomodoroTimer(config=config, sleep_func=lambda _: None)
        for i in range(4):
            timer.run_session(SessionType.WORK)
            if i < 3:
                timer.run_session(SessionType.SHORT_BREAK)
        assert timer.get_next_session_type() == SessionType.LONG_BREAK

    def test_cancel_session(self) -> None:
        call_count = 0

        def counting_sleep(_: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 5:
                timer.cancel()

        timer = PomodoroTimer(
            config=TimerConfig(work_minutes=1),
            sleep_func=counting_sleep,
        )
        record = timer.run_session(SessionType.WORK)
        assert record.completed is False
        assert record.duration_seconds == 5
        assert timer.work_sessions_completed == 0  # not counted

    def test_on_tick_callback(self) -> None:
        ticks: list[tuple[int, SessionType]] = []

        def on_tick(remaining: int, st: SessionType) -> None:
            ticks.append((remaining, st))

        config = TimerConfig(work_minutes=1)
        timer = PomodoroTimer(config=config, on_tick=on_tick, sleep_func=lambda _: None)
        timer.run_session(SessionType.WORK)
        assert len(ticks) == 60
        assert ticks[0] == (60, SessionType.WORK)
        assert ticks[-1] == (1, SessionType.WORK)

    def test_on_session_complete_callback(self) -> None:
        records: list[SessionRecord] = []
        timer = PomodoroTimer(
            config=TimerConfig(work_minutes=1),
            on_session_complete=lambda r: records.append(r),
            sleep_func=lambda _: None,
        )
        timer.run_session(SessionType.WORK)
        assert len(records) == 1
        assert records[0].completed is True

    def test_cannot_run_two_sessions_simultaneously(self) -> None:
        """Verify RuntimeError if run_session called while already running."""
        timer = self._make_timer()
        # Simulate by directly setting _running
        timer._running = True
        with pytest.raises(RuntimeError, match="already running"):
            timer.run_session(SessionType.WORK)

    def test_format_time(self) -> None:
        timer = self._make_timer()
        assert timer.format_time(0) == "00:00"
        assert timer.format_time(59) == "00:59"
        assert timer.format_time(60) == "01:00"
        assert timer.format_time(1500) == "25:00"
        assert timer.format_time(5999) == "99:59"

    def test_format_time_negative(self) -> None:
        timer = self._make_timer()
        assert timer.format_time(-10) == "00:00"

    def test_get_stats_empty(self) -> None:
        timer = self._make_timer()
        stats = timer.get_stats()
        assert stats["total_work_sessions"] == 0
        assert stats["total_break_sessions"] == 0
        assert stats["total_work_minutes"] == 0
        assert stats["total_break_minutes"] == 0

    def test_get_stats_after_sessions(self) -> None:
        timer = self._make_timer()
        timer.run_session(SessionType.WORK)
        timer.run_session(SessionType.SHORT_BREAK)
        stats = timer.get_stats()
        assert stats["total_work_sessions"] == 1
        assert stats["total_break_sessions"] == 1
        assert stats["total_work_minutes"] == 1
        assert stats["total_break_minutes"] == 1

    def test_get_duration_seconds(self) -> None:
        config = TimerConfig(work_minutes=25, short_break_minutes=5, long_break_minutes=15)
        timer = PomodoroTimer(config=config)
        assert timer.get_duration_seconds(SessionType.WORK) == 1500
        assert timer.get_duration_seconds(SessionType.SHORT_BREAK) == 300
        assert timer.get_duration_seconds(SessionType.LONG_BREAK) == 900

    def test_history_returns_copy(self) -> None:
        timer = self._make_timer()
        timer.run_session(SessionType.WORK)
        history = timer.history
        history.clear()
        assert len(timer.history) == 1  # original not affected
