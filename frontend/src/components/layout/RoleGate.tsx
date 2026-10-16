import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { UserRole } from '@/types/auth';
import { Card } from '@/components/common/Card';
import { ShieldAlert } from 'lucide-react';
import { Button } from '@/components/common/Button';

interface RoleGateProps {
  allowedRoles: UserRole[];
  children: React.ReactNode;
}

export const RoleGate: React.FC<RoleGateProps> = ({ allowedRoles, children }) => {
  const { role, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/welcome" replace />;
  }

  if (!allowedRoles.includes(role)) {
    return (
      <div className="py-12">
        <Card className="text-center p-6 space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">Access Restricted</h2>
            <p className="text-xs text-slate-500">
              Your role ({role}) does not have permission to access this section.
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={() => window.history.back()}>
            Go Back
          </Button>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
};
