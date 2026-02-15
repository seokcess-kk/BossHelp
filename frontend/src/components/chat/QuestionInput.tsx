'use client';

import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from 'react';
import { useChatStore } from '@/stores/chat-store';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { Send } from 'lucide-react';

interface QuestionInputProps {
  gameId: string;
}

export function QuestionInput({ gameId }: QuestionInputProps) {
  const [question, setQuestion] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, isLoading } = useChatStore();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [question]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    const trimmedQuestion = question.trim();
    setQuestion('');
    await sendMessage(gameId, trimmedQuestion);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-border bg-bg p-4">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="질문을 입력하세요... (예: 말레니아 어떻게 깸?)"
              className={cn(
                'w-full rounded-xl border border-border bg-surface px-4 py-3 text-sm text-white',
                'placeholder:text-text-secondary',
                'focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
                'resize-none min-h-[48px] max-h-[150px]'
              )}
              rows={1}
              disabled={isLoading}
            />
          </div>
          <Button type="submit" size="lg" isLoading={isLoading} disabled={!question.trim()}>
            <Send className="w-5 h-5" />
          </Button>
        </div>
        <p className="mt-2 text-xs text-text-secondary text-center">
          Enter로 전송, Shift+Enter로 줄바꿈
        </p>
      </div>
    </form>
  );
}
