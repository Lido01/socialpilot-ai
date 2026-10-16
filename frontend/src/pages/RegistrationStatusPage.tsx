import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { companyService } from '@/api/company.service';
import { CompanyRegistrationRequestResponse } from '@/types/company';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { LoadingState } from '@/components/common/StateView';
import {
  Clock,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  Building2,
  ArrowRight,
} from 'lucide-react';

export const RegistrationStatusPage: React.FC = () => {
  const navigate = useNavigate();
  const { pendingRegistration, refreshRegistrations, setActiveCompany } = useAuth();

  const [registration, setRegistration] =
    useState<CompanyRegistrationRequestResponse | null>(pendingRegistration);
  const [isLoading, setIsLoading] = useState(false);

  const fetchStatus = async () => {
    setIsLoading(true);
    try {
      const list = await refreshRegistrations();
      if (list && list.length > 0) {
        const latest = list[0];
        setRegistration(latest);

        if (latest.status === 'approved' || latest.status === 'active') {
          // If approved, load company details and go to dashboard
          try {
            const comp = await companyService.getCompany(latest.id);
            setActiveCompany(comp);
            navigate('/dashboard');
          } catch {
            // Wait for backend to finalize company record
          }
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  if (isLoading && !registration) {
    return <LoadingState message="Checking registration status..." />;
  }

  const isPending = registration?.status === 'pending';
  const isApproved = registration?.status === 'approved' || registration?.status === 'active';
  const isRejected = registration?.status === 'rejected';
  const isInfoRequested = registration?.status === 'info_requested';

  return (
    <div className="py-6 space-y-6 max-w-sm mx-auto">
      <div className="text-center space-y-2">
        <div
          className={`w-14 h-14 rounded-2xl mx-auto flex items-center justify-center shadow-sm ${
            isApproved
              ? 'bg-emerald-50 text-emerald-600'
              : isRejected
              ? 'bg-rose-50 text-rose-600'
              : isInfoRequested
              ? 'bg-amber-50 text-amber-600'
              : 'bg-indigo-50 text-indigo-600 animate-pulse'
          }`}
        >
          {isApproved && <CheckCircle2 className="w-7 h-7" />}
          {isRejected && <XCircle className="w-7 h-7" />}
          {isInfoRequested && <HelpCircle className="w-7 h-7" />}
          {isPending && <Clock className="w-7 h-7" />}
        </div>

        <div className="space-y-1">
          <h1 className="text-xl font-extrabold text-slate-900">
            {isApproved
              ? 'Company Approved!'
              : isRejected
              ? 'Registration Rejected'
              : isInfoRequested
              ? 'Action Required'
              : 'Registration Pending Review'}
          </h1>
          <p className="text-xs text-slate-500">
            {isPending
              ? 'Your application has been received and is awaiting approval by the Platform Owner.'
              : isApproved
              ? 'Your workspace is active. You can now access your channels and dashboard.'
              : isRejected
              ? 'Your registration could not be approved at this time.'
              : 'The reviewer has requested additional information regarding your workspace.'}
          </p>
        </div>
      </div>

      {registration && (
        <Card className="p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-bold text-slate-900">
                {registration.name}
              </span>
            </div>
            <Badge type={registration.status} />
          </div>

          <div className="space-y-2 text-xs text-slate-600">
            {registration.industry && (
              <div className="flex justify-between">
                <span className="text-slate-400">Industry:</span>
                <span className="font-medium text-slate-800">{registration.industry}</span>
              </div>
            )}
            {registration.country && (
              <div className="flex justify-between">
                <span className="text-slate-400">Country:</span>
                <span className="font-medium text-slate-800">{registration.country}</span>
              </div>
            )}
            {registration.contact_email && (
              <div className="flex justify-between">
                <span className="text-slate-400">Contact Email:</span>
                <span className="font-medium text-slate-800">{registration.contact_email}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-400">Submitted:</span>
              <span className="font-medium text-slate-800">
                {new Date(registration.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Stepper tracker */}
          <div className="pt-2 border-t border-slate-100 space-y-2">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
              Approval Progress
            </span>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2 text-emerald-700">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>1. Request submitted</span>
              </div>
              <div
                className={`flex items-center gap-2 ${
                  isPending ? 'text-indigo-600 font-semibold' : 'text-slate-400'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                    isPending
                      ? 'bg-indigo-600 text-white'
                      : isApproved
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {isApproved ? '✓' : '2'}
                </div>
                <span>2. Platform Owner Verification</span>
              </div>
              <div
                className={`flex items-center gap-2 ${
                  isApproved ? 'text-emerald-700 font-semibold' : 'text-slate-400'
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                    isApproved ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  3
                </div>
                <span>3. Company Admin Workspace Activation</span>
              </div>
            </div>
          </div>

          {isApproved ? (
            <Button
              size="lg"
              onClick={() => navigate('/dashboard')}
              icon={<ArrowRight className="w-4 h-4" />}
              className="w-full mt-2"
            >
              Enter Dashboard
            </Button>
          ) : (
            <Button
              size="md"
              variant="outline"
              onClick={fetchStatus}
              isLoading={isLoading}
              icon={<RefreshCw className="w-4 h-4" />}
              className="w-full mt-2"
            >
              Refresh Status
            </Button>
          )}
        </Card>
      )}

      {isPending && (
        <div className="p-3 bg-amber-50 rounded-xl border border-amber-200/60 text-xs text-amber-800 space-y-1">
          <p className="font-semibold">💡 Testing Platform Owner Approval?</p>
          <p className="text-[11px] leading-relaxed">
            Switch your role to <b>Platform Owner</b> in the top banner to review and approve this company request immediately!
          </p>
        </div>
      )}
    </div>
  );
};
