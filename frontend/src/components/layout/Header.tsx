import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useTelegram } from '@/context/TelegramContext';
import { Badge } from '@/components/common/Badge';
import { ChevronLeft, Sparkles, Building2 } from 'lucide-react';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { role, activeCompany, pendingRegistration } = useAuth();
  const { haptic } = useTelegram();

  const isRootTab = [
    '/',
    '/dashboard',
    '/create-post',
    '/drafts',
    '/approvals',
    '/settings',
    '/owner/companies',
  ].includes(location.pathname);

  const handleBack = () => {
    haptic('light');
    navigate(-1);
  };

  const companyName =
    activeCompany?.name ||
    pendingRegistration?.name ||
    (role === 'platform_owner' ? 'Platform Admin' : 'SocialPilot');

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-100">
      <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5 min-w-0">
          {!isRootTab ? (
            <button
              onClick={handleBack}
              className="p-1 -ml-1 text-slate-600 hover:text-slate-900 active:scale-95 transition-all rounded-lg"
              aria-label="Go back"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          ) : (
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-sm shadow-indigo-500/30 shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
          )}

          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold text-slate-900 truncate">
                {companyName}
              </span>
              {activeCompany && (
                <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              )}
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[10px] text-slate-500 font-medium">SocialPilot AI</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge type={role} size="sm" />
        </div>
      </div>
    </header>
  );
};
