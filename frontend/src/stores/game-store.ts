import { create } from 'zustand';
import type { Game } from '@/types';

// Mock data for development
const MOCK_GAMES: Game[] = [
  { id: 'elden-ring', title: 'Elden Ring', genre: 'soulslike', isActive: true },
  { id: 'sekiro', title: 'Sekiro: Shadows Die Twice', genre: 'soulslike', isActive: true },
  { id: 'hollow-knight', title: 'Hollow Knight', genre: 'metroidvania', isActive: true },
  { id: 'silksong', title: 'Hollow Knight: Silksong', genre: 'metroidvania', isActive: true },
  { id: 'lies-of-p', title: 'Lies of P', genre: 'soulslike', isActive: true },
];

interface GameState {
  games: Game[];
  selectedGame: Game | null;
  isLoading: boolean;

  // Actions
  fetchGames: () => Promise<void>;
  selectGame: (gameId: string) => void;
  clearSelection: () => void;
}

export const useGameStore = create<GameState>((set, get) => ({
  games: MOCK_GAMES,
  selectedGame: null,
  isLoading: false,

  fetchGames: async () => {
    set({ isLoading: true });
    try {
      // TODO: Replace with actual API call
      // const response = await api.getGames();
      // set({ games: response.games, isLoading: false });
      set({ games: MOCK_GAMES, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch games:', error);
      set({ isLoading: false });
    }
  },

  selectGame: (gameId: string) => {
    const game = get().games.find((g) => g.id === gameId);
    if (game) {
      set({ selectedGame: game });
    }
  },

  clearSelection: () => {
    set({ selectedGame: null });
  },
}));
