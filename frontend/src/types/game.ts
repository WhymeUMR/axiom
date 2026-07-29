export type CellState = "hidden" | "revealed" | "flagged";
export type GameStatus = "in_progress" | "won" | "lost";

export type GameCell = {
  state: CellState;
  adjacentMines?: number;
  mine?: boolean;
};

export type GameSettings = {
  width: number;
  height: number;
  mineCount: number;
  seed?: number;
};

export type CellAction = {
  row: number;
  column: number;
};

export type GameState = {
  id: string;
  width: number;
  height: number;
  mineCount: number;
  elapsedSeconds: number;
  status: GameStatus;
  grid: GameCell[][];
};
