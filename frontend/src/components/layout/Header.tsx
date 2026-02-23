'use client';

import Link from 'next/link';
import { Gamepad2 } from 'lucide-react';
import { GameSelector } from '@/components/game/GameSelector';
import { MobileNav } from './MobileNav';

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-bg/95 backdrop-blur">
      <div className="container flex h-14 items-center justify-between px-4 mx-auto max-w-6xl">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 font-bold text-xl text-white">
          <Gamepad2 className="h-6 w-6 text-accent" />
          <span>BossHelp</span>
        </Link>

        {/* Desktop: Game Selector */}
        <div className="hidden lg:block">
          <GameSelector />
        </div>

        {/* Mobile: Navigation Menu */}
        <MobileNav />
      </div>
    </header>
  );
}
