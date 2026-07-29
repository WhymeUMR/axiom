import type { CellAction, GameState } from "../types/game";
import { CellButton } from "./CellButton";

type MinesweeperBoardProps = {
  game: GameState;
  onReveal: (cell: CellAction) => void;
  onFlag: (cell: CellAction) => void;
};

export function MinesweeperBoard({ game, onReveal, onFlag }: MinesweeperBoardProps) {
  return (
    <div
      aria-label="Minesweeper board"
      className="board"
      style={{ gridTemplateColumns: `repeat(${game.width}, var(--cell-size))` }}
    >
      {game.grid.flatMap((row, rowIndex) =>
        row.map((cell, columnIndex) => (
          <CellButton
            cell={cell}
            column={columnIndex}
            disabled={game.status !== "in_progress"}
            key={`${rowIndex}-${columnIndex}`}
            onFlag={onFlag}
            onReveal={onReveal}
            row={rowIndex}
          />
        )),
      )}
    </div>
  );
}
