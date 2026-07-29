import type { MouseEvent } from "react";

import type { CellAction, GameCell } from "../types/game";

type CellButtonProps = {
  cell: GameCell;
  row: number;
  column: number;
  disabled: boolean;
  onReveal: (cell: CellAction) => void;
  onFlag: (cell: CellAction) => void;
};

export function CellButton({ cell, row, column, disabled, onReveal, onFlag }: CellButtonProps) {
  const action = { row, column };
  const label = `Cell row ${row + 1} column ${column + 1} ${cell.state}`;
  const content = cell.mine ? "*" : cell.state === "flagged" ? "!" : cell.adjacentMines ?? "";

  const handleContextMenu = (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    if (!disabled) onFlag(action);
  };

  return (
    <button
      aria-label={label}
      className={`cell cell--${cell.state}${cell.mine ? " cell--mine" : ""}`}
      disabled={disabled}
      onClick={() => onReveal(action)}
      onContextMenu={handleContextMenu}
      type="button"
    >
      {content}
    </button>
  );
}
