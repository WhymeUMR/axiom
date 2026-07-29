import type { CellAction, GameSettings, GameState } from "../types/game";

export class ApiError extends Error {
  constructor(readonly status: number, readonly detail: string) {
    super(detail);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body: unknown = await response.json();
  if (!response.ok) {
    const detail =
      typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string"
        ? body.detail
        : "Request failed";
    throw new ApiError(response.status, detail);
  }
  return body as T;
}

export const createGame = (settings: GameSettings) =>
  request<GameState>("/games", { method: "POST", body: JSON.stringify(settings) });

export const getGame = (gameId: string) => request<GameState>(`/games/${gameId}`);

export const revealCell = (gameId: string, cell: CellAction) =>
  request<GameState>(`/games/${gameId}/reveal`, {
    method: "POST",
    body: JSON.stringify(cell),
  });

export const toggleFlag = (gameId: string, cell: CellAction) =>
  request<GameState>(`/games/${gameId}/flag`, {
    method: "POST",
    body: JSON.stringify(cell),
  });

export const restartGame = (gameId: string) =>
  request<GameState>(`/games/${gameId}/restart`, { method: "POST" });
