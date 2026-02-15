'use client';

import Link from 'next/link';
import { useGameStore } from '@/stores/game-store';
import { Gamepad2, ChevronDown } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

export function Header() {
  const { games, selectedGame, selectGame } = useGameStore();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-bg/95 backdrop-blur">
      <div className="container flex h-14 items-center justify-between px-4 mx-auto max-w-6xl">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-bold text-xl text-white">
          <Gamepad2 className="h-6 w-6 text-accent" />
          <span>BossHelp</span>
        </Link>

        {/* Game Selector */}
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={cn(
              'flex items-center gap-2 px-3 py-2 rounded-lg text-sm',
              'border border-border hover:bg-surface-hover transition-colors',
              selectedGame ? 'text-white' : 'text-text-secondary'
            )}
          >
            {selectedGame ? selectedGame.title : '게임 선택'}
            <ChevronDown className={cn('h-4 w-4 transition-transform', isDropdownOpen && 'rotate-180')} />
          </button>

          {isDropdownOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setIsDropdownOpen(false)} />
              <div className="absolute right-0 top-full mt-2 w-56 rounded-lg border border-border bg-surface shadow-lg z-20">
                {games.map((game) => (
                  <button
                    key={game.id}
                    onClick={() => {
                      selectGame(game.id);
                      setIsDropdownOpen(false);
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
      </div>
    </header>
  );
}
