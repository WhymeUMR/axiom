# Minesweeper GUI and API: Design

**Date:** 2026-07-29
**Status:** proposed
**Scope:** first implementation increment

## Goal

Deliver a classic, playable Minesweeper application with a polished browser GUI and
a Python API designed for a future reinforcement-learning agent. The application
must own the board state directly; it must not depend on screen capture or computer
vision.

## Scope

This increment includes:

- configurable classic Minesweeper boards;
- left-click reveal, right-click flagging, timer, mine counter, reset, win, and loss;
- a REST API that exposes deterministic game operations and serializable state;
- a browser GUI that calls the API and renders the returned state;
- deterministic seeds for tests and future simulation;
- project documentation in the repository and Obsidian.

This increment excludes model training, PPO, PyTorch, autonomous AI play, WebSocket
streaming, and explanations of model decisions. Those features are a separate next
increment and must use the API introduced here.

## Architecture

The Python backend is the sole owner of the game rules and state. `GameService`
coordinates games identified by UUIDs and delegates all board mechanics to a pure,
side-effect-free domain module. The API layer only validates requests and maps domain
objects to JSON. This keeps the future AI integration independent of the GUI.

The React frontend is an API client. It renders a responsive board, game controls,
and status information from API responses. It does not calculate mines, neighbouring
counts, win conditions, or legal moves locally.

```text
React GUI -> HTTP JSON -> FastAPI -> GameService -> Minesweeper domain
                                               -> state snapshot for future AI
```

## API Contract

All endpoints are local and JSON based.

- `POST /api/games`: create a game. Request accepts width, height, mines, and an
  optional integer seed. Response returns an opaque game id and public state.
- `GET /api/games/{game_id}`: return the current public state.
- `POST /api/games/{game_id}/reveal`: reveal `{ "row": number, "column": number }`.
- `POST /api/games/{game_id}/flag`: toggle a flag at the given coordinate.
- `POST /api/games/{game_id}/restart`: reset the game with its original settings;
  a new random layout is used unless a seed was supplied.

The public state contains dimensions, mine count, elapsed seconds, status, and a
row-major grid of cells. Each cell carries `state` (`hidden`, `revealed`, `flagged`)
and exposes `adjacentMines` only after reveal. Mine positions are never returned while
the game is active. At win or loss, mine positions are returned for rendering.

The same contract will later be extended with an agent-only observation endpoint that
may expose structured board data without weakening normal GUI behavior.

## GUI

The initial screen starts a standard beginner game and provides a compact difficulty
selector for Beginner (9x9, 10 mines), Intermediate (16x16, 40 mines), Expert
(30x16, 99 mines), and Custom. The UI includes a restart button, numeric timer,
remaining-mine count, responsive board scaling, keyboard-accessible cells, and clear
visual states for hidden, flagged, revealed, victory, and exploded mine cells.

The layout reserves a non-intrusive right-side activity area for the future AI runtime.
Until the AI increment, it displays game status only; it does not imply that an agent
is active.

## Error Handling

The API returns 404 for unknown game ids, 422 for malformed or out-of-board
coordinates, and a stable 409 error when an action is attempted in a finished game.
The GUI displays a recoverable error message and keeps the last valid board state.

## Test Strategy

Before implementation, write tests covering at least:

1. requested mine count and unique mine placement;
2. correct adjacent mine counts;
3. first reveal never exposes a mine;
4. flood reveal of zero-count cells;
5. flag toggling and counter changes;
6. loss after revealing a mine;
7. win after every safe cell is revealed;
8. deterministic layouts with the same seed;
9. no mine data leakage in active API responses;
10. API validation and terminal-state responses.

## Acceptance Criteria

- A user can complete a standard game without opening developer tools.
- All game rules are calculated by Python and verified by automated tests.
- A Python program can create a game, read its state, and make legal moves through
  the documented API.
- The frontend has no duplicated game-rule implementation.
- The future RL agent can be added behind the API without changing the GUI's board
  protocol.
