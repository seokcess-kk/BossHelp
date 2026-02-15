'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useGameStore } from '@/stores/game-store';
import { ChatContainer } from '@/components/chat/ChatContainer';

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const gameId = params.gameId as string;
  const { games, selectedGame, selectGame } = useGameStore();

  useEffect(() => {
    if (gameId) {
      const game = games.find((g) => g.id === gameId);
      if (game) {
        selectGame(gameId);
      } else {
        router.push('/');
      }
    }
  }, [gameId, games, selectGame, router]);

  if (!selectedGame) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-56px)]">
        <div className="animate-spin w-8 h-8 border-2 border-accent border-t-transparent rounded-full" />
      </div>
    );
  }

  return <ChatContainer gameId={selectedGame.id} gameTitle={selectedGame.title} />;
}
