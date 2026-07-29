import { RotateCcw } from "lucide-react";

import type { GameSettings } from "../types/game";

export const presets = {
  beginner: { label: "Beginner", width: 9, height: 9, mineCount: 10 },
  intermediate: { label: "Intermediate", width: 16, height: 16, mineCount: 40 },
  expert: { label: "Expert", width: 30, height: 16, mineCount: 99 },
} as const;

export type PresetName = keyof typeof presets;

type GameControlsProps = {
  preset: PresetName;
  onCreate: (settings: GameSettings) => void;
  pending: boolean;
};

export function GameControls({ preset, onCreate, pending }: GameControlsProps) {
  return (
    <div className="game-controls">
      <label className="field-label" htmlFor="difficulty">Difficulty</label>
      <select
        disabled={pending}
        id="difficulty"
        onChange={(event) => onCreate(presets[event.target.value as PresetName])}
        value={preset}
      >
        {Object.entries(presets).map(([name, value]) => <option key={name} value={name}>{value.label}</option>)}
      </select>
      <button className="icon-command" disabled={pending} onClick={() => onCreate(presets[preset])} title="New game" type="button">
        <RotateCcw aria-hidden="true" size={17} />
        <span>New game</span>
      </button>
    </div>
  );
}
