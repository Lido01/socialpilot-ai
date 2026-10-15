import React from 'react';
import { PostStatus, CompanyStatus } from '@/types';
import { UserRole, ROLE_CONFIGS } from '@/types/auth';

type BadgeType = PostStatus | CompanyStatus | UserRole | 'custom';

interface BadgeProps {
  type?: BadgeType;
  label?: string;
  variant?: 'slate' | 'indigo' | 'emerald' | 'amber' | 'rose' | 'blue';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  type,
  label,
  variant,
  size = 'sm',
}) => {
  let resolvedLabel = label || '';
  let resolvedVariant = variant || 'slate';

  if (type) {
    switch (type) {
      // Roles
      case 'platform_owner':
        resolvedLabel = ROLE_CONFIGS.platform_owner.label;
        resolvedVariant = 'indigo';
        break;
      case 'company_admin':
        resolvedLabel = ROLE_CONFIGS.company_admin.label;
        resolvedVariant = 'blue';
        break;
      case 'content_owner':
        resolvedLabel = ROLE_CONFIGS.content_owner.label;
        resolvedVariant = 'slate';
        break;

      // Post status
      case 'draft':
        resolvedLabel = 'Draft';
        resolvedVariant = 'slate';
        break;
      case 'in_review':
        resolvedLabel = 'In Review';
        resolvedVariant = 'amber';
        break;
      case 'approved':
        resolvedLabel = 'Approved';
        resolvedVariant = 'emerald';
        break;
      case 'scheduled':
        resolvedLabel = 'Scheduled';
        resolvedVariant = 'blue';
        break;
      case 'published':
        resolvedLabel = 'Published';
        resolvedVariant = 'emerald';
        break;
      case 'rejected':
      case 'failed':
        resolvedLabel = type === 'rejected' ? 'Rejected' : 'Failed';
        resolvedVariant = 'rose';
        break;

      // Company status
      case 'pending':
        resolvedLabel = 'Pending Review';
        resolvedVariant = 'amber';
        break;
      case 'active':
        resolvedLabel = 'Active';
        resolvedVariant = 'emerald';
        break;
      case 'info_requested':
        resolvedLabel = 'Action Needed';
        resolvedVariant = 'amber';
        break;
      case 'suspended':
        resolvedLabel = 'Suspended';
        resolvedVariant = 'rose';
        break;
    }
  }

  const variantStyles = {
    slate: 'bg-slate-100 text-slate-700 border-slate-200',
    indigo: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    rose: 'bg-rose-50 text-rose-700 border-rose-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 font-medium',
    md: 'text-xs px-2.5 py-1 font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${variantStyles[resolvedVariant]} ${sizeStyles[size]} tracking-tight`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {resolvedLabel}
    </span>
  );
};
