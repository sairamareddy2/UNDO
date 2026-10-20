import React, { useState } from 'react';
import {
  RotateCcw,
  Play,
  Check,
  X,
  ChevronDown,
  ChevronUp,
  Database,
  Info,
  Clock,
  Loader2,
} from 'lucide-react';
import type { Action } from '../types';
import { PolicyBadge } from './PolicyBadge';
import { StatusBadge } from './StatusBadge';

interface Props {
  action: Action;
  onApprove?: (actionId: string) => Promise<void>;
  onReject?: (actionId: string) => Promise<void>;
  onExecute?: (actionId: string) => Promise<void>;
  onUndo?: (actionId: string) => Promise<void>;
  isProcessing?: boolean;
}

export const ActionCard: React.FC<Props> = ({
  action,
  onApprove,
  onReject,
  onExecute,
  onUndo,
  isProcessing = false,
}) => {
  const [showStateDetails, setShowStateDetails] = useState(false);
  const [localLoading, setLocalLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleAction = async (fn?: (id: string) => Promise<void>) => {
    if (!fn) return;
    setActionError(null);
    setLocalLoading(true);
    try {
      await fn(action.id);
    } catch (err: any) {
      setActionError(err.message || 'Action operation failed');
    } finally {
      setLocalLoading(false);
    }
  };

  const busy = isProcessing || localLoading;

  // Determine eligible actions
  const needsApproval =
    action.policy_decision === 'REQUIRE_APPROVAL' &&
    action.status === 'PENDING' &&
    !action.approval_decision;

  const canExecute =
    action.status === 'APPROVED' ||
    (action.status === 'PENDING' && action.policy_decision === 'ALLOW');

  const canUndo = action.status === 'EXECUTED' && action.is_reversible;

  return (
    <div className="bg-navy-900 border border-navy-750/70 hover:border-navy-600/70 rounded-xl p-5 shadow-lg transition-all duration-200">
      {/* Header row: Title + Badges */}
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-navy-800 text-violet-400 border border-violet-900/40">
              {action.action_type}
            </span>
            <span className="text-xs text-slate-400">
              ID: {action.id.slice(0, 8)}...
            </span>
          </div>
          <h3 className="text-base font-semibold text-slate-100">{action.title}</h3>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <PolicyBadge decision={action.policy_decision} />
          <StatusBadge status={action.status} />
        </div>
      </div>

      {/* Policy Governance Rationale */}
      <div className="bg-navy-950/70 border border-navy-800/80 rounded-lg p-3 mb-4 text-xs">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-slate-400 font-medium">Policy Rule: </span>
            <span className="text-slate-300">{action.policy_reason}</span>
          </div>
        </div>
      </div>

      {/* Parameters Preview */}
      <div className="mb-4">
        <div className="text-xs font-medium text-slate-400 mb-1.5 flex items-center justify-between">
          <span>Parameters</span>
          <span className="text-[11px] text-slate-400">
            {action.is_reversible ? '✦ Reversible Operation' : '⚠ Non-Reversible'}
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(action.parameters).map(([key, val]) => (
            <span
              key={key}
              className="inline-flex items-center gap-1 font-mono text-xs bg-navy-850 px-2.5 py-1 rounded-md text-slate-300 border border-navy-750"
            >
              <span className="text-slate-400">{key}:</span>
              <span className="text-violet-300 font-semibold">{String(val)}</span>
            </span>
          ))}
        </div>
      </div>

      {/* Execution Result Banner */}
      {action.execution_result && (
        <div className="bg-emerald-950/30 border border-emerald-500/20 rounded-lg p-3 mb-4 text-xs text-emerald-300 flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{action.execution_result.message || 'Operation executed successfully.'}</span>
        </div>
      )}

      {/* Error Banner */}
      {(action.error_message || actionError) && (
        <div className="bg-rose-950/40 border border-rose-500/30 rounded-lg p-3 mb-4 text-xs text-rose-300">
          {action.error_message || actionError}
        </div>
      )}

      {/* Before / After State Snapshot Toggle */}
      {(action.before_state || action.after_state) && (
        <div className="mb-4 pt-2 border-t border-navy-800">
          <button
            type="button"
            onClick={() => setShowStateDetails(!showStateDetails)}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-violet-300 transition-colors"
          >
            <Database className="w-3.5 h-3.5 text-violet-400" />
            <span>State Diff Inspection</span>
            {showStateDetails ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>

          {showStateDetails && (
            <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
              <div className="bg-navy-950 p-2.5 rounded border border-navy-800">
                <div className="text-[11px] text-slate-400 font-semibold mb-1 flex items-center gap-1">
                  <span>BEFORE STATE</span>
                </div>
                <pre className="text-slate-300 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(action.before_state, null, 2) || '(empty)'}
                </pre>
              </div>

              <div className="bg-navy-950 p-2.5 rounded border border-navy-800">
                <div className="text-[11px] text-emerald-400 font-semibold mb-1 flex items-center gap-1">
                  <span>AFTER STATE</span>
                </div>
                <pre className="text-emerald-300/90 overflow-x-auto whitespace-pre-wrap">
                  {JSON.stringify(action.after_state, null, 2) || '(empty)'}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Action Controls Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-navy-800/80 mt-2">
        <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          <span>
            {action.executed_at
              ? `Executed: ${new Date(action.executed_at).toLocaleTimeString()}`
              : action.reversed_at
              ? `Reversed: ${new Date(action.reversed_at).toLocaleTimeString()}`
              : `Created: ${new Date(action.created_at).toLocaleTimeString()}`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Approval Controls */}
          {needsApproval && (
            <>
              <button
                type="button"
                disabled={busy}
                onClick={() => handleAction(onReject)}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-rose-950/50 hover:bg-rose-900/60 text-rose-300 border border-rose-800/50 transition-colors disabled:opacity-50"
              >
                {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <X className="w-3.5 h-3.5" />}
                Reject
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => handleAction(onApprove)}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white shadow transition-colors disabled:opacity-50"
              >
                {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                Approve
              </button>
            </>
          )}

          {/* Execute Control */}
          {canExecute && (
            <button
              type="button"
              disabled={busy}
              onClick={() => handleAction(onExecute)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white shadow-md shadow-violet-900/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              Execute Action
            </button>
          )}

          {/* Reversal / Undo Control */}
          {canUndo && (
            <button
              type="button"
              disabled={busy}
              onClick={() => handleAction(onUndo)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-purple-950/80 hover:bg-purple-900 text-purple-200 border border-purple-500/40 shadow-md transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
              title="Undo this operation and restore prior database state"
            >
              {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCcw className="w-3.5 h-3.5" />}
              Undo Action
            </button>
          )}

          {action.status === 'REVERSED' && (
            <span className="text-xs text-purple-300 font-mono flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-950/60 border border-purple-800/40 shadow-sm">
              <RotateCcw className="w-3.5 h-3.5 text-purple-300" /> Restored to Prior State
            </span>
          )}

          {action.status === 'BLOCKED' && (
            <span className="text-xs text-rose-400 font-mono">
              Action Blocked
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
