import React from 'react';
import { AlertCircle, Inbox, RefreshCw } from 'lucide-react';
import { Button } from './Button';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading...',
}) => (
  <div className="flex flex-col items-center justify-center p-8 text-center space-y-3 min-h-[220px]">
    <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
    <p className="text-xs font-medium text-slate-500 animate-pulse">{message}</p>
  </div>
);

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionText,
  onAction,
}) => (
  <div className="flex flex-col items-center justify-center p-8 text-center bg-white rounded-2xl border border-slate-100 shadow-sm space-y-3">
    <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600">
      {icon || <Inbox className="w-6 h-6" />}
    </div>
    <div className="space-y-1 max-w-xs">
      <h3 className="text-sm font-bold text-slate-800">{title}</h3>
      <p className="text-xs text-slate-500 leading-relaxed">{description}</p>
    </div>
    {actionText && onAction && (
      <Button size="sm" variant="secondary" onClick={onAction} className="mt-2">
        {actionText}
      </Button>
    )}
  </div>
);

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message,
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center p-6 text-center bg-rose-50/50 rounded-2xl border border-rose-100 space-y-3">
    <div className="w-10 h-10 rounded-xl bg-rose-100 flex items-center justify-center text-rose-600">
      <AlertCircle className="w-5 h-5" />
    </div>
    <div className="space-y-1 max-w-xs">
      <h3 className="text-sm font-bold text-rose-900">{title}</h3>
      <p className="text-xs text-rose-700 leading-relaxed">{message}</p>
    </div>
    {onRetry && (
      <Button
        size="sm"
        variant="outline"
        onClick={onRetry}
        icon={<RefreshCw className="w-3.5 h-3.5" />}
        className="mt-1"
      >
        Try Again
      </Button>
    )}
  </div>
);
