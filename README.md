# Fretboard Memorization Game 🎸

A terminal-based game for learning the notes on a guitar fretboard. Built with Python, no dependencies required.

## How It Works

The game highlights a position on a visual fretboard and asks you to identify the note. It uses a **spaced repetition-style learning system** — positions you haven't mastered yet appear more frequently (75% of the time), while already-learned positions are reinforced occasionally.

A position is considered "learned" once you answer it correctly 3 times within 5 seconds each.

## Modes

**Random mode** (default) — 2-minute timed game. Score as many correct answers as possible before time runs out. High score is tracked between sessions.

**Sequential mode** (`--frets`) — Work through all 72 fret positions in a structured order, moving from commonly-used frets outward. No time limit — tracks elapsed time instead.

## Usage

```bash
python fretboard_game.py              # Random mode, sharps
python fretboard_game.py --flats      # Use flat note names (D♭ instead of C♯)
python fretboard_game.py --labels     # Show string names and fret numbers
python fretboard_game.py --frets      # Sequential mode
```

Options can be combined:
```bash
python fretboard_game.py --frets --labels --flats
```

## Controls

| Key | Action |
|-----|--------|
| `0`–`9`, `.`, `+` | Select a note answer |
| `x` | Exit the current game |

## Requirements

- Python 3.x
- macOS or Linux (uses `termios` for raw keyboard input — not compatible with Windows)

## Persistence

Progress and high scores are saved locally in the project directory:

- `fretboard_highscore.json` — best score in random mode
- `fretboard_learning.json` — per-position learning progress across all modes
