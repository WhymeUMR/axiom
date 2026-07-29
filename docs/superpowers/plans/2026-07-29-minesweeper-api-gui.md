# Minesweeper API and GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a playable classic Minesweeper web application whose Python backend owns the game rules and exposes a stable API for a future RL agent.

**Architecture:** The backend contains a pure domain model, an in-memory game service, and FastAPI adapters. The React/Vite frontend is an API-only client and contains rendering, controls, and recoverable request state, but no game rules.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, Uvicorn, pytest, React 18, TypeScript, Vite, Vitest, Testing Library, CSS modules.

---

## File Structure

- `backend/pyproject.toml`: backend dependencies and pytest settings.
- `backend/app/domain/models.py`: immutable enums and transport-neutral domain values.
- `backend/app/domain/board.py`: mine placement, reveal, flag, win, and loss rules.
- `backend/app/services/games.py`: UUID-indexed game lifecycle and timer coordination.
- `backend/app/api/schemas.py`: request and response Pydantic models.
- `backend/app/api/routes.py`: FastAPI HTTP handlers and error translation.
- `backend/app/main.py`: application factory, CORS, and route registration.
- `backend/tests/`: unit and API contract tests.
- `frontend/`: Vite React client.
- `frontend/src/api/client.ts`: typed fetch client and error representation.
- `frontend/src/types/game.ts`: API-compatible frontend types.
- `frontend/src/components/`: board, cells, control panel, and error UI.
- `frontend/src/App.tsx`: page state and API action orchestration.
- `frontend/src/styles.css`: responsive visual system.
- `frontend/src/**/*.test.tsx`: frontend behavior tests.

### Task 1: Bootstrap the Python backend

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/domain/__init__.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/tests/test_smoke.py`

- [ ] **Step 1: Write the failing import test**

```python
def test_backend_package_is_importable() -> None:
    from app.main import create_app

    assert callable(create_app)
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `cd backend && pytest tests/test_smoke.py -v`

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: Add package setup and the smallest application factory**

```toml
[project]
name = "axiom-minesweeper-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi>=0.115,<1", "uvicorn[standard]>=0.30,<1"]

[project.optional-dependencies]
dev = ["httpx>=0.27,<1", "pytest>=8,<9", "ruff>=0.6,<1"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

```python
# backend/app/main.py
from fastapi import FastAPI


def create_app() -> FastAPI:
    return FastAPI(title="Axiom Minesweeper API")


app = create_app()
```

- [ ] **Step 4: Run the test and lint**

Run: `cd backend && pytest tests/test_smoke.py -v && ruff check app tests`

Expected: one passing test and no Ruff findings.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "build: bootstrap minesweeper backend"
```

### Task 2: Implement deterministic board construction and adjacency

**Files:**
- Create: `backend/app/domain/models.py`
- Create: `backend/app/domain/board.py`
- Create: `backend/tests/domain/test_board_creation.py`

- [ ] **Step 1: Write failing domain tests**

```python
def test_seeded_board_has_requested_unique_mines() -> None:
    board = Board.create(width=9, height=9, mine_count=10, seed=7)

    assert len(board.mines) == 10
    assert len(set(board.mines)) == 10


def test_seeded_boards_are_reproducible() -> None:
    first = Board.create(width=9, height=9, mine_count=10, seed=7)
    second = Board.create(width=9, height=9, mine_count=10, seed=7)

    assert first.mines == second.mines


def test_adjacent_mine_count_is_correct() -> None:
    board = Board.from_mines(width=3, height=3, mines={(0, 0), (2, 2)})

    assert board.adjacent_mines((1, 1)) == 2
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `cd backend && pytest tests/domain/test_board_creation.py -v`

Expected: FAIL because `Board` is not defined.

- [ ] **Step 3: Implement coordinate-safe board creation**

```python
# backend/app/domain/models.py
from dataclasses import dataclass
from enum import StrEnum


class GameStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"


class CellState(StrEnum):
    HIDDEN = "hidden"
    REVEALED = "revealed"
    FLAGGED = "flagged"


class GameFinishedError(RuntimeError):
    pass


@dataclass(frozen=True, order=True)
class Coordinate:
    row: int
    column: int
```

```python
# backend/app/domain/board.py
from dataclasses import dataclass, field
from random import Random

from app.domain.models import CellState, Coordinate, GameFinishedError, GameStatus


