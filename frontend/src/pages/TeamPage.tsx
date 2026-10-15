import React, { useState } from 'react';
import { mockService } from '@/api/mock.service';
import { useToast } from '@/context/ToastContext';
import { TeamMember } from '@/types/company';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { Input } from '@/components/common/Input';
import {
  UserPlus,
  Shield,
  PenTool,
} from 'lucide-react';

export const TeamPage: React.FC = () => {
  const { showToast } = useToast();

  const [team, setTeam] = useState<TeamMember[]>(() => mockService.getTeam());
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [telegramId, setTelegramId] = useState('');
  const [selectedRole, setSelectedRole] = useState<'company_admin' | 'content_owner'>(
    'content_owner'
  );

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    if (!displayName.trim() || !telegramId.trim()) {
      showToast('Please enter member name and Telegram numeric ID', 'warning');
      return;
    }

    const tid = parseInt(telegramId.trim(), 10);
    if (isNaN(tid) || tid <= 0) {
      showToast('Telegram ID must be a positive integer', 'warning');
      return;
    }

    const newMember = mockService.inviteMember(displayName.trim(), tid, selectedRole);
    setTeam(mockService.getTeam());
    setShowInviteModal(false);
    setDisplayName('');
    setTelegramId('');
    showToast(`Invited ${newMember.displayName} as ${selectedRole === 'company_admin' ? 'Company Admin' : 'Content Creator'}!`, 'success');
  };

  return (
    <div className="space-y-4 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Team Members</h1>
          <p className="text-xs text-slate-500">
            Manage workspace roles and collaborate on social media
          </p>
        </div>
        <Button
          size="sm"
          onClick={() => setShowInviteModal(!showInviteModal)}
          icon={<UserPlus className="w-3.5 h-3.5" />}
        >
          Invite Member
        </Button>
      </div>

      {/* Role explanation card */}
      <Card className="p-3.5 bg-slate-50 border-slate-100 space-y-2">
        <h3 className="text-xs font-bold text-slate-700">Workspace Role Permissions</h3>
        <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
          <div className="p-2 rounded-xl bg-white border border-slate-200/60 space-y-1">
            <span className="font-bold text-indigo-700 block">Company Admin</span>
            <p className="text-slate-500 leading-tight">
              Review and approve posts, manage channels, invite team members, publish.
            </p>
          </div>
          <div className="p-2 rounded-xl bg-white border border-slate-200/60 space-y-1">
            <span className="font-bold text-slate-700 block">Content Creator</span>
            <p className="text-slate-500 leading-tight">
              Create drafts, upload media, generate AI captions, submit for approval.
            </p>
          </div>
        </div>
      </Card>

      {/* Invite Member Form Modal */}
      {showInviteModal && (
        <Card className="p-4 space-y-3.5 border-indigo-200 bg-indigo-50/20">
          <div className="space-y-1 border-b border-indigo-100 pb-2">
            <h2 className="text-sm font-bold text-slate-900">Invite Team Member</h2>
            <p className="text-xs text-slate-500">
              New members sign in via Telegram Mini App using their Telegram account.
            </p>
          </div>

          <form onSubmit={handleInvite} className="space-y-3">
            <Input
              label="Member Display Name *"
              placeholder="e.g. Alex Morgan"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
            />

            <Input
              label="Telegram Numeric ID *"
              placeholder="e.g. 123456789"
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              helperText="Get Telegram ID from @userinfobot on Telegram"
              required
            />

            {/* Role Radio Picker */}
            <div className="space-y-1.5 text-left">
              <label className="block text-xs font-semibold text-slate-700">
                Assign Workspace Role *
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedRole('content_owner')}
                  className={`p-2.5 rounded-xl border text-left transition-all ${
                    selectedRole === 'content_owner'
                      ? 'bg-indigo-50 border-indigo-300 text-indigo-900 shadow-sm'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <div className="font-bold text-xs flex items-center gap-1.5">
                    <PenTool className="w-3 h-3 text-indigo-600" />
                    <span>Content Creator</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Can draft and submit posts for review
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedRole('company_admin')}
                  className={`p-2.5 rounded-xl border text-left transition-all ${
                    selectedRole === 'company_admin'
                      ? 'bg-indigo-50 border-indigo-300 text-indigo-900 shadow-sm'
                      : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  <div className="font-bold text-xs flex items-center gap-1.5">
                    <Shield className="w-3 h-3 text-indigo-600" />
                    <span>Company Admin</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Full control, approvals & publishing
                  </div>
                </button>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => setShowInviteModal(false)}
              >
                Cancel
              </Button>
              <Button type="submit" size="sm">
                Send Invitation
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Member List */}
      <div className="space-y-2">
        {team.map((member) => (
          <Card key={member.id} className="p-3.5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-sm shrink-0">
                {member.displayName[0].toUpperCase()}
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-slate-900">
                    {member.displayName}
                  </span>
                  {member.username && (
                    <span className="text-[11px] text-slate-400">@{member.username}</span>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  ID: {member.telegramId}
                </div>
              </div>
            </div>

            <Badge type={member.role} />
          </Card>
        ))}
      </div>
    </div>
  );
};
