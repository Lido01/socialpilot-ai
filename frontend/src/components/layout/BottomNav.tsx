import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useTelegram } from '@/context/TelegramContext';
import {
  LayoutDashboard,
  PenTool,
  FileText,
  CheckSquare,
  Radio,
  Settings,
  ShieldCheck,
} from 'lucide-react';

export const BottomNav: React.FC = () => {
  const { role } = useAuth();
  const { haptic } = useTelegram();

  interface NavItem {
    to: string;
    label: string;
    icon: React.ReactNode;
    roles?: string[];
  }

  const navItems: NavItem[] = [
    {
      to: '/dashboard',
      label: 'Home',
      icon: <LayoutDashboard className="w-5 h-5" />,
    },
    {
      to: '/create-post',
      label: 'Create',
      icon: <PenTool className="w-5 h-5" />,
    },
    {
      to: '/drafts',
      label: 'Drafts',
      icon: <FileText className="w-5 h-5" />,
    },
    ...(role === 'company_admin'
      ? [
          {
            to: '/approvals',
            label: 'Approvals',
            icon: <CheckSquare className="w-5 h-5" />,
          },
        ]
      : []),
    ...(role === 'platform_owner'
      ? [
          {
            to: '/owner/companies',
            label: 'Review',
            icon: <ShieldCheck className="w-5 h-5" />,
          },
        ]
      : []),
    ...(role !== 'platform_owner' && role !== 'company_admin'
      ? [
          {
            to: '/channels',
            label: 'Channels',
            icon: <Radio className="w-5 h-5" />,
          },
        ]
      : []),
    {
      to: '/settings',
      label: 'Settings',
      icon: <Settings className="w-5 h-5" />,
    },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-100 safe-area-pb">
      <div className="max-w-md mx-auto px-2 py-1 flex items-center justify-around">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={() => haptic('light')}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center py-1 px-2 min-w-[56px] rounded-xl transition-all duration-150 ${
                isActive
                  ? 'text-indigo-600 font-semibold'
                  : 'text-slate-600 hover:text-slate-800'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <div
                  className={`p-1 rounded-xl transition-colors ${
                    isActive ? 'bg-indigo-50 text-indigo-600' : ''
                  }`}
                >
                  {item.icon}
                </div>
                <span className="text-[10px] mt-0.5 tracking-tight truncate max-w-[64px]">
                  {item.label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
};
