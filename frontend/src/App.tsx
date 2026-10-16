import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AppShell } from '@/components/layout/AppShell';
import { RoleGate } from '@/components/layout/RoleGate';
import { LoadingState } from '@/components/common/StateView';

// Page components
import { WelcomePage } from '@/pages/WelcomePage';
import { RegistrationStatusPage } from '@/pages/RegistrationStatusPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { CreatePostPage } from '@/pages/CreatePostPage';
import { MediaPreviewPage } from '@/pages/MediaPreviewPage';
import { DraftsPage } from '@/pages/DraftsPage';
import { ApprovalsPage } from '@/pages/ApprovalsPage';
import { ChannelsPage } from '@/pages/ChannelsPage';
import { HistoryPage } from '@/pages/HistoryPage';
import { TeamPage } from '@/pages/TeamPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { OwnerAdminPage } from '@/pages/OwnerAdminPage';

// Smart root redirector
const RootRedirect: React.FC = () => {
  const { isAuthenticated, isLoading, activeCompany, pendingRegistration, role } = useAuth();

  if (isLoading) {
    return <LoadingState message="Connecting to SocialPilot AI..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/welcome" replace />;
  }

  if (role === 'platform_owner') {
    return <Navigate to="/owner/companies" replace />;
  }

  if (activeCompany) {
    return <Navigate to="/dashboard" replace />;
  }

  if (pendingRegistration) {
    return <Navigate to="/registration-status" replace />;
  }

  return <Navigate to="/welcome" replace />;
};

export const App: React.FC = () => {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingState message="Loading SocialPilot AI..." />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/welcome" element={<WelcomePage />} />
      <Route path="/registration-status" element={<RegistrationStatusPage />} />

      {/* Main Authenticated Application Layout */}
      <Route element={<AppShell />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/create-post" element={<CreatePostPage />} />
        <Route path="/posts/:id/preview" element={<MediaPreviewPage />} />
        <Route path="/drafts" element={<DraftsPage />} />
        <Route path="/channels" element={<ChannelsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/settings" element={<SettingsPage />} />

        {/* Company Admin & Platform Owner Protected Routes */}
        <Route
          path="/approvals"
          element={
            <RoleGate allowedRoles={['company_admin', 'platform_owner']}>
              <ApprovalsPage />
            </RoleGate>
          }
        />
        <Route
          path="/team"
          element={
            <RoleGate allowedRoles={['company_admin', 'platform_owner']}>
              <TeamPage />
            </RoleGate>
          }
        />

        {/* Platform Owner Dedicated Routes */}
        <Route
          path="/owner/companies"
          element={
            <RoleGate allowedRoles={['platform_owner']}>
              <OwnerAdminPage />
            </RoleGate>
          }
        />
      </Route>

      {/* Fallback route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
