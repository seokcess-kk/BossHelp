'use client';

import { cn } from '@/lib/utils';
import type { Source } from '@/types';
import { ExternalLink } from 'lucide-react';

interface SourceCardProps {
  source: Source;
}

const sourceLabels = {
  reddit: 'Reddit',
  wiki: 'Wiki',
  steam: 'Steam',
};

const sourceColors = {
  reddit: 'text-orange-400',
  wiki: 'text-blue-400',
  steam: 'text-gray-400',
};

export function SourceCard({ source }: SourceCardProps) {
  const qualityPercent = Math.round(source.qualityScore * 100);

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        'flex items-center gap-3 p-3 rounded-lg border border-border',
        'bg-surface hover:bg-surface-hover transition-colors group'
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn('text-xs font-medium', sourceColors[source.sourceType])}>
            {sourceLabels[source.sourceType]}
          </span>
          <span className="text-xs text-text-secondary">신뢰도 {qualityPercent}%</span>
        </div>
        <p className="text-sm text-white truncate mt-1">{source.title}</p>
      </div>
      <ExternalLink className="w-4 h-4 text-text-secondary group-hover:text-accent flex-shrink-0" />
    </a>
  );
}
