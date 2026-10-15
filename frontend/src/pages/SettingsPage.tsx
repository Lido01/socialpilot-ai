import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useTelegram } from '@/context/TelegramContext';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import {
  Building2,
  Smartphone,
  LogOut,
  Code2,
  Radio,
  FileText,
  Users,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, role, activeCompany, setDevRole, isDevMockMode, toggleDevMockMode, logout } = useAuth();
  const { tg, isInTelegram } = useTelegram();

  const handleLogout = () => {
    logout();
    navigate('/welcome');
  };

  return (
    <div className="space-y-4 pb-8">
      <div>
        <h1 className="text-lg font-bold text-slate-900">Settings & Profile</h1>
        <p className="text-xs text-slate-500">
          Manage your account, workspace, and application preferences
        </p>
      </div>

      {/* User Profile Card */}
      <Card className="p-4 space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center font-bold text-lg shadow-sm">
            {user?.displayName ? user.displayName[0].toUpperCase() : 'U'}
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="text-sm font-bold text-slate-900 truncate">
              {user?.displayName || 'SocialPilot User'}
            </h2>
            <p className="text-xs text-slate-500 font-mono">
              Telegram ID: {user?.telegramId || '5298799880'}
            </p>
          </div>
          <Badge type={role} />
        </div>
      </Card>

      {/* Company Workspace Info */}
      {activeCompany && (
        <Card className="p-4 space-y-2.5">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-600" />
              <span className="text-xs font-bold text-slate-800">Workspace Details</span>
            </div>
            <Badge type={activeCompany.status} />
          </div>

          <div className="space-y-1.5 text-xs text-slate-600">
            <div className="flex justify-between">
              <span className="text-slate-400">Company Name:</span>
              <span className="font-semibold text-slate-800">{activeCompany.name}</span>
            </div>
            {activeCompany.industry && (
              <div className="flex justify-between">
                <span className="text-slate-400">Industry:</span>
                <span className="text-slate-700">{activeCompany.industry}</span>
              </div>
            )}
            {activeCompany.contact_email && (
              <div className="flex justify-between">
                <span className="text-slate-400">Contact Email:</span>
                <span className="text-slate-700">{activeCompany.contact_email}</span>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Workspace Navigation Shortcuts */}
      <Card className="p-2 space-y-1">
        <button
          onClick={() => navigate('/channels')}
          className="w-full p-2.5 text-left rounded-xl hover:bg-slate-50 flex items-center justify-between text-xs text-slate-700 transition-colors"
        >
          <div className="flex items-center gap-2.5">
            <Radio className="w-4 h-4 text-blue-600" />
            <span className="font-medium">Telegram Channels</span>
          </div>
          <span className="text-slate-400">→</span>
        </button>

        {role === 'company_admin' && (
          <button
            onClick={() => navigate('/team')}
            className="w-full p-2.5 text-left rounded-xl hover:bg-slate-50 flex items-center justify-between text-xs text-slate-700 transition-colors"
          >
            <div className="flex items-center gap-2.5">
              <Users className="w-4 h-4 text-purple-600" />
              <span className="font-medium">Team Members</span>
            </div>
            <span className="text-slate-400">→</span>
          </button>
        )}

        <button
          onClick={() => navigate('/history')}
          className="w-full p-2.5 text-left rounded-xl hover:bg-slate-50 flex items-center justify-between text-xs text-slate-700 transition-colors"
        >
          <div className="flex items-center gap-2.5">
            <FileText className="w-4 h-4 text-emerald-600" />
            <span className="font-medium">Publishing History</span>
          </div>
          <span className="text-slate-400">→</span>
        </button>
      </Card>

      {/* Telegram Runtime Environment Info */}
      <Card className="p-4 space-y-2.5">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
          <Smartphone className="w-4 h-4 text-slate-600" />
          <span className="text-xs font-bold text-slate-800">Telegram Environment</span>
        </div>

        <div className="space-y-1.5 text-xs text-slate-600">
          <div className="flex justify-between">
            <span className="text-slate-400">Context:</span>
            <span className="font-medium text-slate-800">
              {isInTelegram ? 'Telegram Mini App' : 'Browser Preview Mode'}
            </span>
          </div>
          {tg && (
            <>
              <div className="flex justify-between">
                <span className="text-slate-400">SDK Version:</span>
                <span className="font-mono text-slate-700">{tg.version || '7.0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Platform:</span>
                <span className="font-medium text-slate-700">{tg.platform || 'web'}</span>
              </div>
            </>
          )}
        </div>
      </Card>

      {/* Developer Preview & Role Switcher */}
      <Card className="p-4 space-y-3 bg-slate-900 text-white">
        <div className="flex items-center justify-between pb-2 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-bold text-slate-200">Developer Testing Tools</span>
          </div>
        </div>

        <div className="space-y-2">
          <span className="text-[11px] text-slate-400 block font-semibold">
            Test As Role:
          </span>
          <div className="grid grid-cols-3 gap-1.5">
            <button
              onClick={() => setDevRole('platform_owner')}
              className={`py-1.5 px-2 rounded-lg text-xs font-semibold transition-all ${
                role === 'platform_owner'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Owner
            </button>
            <button
              onClick={() => setDevRole('company_admin')}
              className={`py-1.5 px-2 rounded-lg text-xs font-semibold transition-all ${
                role === 'company_admin'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Admin
            </button>
            <button
              onClick={() => setDevRole('content_owner')}
              className={`py-1.5 px-2 rounded-lg text-xs font-semibold transition-all ${
                role === 'content_owner'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Creator
            </button>
          </div>
        </div>

        <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
          <span className="text-xs text-slate-300">Dev Mock Mode</span>
          <button
            onClick={() => toggleDevMockMode()}
            className={`px-3 py-1 rounded-full text-xs font-bold ${
              isDevMockMode ? 'bg-amber-400 text-slate-950' : 'bg-slate-800 text-slate-400'
            }`}
          >
            {isDevMockMode ? 'ON' : 'OFF'}
          </button>
        </div>
      </Card>

      {/* Logout Button */}
      <Button
        variant="outline"
        size="md"
        onClick={handleLogout}
        icon={<LogOut className="w-4 h-4 text-rose-500" />}
        className="w-full text-rose-600 hover:bg-rose-50 border-rose-200"
      >
        Sign Out / Switch Account
      </Button>
    </div>
  );
};
