'use client';

import { useEffect, useRef } from 'react';
import { useChatStore } from '@/stores/chat-store';
import { MessageBubble } from './MessageBubble';
import { QuestionInput } from './QuestionInput';
import { Sidebar } from '@/components/layout/Sidebar';
import { MessageCircle } from 'lucide-react';

interface ChatContainerProps {
  gameId: string;
  gameTitle: string;
}

export function ChatContainer({ gameId, gameTitle }: ChatContainerProps) {
  const { messages, expandAnswer, clearChat } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Clear chat when game changes
  useEffect(() => {
    clearChat();
  }, [gameId, clearChat]);

  return (
    <div className="flex flex-col h-[calc(100vh-56px)]">
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - Desktop */}
        <Sidebar />

        {/* Chat Area */}
        <main className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 rounded-full bg-accent/10 flex items-center justify-center mb-4">
                  <MessageCircle className="w-8 h-8 text-accent" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">
                  {gameTitle}에서 막히셨나요?
                </h2>
                <p className="text-text-secondary max-w-md">
                  보스 공략, 빌드 추천, 아이템 위치 등 무엇이든 물어보세요.
                  <br />
                  3초 안에 정확한 답변을 드릴게요!
                </p>
              </div>
            ) : (
              <div className="max-w-3xl mx-auto space-y-4">
                {messages.map((message) => (
                  <MessageBubble key={message.id} message={message} onExpand={expandAnswer} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input */}
          <QuestionInput gameId={gameId} />
        </main>
      </div>
    </div>
  );
}
