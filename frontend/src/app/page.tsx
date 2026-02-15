'use client';

import { useGameStore } from '@/stores/game-store';
import { GameCard } from '@/components/game/GameCard';
import { Gamepad2, Zap, Shield, MessageCircle } from 'lucide-react';

export default function HomePage() {
  const { games } = useGameStore();

  return (
    <main className="min-h-[calc(100vh-56px)]">
      {/* Hero Section */}
      <section className="py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            막히면 물어봐.
            <br />
            <span className="text-accent">바로 알려줄게.</span>
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            하드코어 게임에서 막혔을 때, 채팅창에 질문 하나만 던지면
            <br />
            3초 안에 정확한 공략을 알려주는 AI 도우미
          </p>
        </div>
      </section>

      {/* Features */}
      <section className="py-8 px-4 border-t border-border">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex items-start gap-3 p-4">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                <Zap className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h3 className="font-semibold text-white">3초 내 답변</h3>
                <p className="text-sm text-text-secondary mt-1">
                  검색 없이, 영상 시청 없이 바로 핵심만
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                <Shield className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h3 className="font-semibold text-white">출처 기반 답변</h3>
                <p className="text-sm text-text-secondary mt-1">
                  Reddit, Wiki 등 검증된 데이터만 사용
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-4">
              <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                <MessageCircle className="w-5 h-5 text-accent" />
              </div>
              <div>
                <h3 className="font-semibold text-white">스포일러 컨트롤</h3>
                <p className="text-sm text-text-secondary mt-1">
                  원하는 만큼만 알려드려요
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Game Selection */}
      <section className="py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Gamepad2 className="w-6 h-6 text-accent" />
            어떤 게임에서 막히셨나요?
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {games.map((game) => (
              <GameCard key={game.id} game={game} />
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-border">
        <div className="max-w-4xl mx-auto text-center text-text-secondary text-sm">
          <p>BossHelp - 커뮤니티 데이터 기반 AI 게임 도우미</p>
          <p className="mt-1">Reddit, Wiki 등의 출처를 항상 표시합니다</p>
        </div>
      </footer>
    </main>
  );
}
