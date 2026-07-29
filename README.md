# Axiom Minesweeper

A classic Minesweeper game with a Python-owned game engine, a JSON API, and a React GUI.
The API is the integration point for a future reinforcement-learning agent; the current
increment is intentionally limited to the playable environment and its interface.

## Local Development

Use two terminals from the repository root.

```bash
cd backend
python3 -m venv ../.venv
../.venv/bin/pip install -e '.[dev]'
../.venv/bin/uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Verification

```bash
cd backend && ../.venv/bin/pytest -v && ../.venv/bin/ruff check app tests
cd frontend && npm test -- --run && npm run typecheck && npm run build
```

## API

- `POST /api/games`: create a game with `width`, `height`, `mineCount`, and optional `seed`.
- `GET /api/games/{gameId}`: read current public state.
- `POST /api/games/{gameId}/reveal`: reveal `{ "row": number, "column": number }`.
- `POST /api/games/{gameId}/flag`: toggle a flag.
- `POST /api/games/{gameId}/restart`: restart with the original settings.

The API does not reveal mine positions for an active game. Game rules exist only in the
Python backend, so the GUI and a future AI agent share the same environment.
