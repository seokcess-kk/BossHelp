'use client';

import { useChatStore } from '@/stores/chat-store';
import { cn } from '@/lib/utils';
import type { Category } from '@/types';
import { Swords, Wrench, Map, Users, Package, Lightbulb, Eye } from 'lucide-react';

interface CategoryOption {
  value: Category | null;
  label: string;
  icon: typeof Swords;
}

const categories: CategoryOption[] = [
  { value: null, label: '전체', icon: Eye },
  { value: 'boss_guide', label: '보스 공략', icon: Swords },
  { value: 'build_guide', label: '빌드 가이드', icon: Wrench },
  { value: 'progression_route', label: '진행 순서', icon: Map },
  { value: 'npc_quest', label: 'NPC 퀘스트', icon: Users },
  { value: 'item_location', label: '아이템 위치', icon: Package },
  { value: 'mechanic_tip', label: '메카닉 팁', icon: Lightbulb },
];

export function CategoryFilter() {
  const { category, setCategory } = useChatStore();

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-text-secondary">카테고리</label>
      <div className="flex flex-wrap gap-2">
        {categories.map((cat) => {
          const Icon = cat.icon;
          const isSelected = category === cat.value;

          return (
            <button
              key={cat.value ?? 'all'}
              onClick={() => setCategory(cat.value)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors',
                isSelected
                  ? 'bg-accent text-white'
                  : 'bg-surface border border-border text-text-secondary hover:text-white hover:border-accent/50'
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {cat.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
