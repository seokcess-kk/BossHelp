import { create } from 'zustand';
import type { Message, SpoilerLevel, Category, Source } from '@/types';
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
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      // For development, add mock response
      const mockSources: Source[] = [
        {
          url: 'https://reddit.com/r/Eldenring/example',
          title: 'Boss Guide - Community Tips',
          sourceType: 'reddit',
          qualityScore: 0.85,
        },
      ];

      const mockMessage: Message = {
        id: `msg_${Date.now()}_ai`,
        role: 'assistant',
        content: `[개발 모드] "${question}"에 대한 답변입니다.\n\n아직 백엔드가 연결되지 않았습니다. 실제 서비스에서는 RAG 기반의 정확한 답변이 제공됩니다.`,
        sources: mockSources,
        hasDetail: true,
        conversationId: `conv_${Date.now()}`,
        timestamp: new Date(),
      };

      set((state) => ({
        messages: [...state.messages, mockMessage],
        isLoading: false,
        error: null,
      }));
    }
  },

  expandAnswer: async (conversationId: string) => {
    // TODO: Implement expand answer
    console.log('Expanding answer for:', conversationId);
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
