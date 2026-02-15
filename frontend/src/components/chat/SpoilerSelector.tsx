'use client';

import { useChatStore } from '@/stores/chat-store';
import { cn } from '@/lib/utils';
import { Eye, EyeOff, AlertTriangle } from 'lucide-react';
import type { SpoilerLevel } from '@/types';

const spoilerOptions: { level: SpoilerLevel; label: string; description: string; icon: typeof Eye }[] = [
  {
    level: 'none',
    label: '스포 없음',
    description: '스토리 언급 없이 순수 공략만',
    icon: EyeOff,
  },
  {
    level: 'light',
    label: '가벼운 스포',
    description: '보스명, 기본 세계관 언급',
    icon: Eye,
  },
  {
    level: 'heavy',
    label: '모든 정보',
    description: '스토리 포함 전체 정보',
    icon: AlertTriangle,
  },
];

export function SpoilerSelector() {
  const { spoilerLevel, setSpoilerLevel } = useChatStore();

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-text-secondary">스포일러 레벨</label>
      <div className="flex flex-col gap-2">
        {spoilerOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = spoilerLevel === option.level;

          return (
            <button
              key={option.level}
              onClick={() => setSpoilerLevel(option.level)}
              className={cn(
                'flex items-center gap-3 p-3 rounded-lg border transition-colors text-left',
                isSelected
                  ? 'border-accent bg-accent/10 text-white'
                  : 'border-border hover:border-accent/50 text-text-secondary hover:text-white'
              )}
            >
              <Icon className={cn('w-5 h-5', isSelected ? 'text-accent' : 'text-text-secondary')} />
              <div>
                <div className="font-medium">{option.label}</div>
                <div className="text-xs text-text-secondary">{option.description}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
