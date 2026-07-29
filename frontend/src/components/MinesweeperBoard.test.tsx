import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it, vi } from "vitest";

import { MinesweeperBoard } from "./MinesweeperBoard";
import type { GameState } from "../types/game";

const game: GameState = {
  id: "game-1",
  width: 2,
  height: 2,
  mineCount: 1,
  elapsedSeconds: 0,
  status: "in_progress",
  grid: [[{ state: "hidden" }, { state: "hidden" }], [{ state: "hidden" }, { state: "hidden" }]],
};

it("reveals a cell with the primary action", async () => {
  const onReveal = vi.fn();
  render(<MinesweeperBoard game={game} onReveal={onReveal} onFlag={vi.fn()} />);

  await userEvent.click(screen.getByRole("button", { name: "Cell row 1 column 1 hidden" }));

  expect(onReveal).toHaveBeenCalledWith({ row: 0, column: 0 });
});

it("flags a hidden cell with the context-menu action", () => {
  const onFlag = vi.fn();
  render(<MinesweeperBoard game={game} onReveal={vi.fn()} onFlag={onFlag} />);

  fireEvent.contextMenu(screen.getByRole("button", { name: "Cell row 1 column 1 hidden" }));

  expect(onFlag).toHaveBeenCalledWith({ row: 0, column: 0 });
});
