import React, { useEffect, useState } from 'react';
import { platformService } from '@/api/platform.service';
import { PendingCompanyResponse } from '@/types/platform';
import { useToast } from '@/context/ToastContext';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { Badge } from '@/components/common/Badge';
import { LoadingState, EmptyState } from '@/components/common/StateView';
import {
  ShieldCheck,
  Building2,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';

export const OwnerAdminPage: React.FC = () => {
  const { showToast } = useToast();
  const [pendingList, setPendingList] = useState<PendingCompanyResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [rejectModalId, setRejectModalId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const loadPendingCompanies = async () => {
    setIsLoading(true);
    try {
      const data = await platformService.getPendingCompanies();
      setPendingList(data || []);
    } catch (err: any) {
      showToast(err.message || 'Failed to load pending registrations', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPendingCompanies();
  }, []);

  const handleApprove = async (id: string) => {
    setActionLoadingId(id);
    try {
      const res = await platformService.approveCompany(id);
      showToast(res.message || 'Company approved successfully!', 'success');
      loadPendingCompanies();
    } catch (err: any) {
      showToast(err.message || 'Failed to approve company', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReject = async (id: string) => {
    if (!rejectionReason.trim()) {
      showToast('Please provide a reason for rejection', 'warning');
      return;
    }

    setActionLoadingId(id);
    try {
      const res = await platformService.rejectCompany(id, rejectionReason.trim());
      showToast(res.message || 'Company registration rejected', 'info');
      setRejectModalId(null);
      setRejectionReason('');
      loadPendingCompanies();
    } catch (err: any) {
      showToast(err.message || 'Failed to reject registration', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRequestInfo = async (id: string) => {
    if (!rejectionReason.trim()) {
      showToast('Please specify what additional information is needed', 'warning');
      return;
    }

    setActionLoadingId(id);
    try {
      const res = await platformService.requestMoreInfo(id, rejectionReason.trim());
      showToast(res.message || 'Requested more information', 'info');
      setRejectModalId(null);
      setRejectionReason('');
      loadPendingCompanies();
    } catch (err: any) {
      showToast(err.message || 'Failed to request info', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="space-y-4 pb-8">
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center gap-1.5 text-indigo-600 font-bold text-xs uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" />
            <span>Platform Owner Admin</span>
          </div>
          <h1 className="text-lg font-bold text-slate-900">Company Registrations</h1>
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={loadPendingCompanies}
          isLoading={isLoading}
          icon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Refresh
        </Button>
      </div>

      {isLoading && pendingList.length === 0 ? (
        <LoadingState message="Loading pending registrations from backend..." />
      ) : pendingList.length === 0 ? (
        <EmptyState
          icon={<CheckCircle2 className="w-6 h-6 text-emerald-600" />}
          title="No pending registrations"
          description="There are currently no company workspaces waiting for platform review."
        />
      ) : (
        <div className="space-y-3">
          {pendingList.map((item) => (
            <Card key={item.id} className="p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-indigo-600" />
                    <h2 className="text-sm font-bold text-slate-900">{item.name}</h2>
                  </div>
                  <p className="text-xs text-slate-500 font-mono">
                    Owner: {item.user_display_name} (TID: {item.user_telegram_id})
                  </p>
                </div>
                <Badge type="pending" />
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                <div>
                  <span className="text-slate-400 block text-[10px]">Industry:</span>
                  <span className="font-medium">{item.industry || '—'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Country:</span>
                  <span className="font-medium">{item.country || '—'}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-slate-400 block text-[10px]">Contact Email:</span>
                  <span className="font-medium">{item.contact_email || '—'}</span>
                </div>
                {item.website && (
                  <div className="col-span-2 flex items-center gap-1">
                    <span className="text-slate-400 text-[10px]">Website:</span>
                    <a
                      href={item.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:underline flex items-center gap-0.5"
                    >
                      <span>{item.website}</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>

              {rejectModalId === item.id ? (
                <div className="p-3 bg-rose-50 rounded-xl border border-rose-200 space-y-2 text-xs">
                  <label className="font-semibold text-rose-900 block">
                    Reason / Notes for applicant:
                  </label>
                  <textarea
                    rows={2}
                    className="w-full p-2 rounded-lg border border-rose-300 bg-white text-xs"
                    placeholder="Enter reason for rejection or additional info requested..."
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                  />
                  <div className="flex justify-end gap-1.5">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setRejectModalId(null);
                        setRejectionReason('');
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRequestInfo(item.id)}
                      isLoading={actionLoadingId === item.id}
                      icon={<HelpCircle className="w-3.5 h-3.5" />}
                    >
                      Request Info
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => handleReject(item.id)}
                      isLoading={actionLoadingId === item.id}
                      icon={<XCircle className="w-3.5 h-3.5" />}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-100">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setRejectModalId(item.id)}
                    icon={<XCircle className="w-3.5 h-3.5 text-rose-500" />}
                  >
                    Reject / Info
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleApprove(item.id)}
                    isLoading={actionLoadingId === item.id}
                    icon={<CheckCircle2 className="w-3.5 h-3.5" />}
                  >
                    Approve Company
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
