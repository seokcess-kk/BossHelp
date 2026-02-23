'use client';

import { SpoilerSelector } from '@/components/chat/SpoilerSelector';
import { CategoryFilter } from '@/components/game/CategoryFilter';
import { cn } from '@/lib/utils';

interface SidebarProps {
  className?: string;
  showCategoryFilter?: boolean;
}

export function Sidebar({ className, showCategoryFilter = false }: SidebarProps) {
  return (
    <aside
      className={cn(
        'hidden lg:flex w-64 border-r border-border flex-col p-4 bg-surface/50',
        className
      )}
    >
      {/* Spoiler Control */}
      <SpoilerSelector />

      {/* Category Filter (optional) */}
      {showCategoryFilter && (
        <div className="mt-6">
          <CategoryFilter />
        </div>
      )}
    </aside>
  );
}
