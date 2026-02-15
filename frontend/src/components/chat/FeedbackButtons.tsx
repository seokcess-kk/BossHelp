'use client';

import { useState } from 'react';
import { useChatStore } from '@/stores/chat-store';
import { cn } from '@/lib/utils';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

interface FeedbackButtonsProps {
  conversationId: string;
}

export function FeedbackButtons({ conversationId }: FeedbackButtonsProps) {
  const { submitFeedback } = useChatStore();
  const [feedback, setFeedback] = useState<'helpful' | 'not_helpful' | null>(null);

  const handleFeedback = async (isHelpful: boolean) => {
    const newFeedback = isHelpful ? 'helpful' : 'not_helpful';
    setFeedback(newFeedback);
    await submitFeedback(conversationId, isHelpful);
  };

  if (feedback) {
    return (
      <div className="flex items-center gap-2 text-sm text-text-secondary">
        <span>피드백 감사합니다!</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-text-secondary">도움이 되었나요?</span>
      <button
        onClick={() => handleFeedback(true)}
        className={cn(
          'p-1.5 rounded-lg border border-border hover:border-green-500/50 hover:bg-green-500/10',
          'transition-colors group'
        )}
        title="도움됨"
      >
        <ThumbsUp className="w-4 h-4 text-text-secondary group-hover:text-green-400" />
      </button>
      <button
        onClick={() => handleFeedback(false)}
        className={cn(
          'p-1.5 rounded-lg border border-border hover:border-red-500/50 hover:bg-red-500/10',
          'transition-colors group'
        )}
        title="도움안됨"
      >
        <ThumbsDown className="w-4 h-4 text-text-secondary group-hover:text-red-400" />
      </button>
    </div>
  );
}
