import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { DevModeBanner } from '@/components/common/DevModeBanner';
import { Header } from './Header';
import { BottomNav } from './BottomNav';

export const AppShell: React.FC = () => {
  const location = useLocation();

  // Screens that should not display the bottom tab bar (e.g. Welcome & registration)
  const isAuthOrOnboarding = [
    '/welcome',
    '/register',
    '/registration-status',
  ].includes(location.pathname);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      <DevModeBanner />
      {!isAuthOrOnboarding && <Header />}

      <main className={`flex-1 max-w-md w-full mx-auto px-4 ${isAuthOrOnboarding ? 'py-6' : 'pt-4 pb-24'}`}>
        <Outlet />
      </main>

      {!isAuthOrOnboarding && <BottomNav />}
    </div>
  );
};