@dataclass
class Board:
    width: int
    height: int
    mine_count: int
    mines: set[Coordinate]
    cells: dict[Coordinate, CellState] = field(default_factory=dict)
    status: GameStatus = GameStatus.IN_PROGRESS

    @classmethod
    def create(cls, width: int, height: int, mine_count: int, seed: int | None = None) -> "Board":
        if not 1 <= mine_count < width * height:
            raise ValueError("mine_count must leave at least one safe cell")
        coordinates = [Coordinate(row, column) for row in range(height) for column in range(width)]
        mines = set(Random(seed).sample(coordinates, mine_count))
        return cls(width, height, mine_count, mines, {cell: CellState.HIDDEN for cell in coordinates})

    @classmethod
    def from_mines(cls, width: int, height: int, mines: set[tuple[int, int]]) -> "Board":
        mine_coordinates = {Coordinate(row, column) for row, column in mines}
        return cls.create(width, height, len(mine_coordinates), 0)._replace_mines(mine_coordinates)

    def _replace_mines(self, mines: set[Coordinate]) -> "Board":
        self.mines = mines
        return self

    def adjacent_mines(self, cell: Coordinate | tuple[int, int]) -> int:
        coordinate = cell if isinstance(cell, Coordinate) else Coordinate(*cell)
        return sum(neighbor in self.mines for neighbor in self.neighbors(coordinate))

    def neighbors(self, cell: Coordinate) -> list[Coordinate]:
        return [
            Coordinate(row, column)
            for row in range(max(0, cell.row - 1), min(self.height, cell.row + 2))
            for column in range(max(0, cell.column - 1), min(self.width, cell.column + 2))
            if (row, column) != (cell.row, cell.column)
        ]
```

- [ ] **Step 4: Run domain tests**

Run: `cd backend && pytest tests/domain/test_board_creation.py -v && ruff check app tests`

Expected: three passing tests and no Ruff findings.

- [ ] **Step 5: Commit**

```bash
git add backend/app/domain backend/tests/domain
git commit -m "feat: add deterministic minesweeper board"
```

### Task 3: Implement reveal, flags, terminal states, and first-click safety

**Files:**
- Modify: `backend/app/domain/board.py`
- Create: `backend/tests/domain/test_board_actions.py`

- [ ] **Step 1: Write failing behavior tests**

```python
def test_first_reveal_relocates_a_mine() -> None:
    board = Board.from_mines(width=2, height=2, mines={(0, 0)})

    board.reveal(Coordinate(0, 0))

    assert board.status is GameStatus.IN_PROGRESS
    assert board.cells[Coordinate(0, 0)] is CellState.REVEALED


def test_zero_reveal_floods_connected_safe_cells() -> None:
    board = Board.from_mines(width=4, height=4, mines={(3, 3)})

    board.reveal(Coordinate(0, 0))

    assert board.cells[Coordinate(2, 2)] is CellState.REVEALED
    assert board.cells[Coordinate(3, 3)] is CellState.HIDDEN


def test_revealing_a_mine_loses_after_first_turn() -> None:
    board = Board.from_mines(width=3, height=3, mines={(0, 0)})

    board.reveal(Coordinate(1, 1))
    board.reveal(Coordinate(0, 0))

    assert board.status is GameStatus.LOST


def test_revealing_all_safe_cells_wins() -> None:
    board = Board.from_mines(width=2, height=2, mines={(0, 0)})

    for cell in (Coordinate(0, 1), Coordinate(1, 0), Coordinate(1, 1)):
        board.reveal(cell)

    assert board.status is GameStatus.WON


def test_flag_toggles_without_revealing_cell() -> None:
    board = Board.from_mines(width=2, height=2, mines={(0, 0)})

    board.toggle_flag(Coordinate(0, 0))

    assert board.cells[Coordinate(0, 0)] is CellState.FLAGGED
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `cd backend && pytest tests/domain/test_board_actions.py -v`

Expected: FAIL because action methods do not exist.

- [ ] **Step 3: Implement actions using recursive-free flood fill**

