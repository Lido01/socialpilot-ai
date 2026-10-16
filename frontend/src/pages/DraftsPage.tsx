import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { mockService } from '@/api/mock.service';
import { useToast } from '@/context/ToastContext';
import { Post } from '@/types/post';
import { Card } from '@/components/common/Card';
import { Badge } from '@/components/common/Badge';
import { Button } from '@/components/common/Button';
import { EmptyState } from '@/components/common/StateView';
import {
  Trash2,
  PenTool,
  ArrowRight,
} from 'lucide-react';

export const DraftsPage: React.FC = () => {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [filter, setFilter] = useState<string>('all');
  const [posts, setPosts] = useState<Post[]>(() => mockService.getPosts());

  const filteredPosts = posts.filter((p) => {
    if (filter === 'all') return true;
    return p.status === filter;
  });

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    mockService.deletePost(id);
    setPosts(mockService.getPosts());
    showToast('Post removed', 'info');
  };

  const filterTabs: Array<{ id: string; label: string }> = [
    { id: 'all', label: 'All' },
    { id: 'draft', label: 'Drafts' },
    { id: 'in_review', label: 'In Review' },
    { id: 'approved', label: 'Approved' },
    { id: 'published', label: 'Published' },
  ];

  return (
    <div className="space-y-4 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Posts & Drafts</h1>
          <p className="text-xs text-slate-500">Track and manage your content lifecycle</p>
        </div>
        <Button
          size="sm"
          onClick={() => navigate('/create-post')}
          icon={<PenTool className="w-3.5 h-3.5" />}
        >
          New Post
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        {filterTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id)}
            className={`text-xs px-3 py-1.5 rounded-full border whitespace-nowrap transition-all font-medium ${
              filter === tab.id
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Posts List */}
      {filteredPosts.length === 0 ? (
        <EmptyState
          title="No posts found"
          description={
            filter === 'all'
              ? 'You have not created any posts yet. Start by creating your first post!'
              : `No posts with status "${filter}".`
          }
          actionText="Create Post"
          onAction={() => navigate('/create-post')}
        />
      ) : (
        <div className="space-y-2.5">
          {filteredPosts.map((post) => (
            <Card
              key={post.id}
              onClick={() => navigate(`/posts/${post.id}/preview`)}
              hoverEffect
              className="p-4 space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="font-semibold text-slate-700">{post.authorName}</span>
                  <span>•</span>
                  <span>{new Date(post.updatedAt).toLocaleDateString()}</span>
                </div>
                <Badge type={post.status} />
              </div>

              <div className="flex gap-3">
                {post.media.length > 0 && (
                  <div className="w-16 h-16 rounded-xl overflow-hidden shrink-0 border border-slate-100 bg-slate-50">
                    <img
                      src={post.media[0].previewUrl}
                      alt="Thumbnail"
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-slate-800 line-clamp-3 leading-relaxed">
                    {post.caption || '(No caption text)'}
                  </p>
                </div>
              </div>

              {post.rejectionReason && (
                <div className="p-2 bg-rose-50 rounded-lg text-[11px] text-rose-700">
                  <b>Feedback:</b> {post.rejectionReason}
                </div>
              )}

              <div className="flex items-center justify-between pt-2 border-t border-slate-50 text-xs">
                <span className="text-[11px] text-slate-400">
                  {post.channelIds.length} channel(s) selected
                </span>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={(e) => handleDelete(e, post.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors rounded-lg"
                    title="Delete post"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <span className="text-indigo-600 font-semibold text-xs flex items-center gap-1">
                    <span>Preview</span>
                    <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
