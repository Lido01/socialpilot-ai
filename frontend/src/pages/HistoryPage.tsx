import React from 'react';
import { useNavigate } from 'react-router-dom';
import { mockService } from '@/api/mock.service';
import { Post } from '@/types/post';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { EmptyState } from '@/components/common/StateView';
import { Send, Eye, Copy, Calendar } from 'lucide-react';
import { useToast } from '@/context/ToastContext';

export const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const publishedPosts = mockService
    .getPosts()
    .filter((p) => p.status === 'published');

  const handleDuplicate = (post: Post) => {
    mockService.savePost({
      companyId: post.companyId,
      caption: post.caption,
      status: 'draft',
      media: post.media,
      channelIds: post.channelIds,
      authorId: post.authorId,
      authorName: post.authorName,
    });
    showToast('Post duplicated as new draft', 'success');
    navigate('/drafts');
  };

  return (
    <div className="space-y-4 pb-8">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Publishing History</h1>
        <p className="text-xs text-slate-500">
          Archive of posts delivered to your connected Telegram channels
        </p>
      </div>

      {publishedPosts.length === 0 ? (
        <EmptyState
          icon={<Send className="w-6 h-6 text-slate-400" />}
          title="No published posts yet"
          description="When your team publishes posts to Telegram channels, they will be archived here."
          actionText="Create First Post"
          onAction={() => navigate('/create-post')}
        />
      ) : (
        <div className="space-y-3">
          {publishedPosts.map((post) => (
            <Card key={post.id} className="p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>
                    {post.publishedAt
                      ? new Date(post.publishedAt).toLocaleString()
                      : new Date(post.updatedAt).toLocaleString()}
                  </span>
                </div>
                <Badge type="published" />
              </div>

              {/* Media Thumbnail */}
              {post.media.length > 0 && (
                <div className="rounded-xl overflow-hidden aspect-video max-h-44 bg-slate-100 border border-slate-200">
                  <img
                    src={post.media[0].previewUrl}
                    alt="Media preview"
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              {/* Caption */}
              <p className="text-xs text-slate-800 whitespace-pre-line leading-relaxed">
                {post.caption}
              </p>

              {/* Channel and actions footer */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                <div className="flex items-center gap-1 text-[11px] text-slate-500 font-mono">
                  <span>@socialpilot_ai</span>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDuplicate(post)}
                    icon={<Copy className="w-3.5 h-3.5" />}
                  >
                    Duplicate
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => navigate(`/posts/${post.id}/preview`)}
                    icon={<Eye className="w-3.5 h-3.5" />}
                  >
                    View
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