```python
def reveal(self, cell: Coordinate) -> None:
    self._require_active()
    self._require_inside(cell)
    if self.cells[cell] is CellState.FLAGGED:
        return
    if not any(state is CellState.REVEALED for state in self.cells.values()) and cell in self.mines:
        self._relocate_mine(cell)
    if cell in self.mines:
        self.status = GameStatus.LOST
        self.cells[cell] = CellState.REVEALED
        return
    self._reveal_safe_region(cell)
    if all(self.cells[coordinate] is CellState.REVEALED for coordinate in self.cells if coordinate not in self.mines):
        self.status = GameStatus.WON

def toggle_flag(self, cell: Coordinate) -> None:
    self._require_active()
    self._require_inside(cell)
    self.cells[cell] = CellState.HIDDEN if self.cells[cell] is CellState.FLAGGED else CellState.FLAGGED

def _require_inside(self, cell: Coordinate) -> None:
    if not (0 <= cell.row < self.height and 0 <= cell.column < self.width):
        raise ValueError("cell is outside the board")

def _require_active(self) -> None:
    if self.status is not GameStatus.IN_PROGRESS:
        raise GameFinishedError()

def _relocate_mine(self, cell: Coordinate) -> None:
    replacement = next(candidate for candidate in self.cells if candidate not in self.mines and candidate != cell)
    self.mines.remove(cell)
    self.mines.add(replacement)

def _reveal_safe_region(self, origin: Coordinate) -> None:
    pending = [origin]
    while pending:
        cell = pending.pop()
        if self.cells[cell] is CellState.REVEALED or cell in self.mines:
            continue
        self.cells[cell] = CellState.REVEALED
        if self.adjacent_mines(cell) == 0:
            pending.extend(neighbor for neighbor in self.neighbors(cell) if self.cells[neighbor] is CellState.HIDDEN)
```

- [ ] **Step 4: Run all domain tests**

Run: `cd backend && pytest tests/domain -v && ruff check app tests`

Expected: eight passing tests and no Ruff findings.

- [ ] **Step 5: Commit**

```bash
git add backend/app/domain/board.py backend/tests/domain/test_board_actions.py
git commit -m "feat: implement minesweeper actions"
```

### Task 4: Add game lifecycle service and public state projection

**Files:**
- Create: `backend/app/services/games.py`
- Create: `backend/tests/services/test_games.py`

- [ ] **Step 1: Write failing service tests**

```python
def test_created_game_has_a_uuid_and_hidden_mines() -> None:
    service = GameService(clock=lambda: 100.0)

    game = service.create(GameConfig(width=9, height=9, mine_count=10, seed=3))

    assert UUID(game.id)
    assert all(cell.mine is None for row in game.snapshot.grid for cell in row)


def test_restart_reuses_the_original_configuration() -> None:
    service = GameService(clock=lambda: 100.0)
    game = service.create(GameConfig(width=2, height=2, mine_count=1, seed=3))
    restarted = service.restart(game.id)

    assert restarted.config == game.config
    assert restarted.id == game.id
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `cd backend && pytest tests/services/test_games.py -v`

Expected: FAIL because the service does not exist.

- [ ] **Step 3: Implement service-owned snapshots**

```python
@dataclass(frozen=True)
class GameConfig:
    width: int
    height: int
    mine_count: int
    seed: int | None = None


@dataclass
class GameRecord:
    id: str
    config: GameConfig
    board: Board
    started_at: float

    @property
    def snapshot(self) -> PublicGameState:
        return self.to_public_state(now=self.started_at)


class GameService:
    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._games: dict[str, GameRecord] = {}

    def create(self, config: GameConfig) -> GameRecord:
        record = GameRecord(id=str(uuid4()), config=config, board=Board.create(**asdict(config)), started_at=self._clock())
        self._games[record.id] = record
        return record

    def snapshot(self, game_id: str) -> PublicGameState:
        return self._get(game_id).to_public_state(now=self._clock())

    def restart(self, game_id: str) -> GameRecord:
        previous = self._get(game_id)
        replacement = GameRecord(id=previous.id, config=previous.config, board=Board.create(**asdict(previous.config)), started_at=self._clock())
        self._games[game_id] = replacement
        return replacement
```

- [ ] **Step 4: Run service tests**

Run: `cd backend && pytest tests/services/test_games.py -v && ruff check app tests`

Expected: two passing tests and no Ruff findings.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services backend/tests/services
git commit -m "feat: add game lifecycle service"
```

### Task 5: Expose the game through FastAPI

**Files:**
- Create: `backend/app/api/schemas.py`
- Create: `backend/app/api/routes.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/api/test_games_api.py`

- [ ] **Step 1: Write failing API contract tests**

```python
async def test_create_and_reveal_game() -> None:
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        created = await client.post("/api/games", json={"width": 9, "height": 9, "mineCount": 10, "seed": 7})
        game_id = created.json()["id"]
        revealed = await client.post(f"/api/games/{game_id}/reveal", json={"row": 0, "column": 0})

    assert created.status_code == 201
    assert revealed.status_code == 200
    assert revealed.json()["grid"][0][0]["state"] == "revealed"


async def test_unknown_game_returns_404() -> None:
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        response = await client.get("/api/games/missing")

    assert response.status_code == 404
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `cd backend && pytest tests/api/test_games_api.py -v`

Expected: FAIL because no API routes are registered.

- [ ] **Step 3: Register routes with explicit schemas**

```python
router = APIRouter(prefix="/api/games", tags=["games"])

