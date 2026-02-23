'use client';

import { useState } from 'react';
import { useGameStore } from '@/stores/game-store';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface GameSelectorProps {
  className?: string;
}

export function GameSelector({ className }: GameSelectorProps) {
  const { games, selectedGame, selectGame } = useGameStore();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={cn('relative', className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-lg text-sm',
          'border border-border hover:bg-surface-hover transition-colors',
          selectedGame ? 'text-white' : 'text-text-secondary'
        )}
      >
        {selectedGame ? selectedGame.title : '게임 선택'}
        <ChevronDown className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')} />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />

          {/* Dropdown Menu */}
          <div className="absolute right-0 top-full mt-2 w-56 rounded-lg border border-border bg-surface shadow-lg z-20">
            {games.map((game) => (
              <button
                key={game.id}
                onClick={() => {
                  selectGame(game.id);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full px-4 py-2.5 text-left text-sm hover:bg-surface-hover transition-colors',
                  'first:rounded-t-lg last:rounded-b-lg',
                  selectedGame?.id === game.id ? 'text-accent' : 'text-white'
                )}
              >
                {game.title}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
