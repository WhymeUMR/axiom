import { Bomb, BrainCircuit, Clock3, Flag, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError, createGame, getGame, revealCell, toggleFlag } from "./api/client";
import { GameControls, presets, type PresetName } from "./components/GameControls";
import { MinesweeperBoard } from "./components/MinesweeperBoard";
import type { CellAction, GameSettings, GameState } from "./types/game";

const formatTime = (seconds: number) => `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.detail : "Connection to the game server was lost.";
}

export default function App() {
  const [game, setGame] = useState<GameState | null>(null);
  const [preset, setPreset] = useState<PresetName>("beginner");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const apply = useCallback(async (operation: () => Promise<GameState>) => {
    setPending(true);
    try {
      setError(null);
      setGame(await operation());
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setPending(false);
    }
  }, []);

  const startGame = useCallback((settings: GameSettings) => {
    const selected = Object.entries(presets).find(([, value]) => value.width === settings.width && value.height === settings.height && value.mineCount === settings.mineCount);
    if (selected) setPreset(selected[0] as PresetName);
    void apply(() => createGame(settings));
  }, [apply]);

  const reveal = useCallback((cell: CellAction) => {
    if (game) void apply(() => revealCell(game.id, cell));
  }, [apply, game]);

  const flag = useCallback((cell: CellAction) => {
    if (game) void apply(() => toggleFlag(game.id, cell));
  }, [apply, game]);

  useEffect(() => { startGame(presets.beginner); }, [startGame]);

  useEffect(() => {
    if (!game || game.status !== "in_progress") return;
    const interval = window.setInterval(() => { void getGame(game.id).then(setGame).catch((caught) => setError(errorMessage(caught))); }, 1000);
    return () => window.clearInterval(interval);
  }, [game]);

  const flags = useMemo(() => game?.grid.flat().filter((cell) => cell.state === "flagged").length ?? 0, [game]);
  const title = game?.status === "won" ? "Board cleared" : game?.status === "lost" ? "Mine triggered" : "Live board";

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><Bomb aria-hidden="true" size={22} /><span>AXIOM</span><small>MINESWEEPER LAB</small></div>
        <div className={`connection ${error ? "connection--error" : ""}`}><i />{error ? "API unavailable" : "Python API connected"}</div>
      </header>
      <section className="workspace" aria-label="Minesweeper game">
        <div className="game-column">
          <div className="game-head">
            <div><h1>{title}</h1><p>{game ? `${game.width} x ${game.height} field` : "Preparing field"}</p></div>
            <GameControls onCreate={startGame} pending={pending} preset={preset} />
          </div>
          <div className="scorebar">
            <div><Flag aria-hidden="true" size={16} /><span>MINES</span><strong>{game ? game.mineCount - flags : "--"}</strong></div>
            <div><Clock3 aria-hidden="true" size={16} /><span>TIME</span><strong>{game ? formatTime(game.elapsedSeconds) : "--:--"}</strong></div>
          </div>
          {error && <div className="error-banner"><TriangleAlert aria-hidden="true" size={18} />{error}</div>}
          <div className="board-frame">{game ? <MinesweeperBoard game={game} onFlag={flag} onReveal={reveal} /> : <div className="loading-board">Loading game state</div>}</div>
        </div>
        <aside className="agent-panel">
          <div className="agent-icon"><BrainCircuit aria-hidden="true" size={21} /></div>
          <h2>Agent channel</h2>
          <p>The game API is ready for a future Python RL runtime.</p>
          <dl><div><dt>Session</dt><dd>{game?.id.slice(0, 8) ?? "waiting"}</dd></div><div><dt>State</dt><dd>{game?.status.replace("_", " ") ?? "waiting"}</dd></div></dl>
        </aside>
      </section>
    </main>
  );
}
