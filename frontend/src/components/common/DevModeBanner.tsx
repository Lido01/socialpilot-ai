import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useTelegram } from '@/context/TelegramContext';
import { UserRole, ROLE_CONFIGS } from '@/types/auth';
import { Wrench, Shield, ChevronDown, Check, Eye } from 'lucide-react';

export const DevModeBanner: React.FC = () => {
  const { isInTelegram } = useTelegram();
  const { role, setDevRole, isDevMockMode, toggleDevMockMode } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  // In production / inside real Telegram, this banner stays tucked away or minimal
  return (
    <div className="bg-slate-900 text-white text-xs border-b border-slate-800 transition-all">
      <div className="max-w-md mx-auto px-4 py-1.5 flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Wrench className="w-3.5 h-3.5 text-amber-400" />
          <span className="font-semibold text-slate-200">
            {isInTelegram ? 'Telegram Mode' : 'Dev Preview'}
          </span>
          <span className="text-slate-500">•</span>
          <span className="text-indigo-300 font-medium">{ROLE_CONFIGS[role].label}</span>
        </div>

        <div className="flex items-center gap-2">
          {isDevMockMode && (
            <span className="bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded text-[10px] font-bold border border-amber-500/30">
              MOCK PREVIEW
            </span>
          )}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center gap-1 text-slate-400 hover:text-white px-1.5 py-0.5 rounded transition-colors"
          >
            <span>Options</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="max-w-md mx-auto px-4 py-3 bg-slate-950 border-t border-slate-800 space-y-3">
          <div>
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
              <Shield className="w-3 h-3 text-indigo-400" /> Switch Role Preview
            </div>
            <div className="grid grid-cols-3 gap-1.5">
              {(Object.keys(ROLE_CONFIGS) as UserRole[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setDevRole(r)}
                  className={`px-2 py-1.5 rounded-lg text-left text-[11px] transition-all flex items-center justify-between ${
                    role === r
                      ? 'bg-indigo-600 text-white font-semibold'
                      : 'bg-slate-900 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <span className="truncate">{ROLE_CONFIGS[r].label.split(' ')[0]}</span>
                  {role === r && <Check className="w-3 h-3 shrink-0" />}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-1 border-t border-slate-900">
            <div className="flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-slate-400" />
              <div>
                <div className="font-semibold text-slate-200">Dev Mock Mode</div>
                <div className="text-[10px] text-slate-500">
                  Simulates unintegrated endpoints (Posts, Channels, AI)
                </div>
              </div>
            </div>
            <button
              onClick={() => toggleDevMockMode()}
              className={`px-2.5 py-1 rounded-full text-[11px] font-semibold transition-colors ${
                isDevMockMode
                  ? 'bg-amber-500 text-slate-950'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {isDevMockMode ? 'Enabled' : 'Disabled'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
