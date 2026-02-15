'use client';

import { useCallback, useEffect, useMemo } from 'react';
import { useGameStore } from '@/stores/game-store';
import type { Game } from '@/types';

/**
 * useGames - Game data fetching and selection hook
 *
 * Provides access to game list and selection state.
 */
export function useGames() {
  const {
    games,
    selectedGame,
    isLoading,
    fetchGames,
    selectGame: storeSelectGame,
    clearSelection,
  } = useGameStore();

  // Fetch games on mount
  useEffect(() => {
    if (games.length === 0) {
      fetchGames();
    }
  }, [games.length, fetchGames]);

  // Select game by ID
  const selectGame = useCallback(
    (gameId: string) => {
      storeSelectGame(gameId);
    },
    [storeSelectGame]
  );

  // Get game by ID
  const getGameById = useCallback(
    (gameId: string): Game | undefined => {
      return games.find((g) => g.id === gameId);
    },
    [games]
  );

  // Filter games by genre
  const getGamesByGenre = useCallback(
    (genre: Game['genre']): Game[] => {
      return games.filter((g) => g.genre === genre);
    },
    [games]
  );

  // Get only active games
  const activeGames = useMemo(() => {
    return games.filter((g) => g.isActive);
  }, [games]);

  // Group games by genre
  const gamesByGenre = useMemo(() => {
    const grouped: Record<string, Game[]> = {};
    for (const game of games) {
      if (!grouped[game.genre]) {
        grouped[game.genre] = [];
      }
      grouped[game.genre].push(game);
    }
    return grouped;
  }, [games]);

  return {
    // State
    games,
    activeGames,
    selectedGame,
    isLoading,
    gamesByGenre,

    // Actions
    fetchGames,
    selectGame,
    clearSelection,
    getGameById,
    getGamesByGenre,
  };
}

/**
 * useSelectedGame - Subscribe to selected game only
 *
 * Lighter weight hook for components that only need the selected game.
 */
export function useSelectedGame() {
  const selectedGame = useGameStore((state) => state.selectedGame);
  const selectGame = useGameStore((state) => state.selectGame);

  return { selectedGame, selectGame };
}

/**
 * useGameList - Subscribe to game list only
 *
 * For components that only need to display the game list.
 */
export function useGameList() {
  const games = useGameStore((state) => state.games);
  const isLoading = useGameStore((state) => state.isLoading);

  return { games, isLoading };
}

export default useGames;
