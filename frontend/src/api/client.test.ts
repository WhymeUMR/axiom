import { afterEach, expect, it, vi } from "vitest";

import { revealCell } from "./client";

afterEach(() => vi.restoreAllMocks());

it("posts a cell reveal and returns game state", async () => {
  const state = { id: "game-1", grid: [] };
  const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(state), { status: 200, headers: { "Content-Type": "application/json" } }),
  );

  await expect(revealCell("game-1", { row: 2, column: 3 })).resolves.toEqual(state);
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/games/game-1/reveal",
    expect.objectContaining({ method: "POST", body: JSON.stringify({ row: 2, column: 3 }) }),
  );
});
