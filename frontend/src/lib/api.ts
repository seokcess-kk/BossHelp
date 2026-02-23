import type { AskRequest, AskResponse, Game, FeedbackRequest, PopularQuestion } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Games
  async getGames(): Promise<{ games: Game[] }> {
    const response = await this.request<{ games: Array<{
      id: string;
      title: string;
      genre: 'soulslike' | 'metroidvania' | 'action_rpg';
      thumbnail_url?: string;
      is_active: boolean;
    }> }>('/api/v1/games');

    return {
      games: response.games.map((game) => ({
        id: game.id,
        title: game.title,
        genre: game.genre,
        thumbnailUrl: game.thumbnail_url,
        isActive: game.is_active,
      })),
    };
  }

  async getPopularQuestions(gameId: string): Promise<{ questions: PopularQuestion[] }> {
    return this.request(`/api/v1/games/${gameId}/popular`);
  }

  // Chat
  async ask(request: AskRequest): Promise<AskResponse> {
    return this.request('/api/v1/ask', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Feedback
  async submitFeedback(request: FeedbackRequest): Promise<{ success: boolean }> {
    return this.request('/api/v1/feedback', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

export const api = new ApiClient(API_URL);