@router.post("", response_model=GameStateResponse, status_code=status.HTTP_201_CREATED)
def create_game(request: CreateGameRequest, service: GameService = Depends(get_game_service)) -> GameStateResponse:
    return GameStateResponse.from_domain(service.create(GameConfig.from_request(request)).snapshot)

@router.post("/{game_id}/reveal", response_model=GameStateResponse)
def reveal(game_id: str, request: CellActionRequest, service: GameService = Depends(get_game_service)) -> GameStateResponse:
    return GameStateResponse.from_domain(service.reveal(game_id, Coordinate(request.row, request.column)))
```

- [ ] **Step 4: Add CORS and error handlers to the application factory**

```python
def create_app() -> FastAPI:
    app = FastAPI(title="Axiom Minesweeper API")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
    app.include_router(router)
    app.add_exception_handler(GameNotFoundError, game_not_found_handler)
    app.add_exception_handler(GameFinishedError, game_finished_handler)
    return app
```

- [ ] **Step 5: Run API and complete backend checks**

Run: `cd backend && pytest -v && ruff check app tests`

Expected: all backend tests pass and Ruff reports no findings.

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: expose minesweeper api"
```

### Task 6: Bootstrap React client and typed API access

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/types/game.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write the failing API-client test**

```ts
it("posts a cell reveal and returns game state", async () => {
  server.use(http.post("/api/games/game-1/reveal", () => HttpResponse.json(gameState)));

  await expect(revealCell("game-1", { row: 2, column: 3 })).resolves.toEqual(gameState);
});
```

- [ ] **Step 2: Run it and verify it fails**

Run: `cd frontend && npm test -- client.test.ts`

Expected: FAIL because the client module does not exist.

- [ ] **Step 3: Implement transport-neutral client functions**

```ts
export type CellAction = { row: number; column: number };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  if (!response.ok) throw new ApiError(response.status, await response.json());
  return response.json() as Promise<T>;
}

export const createGame = (settings: GameSettings) => request<GameState>("/games", { method: "POST", body: JSON.stringify(settings) });
export const revealCell = (gameId: string, cell: CellAction) => request<GameState>(`/games/${gameId}/reveal`, { method: "POST", body: JSON.stringify(cell) });
export const toggleFlag = (gameId: string, cell: CellAction) => request<GameState>(`/games/${gameId}/flag`, { method: "POST", body: JSON.stringify(cell) });
```

- [ ] **Step 4: Run frontend unit checks**

Run: `cd frontend && npm test -- --run && npm run lint && npm run typecheck`

Expected: client test passes, lint and TypeScript have no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "build: bootstrap minesweeper frontend"
```

### Task 7: Build accessible board and game controls

**Files:**
- Create: `frontend/src/components/MinesweeperBoard.tsx`
- Create: `frontend/src/components/CellButton.tsx`
- Create: `frontend/src/components/GameControls.tsx`
- Create: `frontend/src/components/MinesweeperBoard.test.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Write failing user-flow tests**

```tsx
it("reveals a cell with the primary action", async () => {
  render(<MinesweeperBoard game={gameState} onReveal={onReveal} onFlag={onFlag} />);

  await userEvent.click(screen.getByRole("button", { name: "Cell row 1 column 1 hidden" }));

  expect(onReveal).toHaveBeenCalledWith({ row: 0, column: 0 });
});

it("flags a hidden cell with the context-menu action", async () => {
  render(<MinesweeperBoard game={gameState} onReveal={onReveal} onFlag={onFlag} />);

  fireEvent.contextMenu(screen.getByRole("button", { name: "Cell row 1 column 1 hidden" }));

  expect(onFlag).toHaveBeenCalledWith({ row: 0, column: 0 });
});
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `cd frontend && npm test -- MinesweeperBoard.test.tsx`

Expected: FAIL because board components do not exist.

- [ ] **Step 3: Implement semantic cells and action orchestration**

```tsx
export function CellButton({ cell, row, column, onReveal, onFlag }: CellButtonProps) {
  const label = `Cell row ${row + 1} column ${column + 1} ${cell.state}`;
  return <button aria-label={label} className={`cell cell--${cell.state}`} onClick={() => onReveal({ row, column })} onContextMenu={(event) => { event.preventDefault(); onFlag({ row, column }); }} />;
}
```

```tsx
function App() {
  const [game, setGame] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const apply = async (operation: () => Promise<GameState>) => {
    try { setError(null); setGame(await operation()); } catch (caught) { setError(toMessage(caught)); }
  };
  useEffect(() => { void apply(() => createGame(beginnerSettings)); }, []);
  return <GameScreen game={game} error={error} onReveal={(cell) => apply(() => revealCell(game!.id, cell))} onFlag={(cell) => apply(() => toggleFlag(game!.id, cell))} />;
}
```

- [ ] **Step 4: Run component tests, lint, and type check**

Run: `cd frontend && npm test -- --run && npm run lint && npm run typecheck`

Expected: all tests pass with no lint or type errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src
git commit -m "feat: add playable minesweeper board"
```

