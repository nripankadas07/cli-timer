# ð cli-timer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

A Pomodoro CLI timer with a rich terminal UI. Stay focused with timed work sessions and automatic break scheduling, all from your terminal.

## Features

- **Pomodoro Technique**: Automatic work/short break/long break cycling
- **Rich Terminal UI**: Colorful output with progress indicators using [Rich](https://github.com/Textualize/rich)
- **Configurable Durations**: Customize work, short break, and long break lengths
- **Session Tracking**: Stats on completed work and break sessions
- **Graceful Cancellation**: Press Ctrl+C to stop the current session

## Installation

```bash
# Clone the repository
git clone https://github.com/nripankadas07/cli-timer.git
cd cli-timer

# Install in development mode
pip install -e ".[dev]"
```

## Usage

### Start a Pomodoro session

```bash
# Default: 25min work, 5min short break, 15min long break
cli-timer start

# Custom durations
cli-timer start --work 30 --short-break 10 --long-break 20

# Run 2 full cycles (8 work sessions total)
cli-timer start --cycles 2
```

### View default configuration

```bash
cli-timer config
```

### Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--work` | `-w` | 25 | Work session duration (minutes) |
| `--short-break` | `-s` | 5 | Short break duration (minutes) |
| `--long-break` | `-l` | 15 | Long break duration (minutes) |
| `--sessions` | `-n` | 4 | Work sessions before a long break |
| `--cycles` | `-c` | 1 | Number of full Pomodoro cycles |

## API Reference

### `TimerConfig`

Dataclass holding timer configuration:

```python
from cli_timer.timer import TimerConfig

config = TimerConfig(
    work_minutes=25,
    short_break_minutes=5,
    long_break_minutes=15,
    sessions_before_long_break=4,
)
```

### `PomodoroTimer`

Core timer engine:

```python
from cli_timer.timer import PomodoroTimer, SessionType

timer = PomodoroTimer(config=config)

# Run a work session
record = timer.run_session(SessionType.WORK)
print(record.completed)  # True
print(timer.work_sessions_completed)  # 1

# Check stats
stats = timer.get_stats()
print(stats["total_work_sessions"])  # 1
```

### `TimerDisplay`

Rich-based display layer:

```python
from cli_timer.display import TimerDisplay
from rich.console import Console

display = TimerDisplay(console=Console())
display.show_banner()
```

## Architecture

```
src/cli_timer/
âââ __init__.py    # Package version
âââ timer.py       # Core timer engine (TimerConfig, PomodoroTimer, SessionRecord)
âââ display.py     # Rich terminal display (TimerDisplay)
âââ main.py        # Click CLI entry point
```

The project follows a clean separation of concerns: `timer.py` handles all timing logic with no UI dependencies, `display.py` manages Rich-based rendering, and `main.py` wires them together via Click.

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT License â Copyright 2024 Nripanka Das
