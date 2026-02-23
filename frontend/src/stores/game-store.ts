import { create } from 'zustand';
import type { Game } from '@/types';
import { api } from '@/lib/api';

// Fallback data when API fails
const FALLBACK_GAMES: Game[] = [
  { id: 'elden-ring', title: 'Elden Ring', genre: 'soulslike', isActive: true },
  { id: 'sekiro', title: 'Sekiro: Shadows Die Twice', genre: 'soulslike', isActive: true },
  { id: 'hollow-knight', title: 'Hollow Knight', genre: 'metroidvania', isActive: true },
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
  games: [],
  selectedGame: null,
  isLoading: false,

  fetchGames: async () => {
    set({ isLoading: true });
    try {
      const response = await api.getGames();
      set({ games: response.games, isLoading: false });
    } catch (error) {
      console.error('Failed to fetch games:', error);
      set({ games: FALLBACK_GAMES, isLoading: false });
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