### Task 8: Style responsive game states and difficulty controls

**Files:**
- Create: `frontend/src/styles.css`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/GameControls.tsx`
- Create: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing difficulty and terminal-state tests**

```tsx
it("creates an intermediate game when the difficulty changes", async () => {
  render(<App />);

  await userEvent.selectOptions(await screen.findByLabelText("Difficulty"), "intermediate");

  expect(await screen.findByText("16 x 16")).toBeInTheDocument();
});

it("shows a restart action after a lost game", async () => {
  render(<GameScreen game={{ ...gameState, status: "lost" }} error={null} onReveal={vi.fn()} onFlag={vi.fn()} />);

  expect(screen.getByRole("button", { name: "New game" })).toBeVisible();
});
```

- [ ] **Step 2: Run the tests and verify they fail**

Run: `cd frontend && npm test -- App.test.tsx`

Expected: FAIL because difficulty selection and terminal controls are incomplete.

- [ ] **Step 3: Add explicit presets and responsive CSS tokens**

```ts
export const presets = {
  beginner: { width: 9, height: 9, mineCount: 10 },
  intermediate: { width: 16, height: 16, mineCount: 40 },
  expert: { width: 30, height: 16, mineCount: 99 },
} as const;
```

```css
:root { color: #1b2430; background: #edf1f5; font-family: Inter, system-ui, sans-serif; }
.game-shell { width: min(100% - 2rem, 1320px); margin: 2rem auto; }
.board { display: grid; gap: 2px; overflow: auto; max-width: 100%; padding: 8px; background: #29313d; }
.cell { width: 34px; height: 34px; border: 0; border-radius: 4px; font-weight: 800; }
.cell--hidden { background: #9fb3c8; cursor: pointer; }
.cell--revealed { background: #f8fafc; }
.cell--flagged { background: #f5b942; }
@media (max-width: 640px) { .game-shell { width: min(100% - 1rem, 1320px); margin: .5rem auto; } .cell { width: 30px; height: 30px; } }
```

- [ ] **Step 4: Run all frontend checks and production build**

Run: `cd frontend && npm test -- --run && npm run lint && npm run typecheck && npm run build`

Expected: all tests pass and Vite emits a production bundle.

- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add responsive game controls and styling"
```

### Task 9: Verify the full local flow and document it

**Files:**
- Modify: `README.md`
- Modify: `/Users/bogdanlazarev/Developer/obsidian-storage/Codex/Axiom/Project.md`
- Create: `backend/tests/api/test_public_state.py`

- [ ] **Step 1: Write a final API disclosure test**

```python
async def test_active_game_does_not_disclose_mine_locations() -> None:
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        response = await client.post("/api/games", json={"width": 9, "height": 9, "mineCount": 10, "seed": 7})

    assert "mine" not in response.text.lower()
```

- [ ] **Step 2: Run it and verify it fails before projection is corrected**

Run: `cd backend && pytest tests/api/test_public_state.py -v`

Expected: FAIL if the response serializer leaks mine data; otherwise document the existing passing protection and retain the test.

- [ ] **Step 3: Document the exact local run commands**

```markdown
## Local development

Terminal 1:
`cd backend && uv run uvicorn app.main:app --reload --port 8000`

Terminal 2:
`cd frontend && npm install && npm run dev`

Open `http://localhost:5173`. The frontend proxies `/api` to `http://localhost:8000`.
```

- [ ] **Step 4: Execute the complete verification suite**

Run: `cd backend && pytest -v && ruff check app tests`

Run: `cd frontend && npm test -- --run && npm run lint && npm run typecheck && npm run build`

Expected: all checks pass; backend exposes no active-game mine locations; frontend production build succeeds.

- [ ] **Step 5: Manually verify the browser workflow**

Run backend and frontend with the documented commands. In the browser, create a Beginner game, reveal a cell, flag a cell, change to Intermediate, finish or restart a game, and confirm the board remains usable at 390px and 1440px widths.

- [ ] **Step 6: Commit**

```bash
git add README.md backend/tests/api/test_public_state.py
git commit -m "docs: document minesweeper local workflow"
```
