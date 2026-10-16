import React, { useState } from 'react';
import { mockService } from '@/api/mock.service';
import { useToast } from '@/context/ToastContext';
import { Post } from '@/types/post';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { EmptyState } from '@/components/common/StateView';
import { CheckCircle2, XCircle, Send } from 'lucide-react';

export const ApprovalsPage: React.FC = () => {
  const { showToast } = useToast();

  const [pendingPosts, setPendingPosts] = useState<Post[]>(() =>
    mockService.getPosts().filter((p) => p.status === 'in_review')
  );
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const refreshList = () => {
    setPendingPosts(mockService.getPosts().filter((p) => p.status === 'in_review'));
  };

  const handleApprove = (id: string) => {
    mockService.updatePostStatus(id, 'approved');
    showToast('Post approved and added to ready queue', 'success');
    refreshList();
  };

  const handlePublishDirectly = (id: string) => {
    mockService.updatePostStatus(id, 'published');
    showToast('Post approved and published to Telegram channels!', 'success');
    refreshList();
  };

  const handleRejectSubmit = (id: string) => {
    if (!rejectionReason.trim()) {
      showToast('Please provide feedback for rejection', 'warning');
      return;
    }

    mockService.updatePostStatus(id, 'rejected', rejectionReason.trim());
    showToast('Post returned to creator with revision notes', 'info');
    setRejectingId(null);
    setRejectionReason('');
    refreshList();
  };

  return (
    <div className="space-y-4 pb-8">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Approval Queue</h1>
        <p className="text-xs text-slate-500">
          Review posts submitted by Content Creators before publishing
        </p>
      </div>

      {pendingPosts.length === 0 ? (
        <EmptyState
          icon={<CheckCircle2 className="w-6 h-6 text-emerald-600" />}
          title="All caught up!"
          description="There are currently no posts waiting for your review. When team creators submit posts, they will appear here."
        />
      ) : (
        <div className="space-y-3">
          {pendingPosts.map((post) => (
            <Card key={post.id} className="p-4 space-y-3.5">
              <div className="flex items-center justify-between">
                <div className="text-xs">
                  <span className="font-bold text-slate-900">{post.authorName}</span>
                  <span className="text-slate-400"> submitted • </span>
                  <span className="text-slate-500">
                    {new Date(post.createdAt).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <Badge type="in_review" />
              </div>

              {/* Media Thumbnails */}
              {post.media.length > 0 && (
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {post.media.map((m, idx) => (
                    <img
                      key={m.id}
                      src={m.previewUrl}
                      alt={`Media ${idx + 1}`}
                      className="w-20 h-20 rounded-xl object-cover shrink-0 border border-slate-200"
                    />
                  ))}
                </div>
              )}

              {/* Caption */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs text-slate-800 leading-relaxed whitespace-pre-line">
                {post.caption}
              </div>

              {/* Rejection Form Input */}
              {rejectingId === post.id ? (
                <div className="p-3 bg-rose-50 rounded-xl border border-rose-200 space-y-2">
                  <label className="text-xs font-semibold text-rose-900 block">
                    Revision Feedback for Creator:
                  </label>
                  <textarea
                    rows={2}
                    className="w-full text-xs p-2 rounded-lg border border-rose-300 bg-white"
                    placeholder="e.g. Please update hashtags and remove the outdated discount link..."
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                  />
                  <div className="flex justify-end gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setRejectingId(null);
                        setRejectionReason('');
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => handleRejectSubmit(post.id)}
                    >
                      Confirm Rejection
                    </Button>
                  </div>
                </div>
              ) : (
                /* Action Buttons */
                <div className="grid grid-cols-3 gap-2 pt-1 border-t border-slate-100">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setRejectingId(post.id)}
                    icon={<XCircle className="w-3.5 h-3.5 text-rose-500" />}
                  >
                    Reject
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleApprove(post.id)}
                    icon={<CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handlePublishDirectly(post.id)}
                    icon={<Send className="w-3.5 h-3.5" />}
                  >
                    Publish
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
