/**
 * Development Mock Service
 * Used STRICTLY when running in Dev Mode for features whose backend endpoints
 * are not yet implemented (Posts, Channels, Teams, AI generation).
 * All data returned here is explicitly labeled as mock/development preview data.
 */

import { Post, TelegramChannel, TeamMember, AICaptionPrompt, AICaptionResult } from '@/types';

const INITIAL_CHANNELS: TelegramChannel[] = [
  {
    id: 'chan-1',
    title: 'SocialPilot AI Official',
    username: '@socialpilot_ai',
    telegramChatId: '-10022446688',
    subscriberCount: 1420,
    isConnected: true,
    botIsAdmin: true,
    createdAt: new Date().toISOString(),
  },
  {
    id: 'chan-2',
    title: 'Tech & AI Insights Daily',
    username: '@tech_ai_insights',
    telegramChatId: '-10033557799',
    subscriberCount: 890,
    isConnected: true,
    botIsAdmin: true,
    createdAt: new Date(Date.now() - 86400000 * 3).toISOString(),
  },
];

const INITIAL_TEAM: TeamMember[] = [
  {
    id: 'member-1',
    userId: 'u-1',
    displayName: 'Alex Rivers',
    username: 'alex_rivers',
    telegramId: 5298799880,
    role: 'company_admin',
    isActive: true,
    joinedAt: new Date(Date.now() - 86400000 * 10).toISOString(),
  },
  {
    id: 'member-2',
    userId: 'u-2',
    displayName: 'Jordan Lee',
    username: 'jordan_social',
    telegramId: 123456789,
    role: 'content_owner',
    isActive: true,
    joinedAt: new Date(Date.now() - 86400000 * 4).toISOString(),
  },
];

const INITIAL_POSTS: Post[] = [
  {
    id: 'post-1',
    companyId: 'company-demo-1',
    caption: '🚀 Excited to announce our new AI-powered Telegram publishing engine! Schedule, review, and auto-post directly from your mobile Mini App.\n\n#SocialPilot #AI #TelegramMiniApps #SaaS',
    status: 'published',
    media: [
      {
        id: 'm-1',
        previewUrl: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=80',
        name: 'ai_launch_banner.png',
        size: 245000,
        type: 'image/png',
        order: 0,
      },
    ],
    channelIds: ['chan-1'],
    authorId: 'u-1',
    authorName: 'Alex Rivers',
    publishedAt: new Date(Date.now() - 3600000 * 4).toISOString(),
    createdAt: new Date(Date.now() - 3600000 * 12).toISOString(),
    updatedAt: new Date(Date.now() - 3600000 * 4).toISOString(),
  },
  {
    id: 'post-2',
    companyId: 'company-demo-1',
    caption: '📊 5 tips to boost Telegram channel engagement:\n\n1. Consistent publishing schedule\n2. High-value visuals\n3. Interactive polls\n4. Clear calls-to-action\n5. Community discussions\n\nWhich one has worked best for you?',
    status: 'in_review',
    media: [],
    channelIds: ['chan-1', 'chan-2'],
    authorId: 'u-2',
    authorName: 'Jordan Lee',
    createdAt: new Date(Date.now() - 3600000 * 2).toISOString(),
    updatedAt: new Date(Date.now() - 3600000 * 2).toISOString(),
  },
  {
    id: 'post-3',
    companyId: 'company-demo-1',
    caption: 'Drafting announcement for weekend giveaway: Stay tuned for 3 months free SocialPilot Pro access! Details coming soon.',
    status: 'draft',
    media: [],
    channelIds: ['chan-1'],
    authorId: 'u-2',
    authorName: 'Jordan Lee',
    createdAt: new Date(Date.now() - 3600000 * 24).toISOString(),
    updatedAt: new Date(Date.now() - 3600000 * 20).toISOString(),
  },
];

class MockStore {
  private posts: Post[];
  private channels: TelegramChannel[];
  private team: TeamMember[];

  constructor() {
    this.posts = [...INITIAL_POSTS];
    this.channels = [...INITIAL_CHANNELS];
    this.team = [...INITIAL_TEAM];
  }

