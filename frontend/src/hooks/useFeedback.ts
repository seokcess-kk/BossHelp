'use client';

import { useState, useCallback } from 'react';
import { api } from '@/lib/api';

interface FeedbackState {
  isSubmitting: boolean;
  submitted: Record<string, 'helpful' | 'not_helpful'>;
  error: string | null;
}

/**
 * useFeedback - Feedback submission hook
 *
 * Handles submitting feedback for conversation answers and
 * tracks which conversations have received feedback.
 */
export function useFeedback() {
  const [state, setState] = useState<FeedbackState>({
    isSubmitting: false,
    submitted: {},
    error: null,
  });

  // Submit helpful feedback
  const submitHelpful = useCallback(async (conversationId: string) => {
    setState((prev) => ({
      ...prev,
      isSubmitting: true,
      error: null,
    }));

    try {
      await api.submitFeedback({
        conversation_id: conversationId,
        is_helpful: true,
      });

      setState((prev) => ({
        ...prev,
        isSubmitting: false,
        submitted: {
          ...prev.submitted,
          [conversationId]: 'helpful',
        },
      }));

      return true;
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isSubmitting: false,
        error: 'Failed to submit feedback',
      }));
      return false;
    }
  }, []);

  // Submit not helpful feedback
  const submitNotHelpful = useCallback(async (conversationId: string) => {
    setState((prev) => ({
      ...prev,
      isSubmitting: true,
      error: null,
    }));

    try {
      await api.submitFeedback({
        conversation_id: conversationId,
        is_helpful: false,
      });

      setState((prev) => ({
        ...prev,
        isSubmitting: false,
        submitted: {
          ...prev.submitted,
          [conversationId]: 'not_helpful',
        },
      }));

      return true;
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isSubmitting: false,
        error: 'Failed to submit feedback',
      }));
      return false;
    }
  }, []);

  // Generic submit feedback
  const submitFeedback = useCallback(
    async (conversationId: string, isHelpful: boolean) => {
      if (isHelpful) {
        return submitHelpful(conversationId);
      }
      return submitNotHelpful(conversationId);
    },
    [submitHelpful, submitNotHelpful]
  );

  // Check if feedback was submitted for a conversation
  const getFeedbackStatus = useCallback(
    (conversationId: string): 'helpful' | 'not_helpful' | null => {
      return state.submitted[conversationId] || null;
    },
    [state.submitted]
  );

  // Check if feedback was already submitted
  const hasFeedback = useCallback(
    (conversationId: string): boolean => {
      return conversationId in state.submitted;
    },
    [state.submitted]
  );

  // Clear error
  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  return {
    // State
    isSubmitting: state.isSubmitting,
    error: state.error,

    // Actions
    submitFeedback,
    submitHelpful,
    submitNotHelpful,
    getFeedbackStatus,
    hasFeedback,
    clearError,
  };
}

export default useFeedback;
