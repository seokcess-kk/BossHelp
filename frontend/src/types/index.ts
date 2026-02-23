// Game Types
export interface Game {
  id: string;
  title: string;
  genre: 'soulslike' | 'metroidvania' | 'action_rpg';
  thumbnailUrl?: string;
  isActive: boolean;
}

// Chat Types
export type SpoilerLevel = 'none' | 'light' | 'heavy';

export type Category =
  | 'boss_guide'
  | 'build_guide'
  | 'progression_route'
  | 'npc_quest'
  | 'item_location'
  | 'mechanic_tip'
  | 'secret_hidden';

export interface Source {
  url: string;
  title: string;
  sourceType: 'reddit' | 'wiki' | 'steam';
  qualityScore: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  hasDetail?: boolean;
  conversationId?: string;
  gameId?: string;
  isLoading?: boolean;
  isExpanded?: boolean;
  timestamp: Date;
}

// API Types
export interface AskRequest {
  game_id: string;
  question: string;
  spoiler_level: SpoilerLevel;
  session_id: string;
  category?: Category;
  expand?: boolean;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
  conversation_id: string;
  has_detail: boolean;
  is_early_data: boolean;
  latency_ms: number;
}

export interface FeedbackRequest {
  conversation_id: string;
  is_helpful: boolean;
}

export interface PopularQuestion {
  question: string;
  category: Category;
  askCount: number;
}
