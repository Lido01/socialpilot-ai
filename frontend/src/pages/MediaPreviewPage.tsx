import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { mockService } from '@/api/mock.service';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/context/ToastContext';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Textarea } from '@/components/common/Textarea';
import {
  Eye,
  Send,
  CheckCircle,
  XCircle,
  ArrowLeft,
} from 'lucide-react';

export const MediaPreviewPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { role } = useAuth();
  const { showToast } = useToast();

  const post = id ? mockService.getPostById(id) : mockService.getPosts()[0];

  const [isEditing, setIsEditing] = useState(false);
  const [editedCaption, setEditedCaption] = useState(post?.caption || '');

  if (!post) {
    return (
      <div className="py-12 text-center space-y-3">
        <p className="text-sm text-slate-500">Post not found</p>
        <Button size="sm" onClick={() => navigate('/drafts')}>
          Return to Drafts
        </Button>
      </div>
    );
  }

  const handleSaveEdit = () => {
    mockService.savePost({
      ...post,
      caption: editedCaption,
    });
    setIsEditing(false);
    showToast('Post updated successfully', 'success');
  };

  const handleApprove = () => {
    mockService.updatePostStatus(post.id, 'approved');
    showToast('Post approved!', 'success');
    navigate('/drafts');
  };

  const handlePublish = () => {
    mockService.updatePostStatus(post.id, 'published');
    showToast('Post published to Telegram channels!', 'success');
    navigate('/history');
  };

  return (
    <div className="space-y-4 pb-8">
      {/* Top Header Controls */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back</span>
        </button>
        <Badge type={post.status} />
      </div>

      {/* Telegram Message Simulation Mockup */}
      <div className="space-y-2">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block px-1">
          Telegram Channel Preview
        </span>

        <div className="bg-[#17212b] text-[#f5f5f5] rounded-3xl p-4 shadow-lg border border-slate-800 space-y-3 max-w-sm mx-auto">
          {/* Mock Channel Header */}
          <div className="flex items-center gap-2.5 pb-2 border-b border-white/10">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-sky-400 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
              SP
            </div>
            <div className="min-w-0">
              <div className="text-xs font-bold truncate">SocialPilot AI Channel</div>
              <div className="text-[10px] text-white/50">1,420 subscribers</div>
            </div>
          </div>

          {/* Media Container */}
          {post.media.length > 0 && (
            <div className="rounded-2xl overflow-hidden bg-black/40">
              {post.media.length === 1 ? (
                <img
                  src={post.media[0].previewUrl}
                  alt="Post attachment"
                  className="w-full max-h-72 object-cover"
                />
              ) : (
                <div className="grid grid-cols-2 gap-1">
                  {post.media.slice(0, 4).map((m, idx) => (
                    <img
                      key={m.id}
                      src={m.previewUrl}
                      alt={`Attachment ${idx + 1}`}
                      className="w-full h-32 object-cover"
                    />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Caption text */}
          <div className="text-xs leading-relaxed whitespace-pre-line text-white/90">
            {editedCaption}
          </div>

          {/* Telegram Timestamp & Views */}
          <div className="flex items-center justify-end gap-1.5 text-[10px] text-white/40 pt-1">
            <Eye className="w-3 h-3" />
            <span>1</span>
            <span>•</span>
            <span>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
        </div>
      </div>

      {/* Edit Controls */}
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-800">Post Details</span>
          <button
            onClick={() => setIsEditing(!isEditing)}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700"
          >
            {isEditing ? 'Cancel Edit' : 'Edit Caption'}
          </button>
        </div>

        {isEditing ? (
          <div className="space-y-2">
            <Textarea
              rows={4}
              value={editedCaption}
              onChange={(e) => setEditedCaption(e.target.value)}
            />
            <Button size="sm" onClick={handleSaveEdit} className="w-full">
              Save Changes
            </Button>
          </div>
        ) : (
          <div className="text-xs text-slate-500 space-y-1">
            <div>Author: <span className="font-medium text-slate-700">{post.authorName}</span></div>
            <div>Created: <span className="font-medium text-slate-700">{new Date(post.createdAt).toLocaleString()}</span></div>
            {post.rejectionReason && (
              <div className="p-2 bg-rose-50 text-rose-700 rounded-lg text-xs mt-2">
                <b>Rejection Feedback:</b> {post.rejectionReason}
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="pt-2 border-t border-slate-100 flex flex-col gap-2">
          {role === 'company_admin' && post.status === 'in_review' && (
            <div className="grid grid-cols-2 gap-2">
              <Button
                size="md"
                variant="outline"
                onClick={() => {
                  mockService.updatePostStatus(post.id, 'rejected', 'Needs better hashtags');
                  showToast('Post rejected with feedback', 'info');
                  navigate('/approvals');
                }}
                icon={<XCircle className="w-4 h-4 text-rose-500" />}
              >
                Reject
              </Button>
              <Button
                size="md"
                onClick={handleApprove}
                icon={<CheckCircle className="w-4 h-4" />}
              >
                Approve
              </Button>
            </div>
          )}

          {role === 'company_admin' && (post.status === 'approved' || post.status === 'draft') && (
            <Button
              size="md"
              onClick={handlePublish}
              icon={<Send className="w-4 h-4" />}
              className="w-full"
            >
              Publish to Channels
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};
