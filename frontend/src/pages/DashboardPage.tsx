import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { mockService } from '@/api/mock.service';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import {
  PenTool,
  Sparkles,
  Radio,
  Users,
  CheckSquare,
  Clock,
  Send,
  FileText,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { role, activeCompany, isDevMockMode, toggleDevMockMode } = useAuth();

  const posts = mockService.getPosts();
  const channels = mockService.getChannels();

  const pendingCount = posts.filter((p) => p.status === 'in_review').length;
  const publishedCount = posts.filter((p) => p.status === 'published').length;
  const draftCount = posts.filter((p) => p.status === 'draft').length;

  return (
    <div className="space-y-5 pb-6">
      {/* Top Welcome Card */}
      <div className="bg-gradient-to-r from-indigo-600 via-indigo-700 to-violet-700 rounded-3xl p-5 text-white shadow-md shadow-indigo-600/15 space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-indigo-200">
              Workspace Overview
            </span>
            <h1 className="text-xl font-bold tracking-tight">
              {activeCompany ? activeCompany.name : 'SocialPilot AI'}
            </h1>
            <p className="text-xs text-indigo-100/80">
              AI-driven social pipeline for Telegram communities.
            </p>
          </div>
          <Badge type={role} variant="indigo" size="md" />
        </div>

        {/* Quick action pill row */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <Button
            size="sm"
            onClick={() => navigate('/create-post')}
            icon={<PenTool className="w-4 h-4" />}
            className="bg-white text-indigo-700 hover:bg-indigo-50 border-0 shadow-none font-bold"
          >
            Create Post
          </Button>
          <Button
            size="sm"
            onClick={() => navigate('/create-post?tab=ai')}
            icon={<Sparkles className="w-4 h-4" />}
            className="bg-indigo-500/40 text-white hover:bg-indigo-500/60 border border-indigo-300/30 font-bold backdrop-blur-sm"
          >
            AI Assistant
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-3 gap-2.5">
        <Card
          onClick={() => navigate('/drafts')}
          hoverEffect
          className="p-3 text-center space-y-1"
        >
          <div className="w-7 h-7 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center mx-auto">
            <FileText className="w-3.5 h-3.5" />
          </div>
          <div className="text-lg font-black text-slate-800">{draftCount}</div>
          <div className="text-[10px] font-medium text-slate-500">Drafts</div>
        </Card>

        <Card
          onClick={() => navigate(role === 'company_admin' ? '/approvals' : '/drafts')}
          hoverEffect
          className="p-3 text-center space-y-1 relative"
        >
          {pendingCount > 0 && (
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-amber-500" />
          )}
          <div className="w-7 h-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
            <Clock className="w-3.5 h-3.5" />
          </div>
          <div className="text-lg font-black text-slate-800">{pendingCount}</div>
          <div className="text-[10px] font-medium text-slate-500">In Review</div>
        </Card>

        <Card
          onClick={() => navigate('/history')}
          hoverEffect
          className="p-3 text-center space-y-1"
        >
          <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
            <Send className="w-3.5 h-3.5" />
          </div>
          <div className="text-lg font-black text-slate-800">{publishedCount}</div>
          <div className="text-[10px] font-medium text-slate-500">Published</div>
        </Card>
      </div>

      {/* Quick Navigation Cards */}
      <div className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Quick Management
          </h2>
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <Card
            onClick={() => navigate('/channels')}
            hoverEffect
            className="p-3.5 flex items-center gap-3"
          >
            <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
              <Radio className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="text-xs font-bold text-slate-800">Channels</div>
              <div className="text-[11px] text-slate-500">{channels.length} connected</div>
            </div>
          </Card>

          {role === 'company_admin' ? (
            <Card
              onClick={() => navigate('/team')}
              hoverEffect
              className="p-3.5 flex items-center gap-3"
            >
              <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                <Users className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-slate-800">Team</div>
                <div className="text-[11px] text-slate-500">Manage members</div>
              </div>
            </Card>
          ) : (
            <Card
              onClick={() => navigate('/drafts')}
              hoverEffect
              className="p-3.5 flex items-center gap-3"
            >
              <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                <CheckSquare className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-bold text-slate-800">My Posts</div>
                <div className="text-[11px] text-slate-500">Track status</div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Recent Activity / Post Summaries */}
      <div className="space-y-3">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Recent Posts & Activity
          </h2>
          <button
            onClick={() => navigate('/drafts')}
            className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
          >
            <span>View All</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {/* Backend Endpoint Notice if not in Dev Mock Mode */}
        {!isDevMockMode && (
          <div className="p-3 bg-indigo-50/70 rounded-2xl border border-indigo-100 text-xs text-indigo-900 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold block">Backend Status</span>
              <p className="text-[11px] text-indigo-700 leading-relaxed">
                The FastAPI backend currently exposes company registration & approval APIs. Post storage APIs (<code>/api/v1/companies/&#123;id&#125;/posts</code>) are pending deployment.
              </p>
              <button
                onClick={() => toggleDevMockMode(true)}
                className="text-[11px] font-bold underline text-indigo-800 hover:text-indigo-950 mt-1 block"
              >
                Enable Dev Mock Mode to preview full post lifecycle →
              </button>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {posts.slice(0, 3).map((post) => (
            <Card
              key={post.id}
              onClick={() => navigate(`/drafts`)}
              hoverEffect
              className="p-3.5 space-y-2.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <span className="font-medium text-slate-700">{post.authorName}</span>
                  <span>•</span>
                  <span>{new Date(post.updatedAt).toLocaleDateString()}</span>
                </div>
                <Badge type={post.status} />
              </div>

              <p className="text-xs text-slate-700 line-clamp-2 leading-relaxed">
                {post.caption}
              </p>

              {post.media.length > 0 && (
                <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                  <span>{post.media.length} media attached</span>
                </div>
              )}
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};
