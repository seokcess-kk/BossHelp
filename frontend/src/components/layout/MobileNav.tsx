'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useGameStore } from '@/stores/game-store';
import { useChatStore } from '@/stores/chat-store';
import { Menu, X, Home, MessageCircle, Settings, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

const SPOILER_LABELS = {
  none: '스포일러 없음',
  light: '가벼운 스포일러',
  heavy: '모든 스포일러',
} as const;

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const { selectedGame, games, selectGame } = useGameStore();
  const { spoilerLevel, setSpoilerLevel } = useChatStore();

  const navItems = [
    { href: '/', icon: Home, label: '홈' },
    ...(selectedGame
      ? [{ href: `/chat/${selectedGame.id}`, icon: MessageCircle, label: '채팅' }]
      : []),
  ];

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="lg:hidden p-2 text-text-secondary hover:text-white transition-colors"
        aria-label="메뉴 열기"
      >
        <Menu className="h-6 w-6" />
      </button>

      {/* Mobile Drawer */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setIsOpen(false)}
          />

          {/* Drawer */}
          <div className="fixed inset-y-0 right-0 w-72 bg-surface border-l border-border z-50 lg:hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <span className="font-semibold text-white">메뉴</span>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 text-text-secondary hover:text-white transition-colors"
                aria-label="메뉴 닫기"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Navigation Links */}
            <nav className="p-4 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                    pathname === item.href
                      ? 'bg-accent/10 text-accent'
                      : 'text-text-secondary hover:bg-surface-hover hover:text-white'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              ))}
            </nav>

            {/* Game Selection */}
            <div className="p-4 border-t border-border">
              <h3 className="text-xs font-medium text-text-secondary mb-3 uppercase tracking-wider">
                게임 선택
              </h3>
              <div className="space-y-1">
                {games.map((game) => (
                  <button
                    key={game.id}
                    onClick={() => {
                      selectGame(game.id);
                      setIsOpen(false);
                    }}
                    className={cn(
                      'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                      selectedGame?.id === game.id
                        ? 'bg-accent/10 text-accent'
                        : 'text-text-secondary hover:bg-surface-hover hover:text-white'
                    )}
                  >
                    {game.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Spoiler Settings */}
            <div className="p-4 border-t border-border">
              <h3 className="flex items-center gap-2 text-xs font-medium text-text-secondary mb-3 uppercase tracking-wider">
                <Shield className="h-4 w-4" />
                스포일러 설정
              </h3>
              <div className="space-y-1">
                {(Object.keys(SPOILER_LABELS) as Array<keyof typeof SPOILER_LABELS>).map(
                  (level) => (
                    <button
                      key={level}
                      onClick={() => {
                        setSpoilerLevel(level);
                        setIsOpen(false);
                      }}
                      className={cn(
                        'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
                        spoilerLevel === level
                          ? 'bg-accent/10 text-accent'
                          : 'text-text-secondary hover:bg-surface-hover hover:text-white'
                      )}
                    >
                      {SPOILER_LABELS[level]}
                    </button>
                  )
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
