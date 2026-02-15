'use client';

import { cn } from '@/lib/utils';
import type { Message } from '@/types';
import { SourceCard } from './SourceCard';
import { FeedbackButtons } from './FeedbackButtons';
import { Button } from '@/components/ui/Button';
import { User, Bot, ChevronDown } from 'lucide-react';
import { useState } from 'react';

interface MessageBubbleProps {
  message: Message;
  onExpand?: (conversationId: string) => void;
}

export function MessageBubble({ message, onExpand }: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-accent' : 'bg-surface-hover'
        )}
      >
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-accent" />}
      </div>

      {/* Content */}
      <div className={cn('flex-1 max-w-[80%] space-y-2', isUser && 'flex flex-col items-end')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-3',
            isUser ? 'bg-accent text-white rounded-tr-sm' : 'bg-surface border border-border text-white rounded-tl-sm'
          )}
        >
          {message.isLoading ? (
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm text-text-secondary">답변 생성 중...</span>
            </div>
          ) : (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          )}
        </div>

        {/* AI Message Actions */}
        {!isUser && !message.isLoading && (
          <div className="space-y-2">
            {/* Sources Toggle */}
            {message.sources && message.sources.length > 0 && (
              <div>
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="flex items-center gap-1 text-sm text-text-secondary hover:text-white transition-colors"
                >
                  <span>출처 {message.sources.length}개</span>
                  <ChevronDown className={cn('w-4 h-4 transition-transform', showSources && 'rotate-180')} />
                </button>

                {showSources && (
                  <div className="mt-2 space-y-2">
                    {message.sources.map((source, index) => (
                      <SourceCard key={index} source={source} />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Expand Button */}
            {message.hasDetail && onExpand && message.conversationId && (
              <Button variant="outline" size="sm" onClick={() => onExpand(message.conversationId!)}>
                더 자세히
              </Button>
            )}

            {/* Feedback */}
            {message.conversationId && <FeedbackButtons conversationId={message.conversationId} />}
          </div>
        )}
      </div>
    </div>
  );
}
