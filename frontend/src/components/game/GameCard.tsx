'use client';

import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { Game } from '@/types';
import { Swords, Bug, Gamepad2 } from 'lucide-react';

interface GameCardProps {
  game: Game;
}

const genreIcons = {
  soulslike: Swords,
  metroidvania: Bug,
  action_rpg: Gamepad2,
};

const genreLabels = {
  soulslike: '소울라이크',
  metroidvania: '메트로이드바니아',
  action_rpg: '액션 RPG',
};

export function GameCard({ game }: GameCardProps) {
  const Icon = genreIcons[game.genre];

  return (
    <Link href={`/chat/${game.id}`}>
      <Card variant="interactive" className="h-full">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center">
            <Icon className="w-6 h-6 text-accent" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-white truncate">{game.title}</h3>
            <Badge variant="accent" className="mt-1">
              {genreLabels[game.genre]}
            </Badge>
          </div>
        </div>
      </Card>
    </Link>
  );
}
