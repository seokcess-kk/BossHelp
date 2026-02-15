'use client';

import { useCallback, useMemo } from 'react';
import { useChatStore } from '@/stores/chat-store';
import type { Message, SpoilerLevel, Category } from '@/types';

/**
 * useChat - Chat state and streaming hook
 *
 * Provides access to chat state and actions for sending messages,
 * managing spoiler levels, and handling feedback.
 *
 * @param gameId - The game ID for the chat context
 */
export function useChat(gameId: string) {
  const {
    messages,
    isLoading,
    spoilerLevel,
    category,
    sessionId,
    error,
    sendMessage: storeSendMessage,
    expandAnswer: storeExpandAnswer,
    submitFeedback: storeSubmitFeedback,
    setSpoilerLevel,
    setCategory,
    clearChat,
    clearError,
  } = useChatStore();

  // Memoized send message with gameId bound
  const sendMessage = useCallback(
    async (question: string) => {
      await storeSendMessage(gameId, question);
    },
    [gameId, storeSendMessage]
  );

  // Expand answer for a specific conversation
  const expandAnswer = useCallback(
    async (conversationId: string) => {
      await storeExpandAnswer(conversationId);
    },
    [storeExpandAnswer]
  );

  // Submit feedback for a conversation
  const submitFeedback = useCallback(
    async (conversationId: string, isHelpful: boolean) => {
      await storeSubmitFeedback(conversationId, isHelpful);
    },
    [storeSubmitFeedback]
  );

  // Get the last assistant message
  const lastAssistantMessage = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === 'assistant') {
        return messages[i];
      }
    }
    return null;
  }, [messages]);

  // Check if chat has messages
  const hasMessages = messages.length > 0;

  // Check if the last message can be expanded
  const canExpand = lastAssistantMessage?.hasDetail ?? false;

  return {
    // State
    messages,
    isLoading,
    spoilerLevel,
    category,
    sessionId,
    error,
    hasMessages,
    canExpand,
    lastAssistantMessage,

    // Actions
    sendMessage,
    expandAnswer,
    submitFeedback,
    setSpoilerLevel,
    setCategory,
    clearChat,
    clearError,
  };
}

/**
 * useChatMessages - Subscribe to chat messages only
 *
 * Lighter weight hook for components that only need to display messages.
 */
export function useChatMessages() {
  const messages = useChatStore((state) => state.messages);
  const isLoading = useChatStore((state) => state.isLoading);

  return { messages, isLoading };
}

/**
 * useSpoilerLevel - Subscribe to spoiler level only
 *
 * For components that only need spoiler level state.
 */
export function useSpoilerLevel() {
  const spoilerLevel = useChatStore((state) => state.spoilerLevel);
  const setSpoilerLevel = useChatStore((state) => state.setSpoilerLevel);

  return { spoilerLevel, setSpoilerLevel };
}

export default useChat;
