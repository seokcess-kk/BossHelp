import { create } from 'zustand';
import type { Message, SpoilerLevel, Category } from '@/types';
import { generateSessionId } from '@/lib/utils';
import { api } from '@/lib/api';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  spoilerLevel: SpoilerLevel;
  category: Category | null;
  sessionId: string;
  error: string | null;

  // Actions
  sendMessage: (gameId: string, question: string) => Promise<void>;
  expandAnswer: (conversationId: string) => Promise<void>;
  submitFeedback: (conversationId: string, isHelpful: boolean) => Promise<void>;
  setSpoilerLevel: (level: SpoilerLevel) => void;
  setCategory: (category: Category | null) => void;
  clearChat: () => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  spoilerLevel: 'none',
  category: null,
  sessionId: generateSessionId(),
  error: null,

  sendMessage: async (gameId: string, question: string) => {
    const { spoilerLevel, category, sessionId } = get();

    // Add user message
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    try {
      const response = await api.ask({
        game_id: gameId,
        question,
        spoiler_level: spoilerLevel,
        session_id: sessionId,
        category: category || undefined,
      });

      const assistantMessage: Message = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        hasDetail: response.has_detail,
        conversationId: response.conversation_id,
        gameId: gameId,
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      console.error('Failed to send message:', error);
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : '답변 생성에 실패했습니다. 다시 시도해주세요.',
      });
    }
  },

  expandAnswer: async (conversationId: string) => {
    const { messages, spoilerLevel, sessionId } = get();

    // 해당 conversation의 메시지 찾기
    const targetMessage = messages.find(
      (m) => m.conversationId === conversationId && m.role === 'assistant'
    );

    if (!targetMessage) {
      console.error('Message not found for conversationId:', conversationId);
      return;
    }

    // 이전 user 메시지에서 gameId와 question 추출
    const targetIndex = messages.indexOf(targetMessage);
    const userMessage = messages
      .slice(0, targetIndex)
      .reverse()
      .find((m) => m.role === 'user');

    if (!userMessage) {
      console.error('User message not found');
      return;
    }

    set({ isLoading: true, error: null });

    try {
      // expand=true로 다시 요청
      const response = await api.ask({
        game_id: targetMessage.gameId || 'elden-ring',
        question: userMessage.content,
        spoiler_level: spoilerLevel,
        session_id: sessionId,
        expand: true,
      });

      // 기존 메시지 업데이트 (확장된 답변으로 교체)
      set((state) => ({
        messages: state.messages.map((m) =>
          m.conversationId === conversationId
            ? {
                ...m,
                content: response.answer,
                sources: response.sources,
                hasDetail: false, // 확장 후에는 더 이상 "더 자세히" 버튼 없음
                isExpanded: true,
              }
            : m
        ),
        isLoading: false,
      }));
    } catch (error) {
      console.error('Failed to expand answer:', error);
      set({
        isLoading: false,
        error: '답변 확장에 실패했습니다. 다시 시도해주세요.',
      });
    }
  },

  submitFeedback: async (conversationId: string, isHelpful: boolean) => {
    try {
      await api.submitFeedback({ conversation_id: conversationId, is_helpful: isHelpful });
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  },

  setSpoilerLevel: (level: SpoilerLevel) => {
    set({ spoilerLevel: level });
  },

  setCategory: (category: Category | null) => {
    set({ category });
  },

  clearChat: () => {
    set({
      messages: [],
      sessionId: generateSessionId(),
      error: null,
    });
  },

  clearError: () => {
    set({ error: null });
  },
}));
