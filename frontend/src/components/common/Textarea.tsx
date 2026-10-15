import React from 'react';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  charCount?: { current: number; max: number };
}

export const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  helperText,
  charCount,
  className = '',
  id,
  rows = 4,
  ...props
}) => {
  const textareaId = id || `textarea-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <div className="w-full space-y-1.5 text-left">
      <div className="flex items-center justify-between">
        {label && (
          <label htmlFor={textareaId} className="block text-xs font-semibold text-slate-700">
            {label}
          </label>
        )}
        {charCount && (
          <span
            className={`text-[11px] font-mono ${
              charCount.current > charCount.max
                ? 'text-rose-600 font-bold'
                : 'text-slate-400'
            }`}
          >
            {charCount.current}/{charCount.max}
          </span>
        )}
      </div>
      <textarea
        id={textareaId}
        rows={rows}
        className={`block w-full rounded-xl border bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/20 ${
          error
            ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-500/20'
            : 'border-slate-200 focus:border-indigo-600'
        } ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-rose-600 font-medium">{error}</p>}
      {!error && helperText && <p className="text-xs text-slate-500">{helperText}</p>}
    </div>
  );
};