  getPosts(): Post[] {
    return [...this.posts];
  }

  getPostById(id: string): Post | undefined {
    return this.posts.find((p) => p.id === id);
  }

  savePost(post: Omit<Post, 'id' | 'createdAt' | 'updatedAt'> & { id?: string }): Post {
    if (post.id) {
      const idx = this.posts.findIndex((p) => p.id === post.id);
      if (idx >= 0) {
        const updated: Post = {
          ...this.posts[idx],
          ...post,
          updatedAt: new Date().toISOString(),
        };
        this.posts[idx] = updated;
        return updated;
      }
    }
    const newPost: Post = {
      ...post,
      id: `post-${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.posts.unshift(newPost);
    return newPost;
  }

  updatePostStatus(id: string, status: Post['status'], rejectionReason?: string): Post | null {
    const post = this.posts.find((p) => p.id === id);
    if (!post) return null;
    post.status = status;
    if (rejectionReason) post.rejectionReason = rejectionReason;
    if (status === 'published') post.publishedAt = new Date().toISOString();
    post.updatedAt = new Date().toISOString();
    return { ...post };
  }

  deletePost(id: string): boolean {
    const lenBefore = this.posts.length;
    this.posts = this.posts.filter((p) => p.id !== id);
    return this.posts.length < lenBefore;
  }

  getChannels(): TelegramChannel[] {
    return [...this.channels];
  }

  addChannel(title: string, username: string, telegramChatId: string): TelegramChannel {
    const newChan: TelegramChannel = {
      id: `chan-${Date.now()}`,
      title,
      username: username.startsWith('@') ? username : `@${username}`,
      telegramChatId,
      subscriberCount: 0,
      isConnected: true,
      botIsAdmin: true,
      createdAt: new Date().toISOString(),
    };
    this.channels.push(newChan);
    return newChan;
  }

  getTeam(): TeamMember[] {
    return [...this.team];
  }

  inviteMember(displayName: string, telegramId: number, role: 'company_admin' | 'content_owner'): TeamMember {
    const newMember: TeamMember = {
      id: `member-${Date.now()}`,
      userId: `u-${Date.now()}`,
      displayName,
      telegramId,
      role,
      isActive: true,
      joinedAt: new Date().toISOString(),
    };
    this.team.push(newMember);
    return newMember;
  }

  /**
   * AI caption generation simulation for development preview.
   * Explicitly flagged as simulated.
   */
  generateAICaption(prompt: AICaptionPrompt): AICaptionResult {
    const toneEmojis: Record<string, string[]> = {
      professional: ['💼', '📈', '🚀', '✨'],
      engaging: ['🔥', '💡', '🎉', '👇'],
      casual: ['☕', '👋', '🌟', '👀'],
      promotional: ['⚡', '🎁', '📣', '💥'],
      educational: ['📚', '🧠', '🔍', '💡'],
    };

    const emojis = toneEmojis[prompt.tone] || ['✨'];
    const emojiStr = prompt.includeEmojis ? ` ${emojis[0]} ${emojis[1] || ''}` : '';

    const hashtags = prompt.includeHashtags
      ? [
          `#${prompt.topic.replace(/[^a-zA-Z0-9]/g, '')}`,
          '#SocialPilot',
          '#TelegramGrowth',
          `#${prompt.tone.toUpperCase()}`,
        ]
      : [];

    return {
      caption: `🚀 ${prompt.topic.toUpperCase()}\n\nHere is an engaging insight crafted in a ${prompt.tone} tone for ${prompt.targetAudience || 'our Telegram community'}.${emojiStr}\n\nKey takeaway: Deliver consistent, quality updates that spark immediate discussion and connection.\n\n${hashtags.join(' ')}`,
      suggestedHashtags: hashtags,
      suggestedEmojis: emojis,
      mockNote: 'Simulated preview — real AI generation will connect to backend endpoint when /api/v1/companies/{id}/ai/generate is deployed.',
    };
  }
}

export const mockService = new MockStore();
