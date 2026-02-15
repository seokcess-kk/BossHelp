import { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { MessageCircle, Swords, Bug, Gamepad2 } from 'lucide-react';

// Game data for SSG
const GAMES = {
  'elden-ring': {
    id: 'elden-ring',
    title: 'Elden Ring',
    genre: 'soulslike',
    description: '프롬소프트웨어의 오픈월드 액션 RPG. 어둠의 소울 시리즈의 정신적 후속작.',
    popularQuestions: [
      '말레니아 어떻게 깸?',
      '출혈 빌드 추천해줘',
      '라니 퀘스트 순서',
      '마르기트 공략',
      '최강 무기 추천',
    ],
  },
  'sekiro': {
    id: 'sekiro',
    title: 'Sekiro: Shadows Die Twice',
    genre: 'soulslike',
    description: '일본 전국시대를 배경으로 한 액션 어드벤처. 튕겨내기 메카닉이 핵심.',
    popularQuestions: [
      '겐이치로 어떻게 깸?',
      '튕겨내기 타이밍',
      '번개 반사 방법',
      '이신 검성 공략',
      '보스 순서 추천',
    ],
  },
  'hollow-knight': {
    id: 'hollow-knight',
    title: 'Hollow Knight',
    genre: 'metroidvania',
    description: '수상 경력의 2D 메트로이드바니아. 광활한 지하 왕국을 탐험하세요.',
    popularQuestions: [
      '레이디언스 공략',
      '최고의 참 조합',
      '숨겨진 지역 찾기',
      '그림 트루프 엔딩',
      '초반 루트 추천',
    ],
  },
  'silksong': {
    id: 'silksong',
    title: 'Hollow Knight: Silksong',
    genre: 'metroidvania',
    description: 'Hollow Knight의 후속작. 호넷을 주인공으로 새로운 왕국을 탐험합니다.',
    popularQuestions: [
      '출시일 정보',
      '호넷 기술 목록',
      '새로운 적 정보',
      '맵 구조 예상',
      '전작과의 차이점',
    ],
  },
  'lies-of-p': {
    id: 'lies-of-p',
    title: 'Lies of P',
    genre: 'soulslike',
    description: '피노키오를 모티브로 한 소울라이크. 아름다운 벨에포크 시대 배경.',
    popularQuestions: [
      '퍼레이드 마스터 공략',
      '최강 무기 조합',
      '인간성 시스템',
      '숨겨진 보스',
      '엔딩 분기 조건',
    ],
  },
};

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

interface PageProps {
  params: Promise<{ gameId: string }>;
}

export async function generateStaticParams() {
  return Object.keys(GAMES).map((gameId) => ({ gameId }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { gameId } = await params;
  const game = GAMES[gameId as keyof typeof GAMES];

  if (!game) {
    return { title: 'Game Not Found - BossHelp' };
  }

  return {
    title: `${game.title} 공략 - BossHelp`,
    description: `${game.title} 공략, 보스 가이드, 빌드 추천. ${game.description}`,
    keywords: [game.title, '공략', '가이드', '보스', genreLabels[game.genre as keyof typeof genreLabels]],
  };
}

export default async function GamePage({ params }: PageProps) {
  const { gameId } = await params;
  const game = GAMES[gameId as keyof typeof GAMES];

  if (!game) {
    notFound();
  }

  const Icon = genreIcons[game.genre as keyof typeof genreIcons];

  return (
    <main className="min-h-[calc(100vh-56px)] py-12 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-start gap-6 mb-8">
          <div className="w-20 h-20 rounded-xl bg-accent/10 flex items-center justify-center flex-shrink-0">
            <Icon className="w-10 h-10 text-accent" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">{game.title}</h1>
            <Badge variant="accent" className="mb-3">
              {genreLabels[game.genre as keyof typeof genreLabels]}
            </Badge>
            <p className="text-text-secondary">{game.description}</p>
          </div>
        </div>

        {/* CTA */}
        <Card className="mb-8 p-6 bg-gradient-to-r from-accent/10 to-transparent border-accent/30">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-white mb-1">
                {game.title}에서 막히셨나요?
              </h2>
              <p className="text-text-secondary">AI에게 물어보세요. 3초 안에 답변드립니다.</p>
            </div>
            <Link href={`/chat/${game.id}`}>
              <Button size="lg">
                <MessageCircle className="w-5 h-5 mr-2" />
                질문하기
              </Button>
            </Link>
          </div>
        </Card>

        {/* Popular Questions */}
        <section>
          <h2 className="text-xl font-semibold text-white mb-4">인기 질문</h2>
          <div className="grid gap-3">
            {game.popularQuestions.map((question, index) => (
              <Link key={index} href={`/chat/${game.id}?q=${encodeURIComponent(question)}`}>
                <Card variant="interactive" className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center text-accent font-semibold text-sm">
                      {index + 1}
                    </div>
                    <span className="text-white">{question}</span>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </section>

        {/* Categories */}
        <section className="mt-8">
          <h2 className="text-xl font-semibold text-white mb-4">카테고리</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {[
              { label: '보스 공략', category: 'boss_guide' },
              { label: '빌드 가이드', category: 'build_guide' },
              { label: '진행 순서', category: 'progression_route' },
              { label: 'NPC 퀘스트', category: 'npc_quest' },
              { label: '아이템 위치', category: 'item_location' },
              { label: '메카닉 팁', category: 'mechanic_tip' },
            ].map((cat) => (
              <Link
                key={cat.category}
                href={`/chat/${game.id}?category=${cat.category}`}
              >
                <Card variant="interactive" className="p-4 text-center">
                  <span className="text-white">{cat.label}</span>
                </Card>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
