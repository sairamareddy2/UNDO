import React from 'react';
import {
  Clock,
  CheckCircle2,
  XCircle,
  RotateCcw,
  AlertTriangle,
  Play,
} from 'lucide-react';
import type { ActionStatus } from '../types';

interface Props {
  status: ActionStatus;
}

export const StatusBadge: React.FC<Props> = ({ status }) => {
  switch (status) {
    case 'PENDING':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
          <Clock className="w-3 h-3 text-slate-400" />
          Pending
        </span>
      );
    case 'APPROVED':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-indigo-950/80 text-indigo-300 border border-indigo-700/50">
          <Play className="w-3 h-3 text-indigo-400" />
          Approved (Ready)
        </span>
      );
    case 'REJECTED':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-slate-800/80 text-slate-400 border border-slate-700 line-through">
          <XCircle className="w-3 h-3 text-slate-400" />
          Rejected
        </span>
      );
    case 'EXECUTED':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-emerald-950/70 text-emerald-300 border border-emerald-600/40">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          Completed
        </span>
      );
    case 'REVERSED':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-purple-950/70 text-purple-300 border border-purple-500/40">
          <RotateCcw className="w-3 h-3 text-purple-400" />
          Reversed (Undone)
        </span>
      );
    case 'BLOCKED':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-rose-950/70 text-rose-300 border border-rose-600/40">
          <XCircle className="w-3 h-3 text-rose-400" />
          Blocked
        </span>
      );
    case 'FAILED':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-red-950/80 text-red-300 border border-red-600/50">
          <AlertTriangle className="w-3 h-3 text-red-400" />
          Failed
        </span>
      );
    default:
      return null;
  }
};
