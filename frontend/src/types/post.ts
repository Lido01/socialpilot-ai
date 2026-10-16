/**
 * Post, Media, Channel, and Publishing types
 */

export type PostStatus = 'draft' | 'in_review' | 'approved' | 'rejected' | 'scheduled' | 'published' | 'failed';

export interface LocalMediaItem {
  id: string;
  file?: File;
  previewUrl: string;
  name: string;
  size: number;
  type: string;
  caption?: string;
  order: number;
}

export interface TelegramChannel {
  id: string;
  title: string;
  username: string; // e.g. @socialpilot_ai
  telegramChatId: string;
  subscriberCount?: number;
  isConnected: boolean;
  botIsAdmin: boolean;
  createdAt: string;
}

export interface Post {
  id: string;
  companyId: string;
  caption: string;
  status: PostStatus;
  media: LocalMediaItem[];
  channelIds: string[];
  authorId: string;
  authorName: string;
  rejectionReason?: string;
  scheduledAt?: string;
  publishedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AICaptionPrompt {
  topic: string;
  tone: 'professional' | 'engaging' | 'casual' | 'promotional' | 'educational';
  targetAudience?: string;
  includeEmojis: boolean;
  includeHashtags: boolean;
  maxWords?: number;
}

export interface AICaptionResult {
  caption: string;
  suggestedHashtags: string[];
  suggestedEmojis: string[];
  mockNote?: string;
}
