import React, { useState } from 'react';
import {
  History,
  RotateCcw,
  Search,
  RefreshCw,
} from 'lucide-react';
import type { Action, AuditEvent } from '../types';
import { PolicyBadge } from './PolicyBadge';
import { StatusBadge } from './StatusBadge';

interface Props {
  actions: Action[];
  auditEvents: AuditEvent[];
  onUndo: (actionId: string) => Promise<void>;
  onRefresh: () => Promise<void>;
  isLoading?: boolean;
}

export const HistoryView: React.FC<Props> = ({
  actions,
  auditEvents,
  onUndo,
  onRefresh,
  isLoading = false,
}) => {
  const [filterTab, setFilterTab] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'ACTIONS' | 'AUDIT_LOG'>('ACTIONS');
  const [undoingId, setUndoingId] = useState<string | null>(null);

  const handleUndo = async (actionId: string) => {
    setUndoingId(actionId);
    try {
      await onUndo(actionId);
    } finally {
      setUndoingId(null);
    }
  };

  const filteredActions = actions.filter((act) => {
    // Tab filter
    if (filterTab === 'COMPLETED' && act.status !== 'EXECUTED') return false;
    if (filterTab === 'REVERSED' && act.status !== 'REVERSED') return false;
    if (filterTab === 'PENDING' && act.status !== 'PENDING' && act.status !== 'APPROVED') return false;
    if (filterTab === 'BLOCKED' && act.status !== 'BLOCKED') return false;

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      const matchTitle = act.title.toLowerCase().includes(term);
      const matchType = act.action_type.toLowerCase().includes(term);
      const matchReason = act.policy_reason.toLowerCase().includes(term);
      return matchTitle || matchType || matchReason;
    }
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Top Header & Search / Tabs */}
      <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-violet-950/70 border border-violet-800/40 text-violet-400">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100">Action History & State Rollback</h2>
              <p className="text-xs text-slate-400">
                Audit trail of all proposed, approved, executed, and reversed Alexa+ operations.
              </p>
            </div>
          </div>

          {/* View mode toggle & Refresh */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onRefresh()}
              disabled={isLoading}
              className="p-2 rounded-xl bg-navy-950 border border-navy-750 text-slate-300 hover:text-white transition-colors"
              title="Refresh ledger"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>

            <div className="inline-flex rounded-xl p-1 bg-navy-950 border border-navy-750 text-xs">
              <button
                type="button"
                onClick={() => setViewMode('ACTIONS')}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                  viewMode === 'ACTIONS'
                    ? 'bg-violet-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Action Ledger ({actions.length})
              </button>
              <button
                type="button"
                onClick={() => setViewMode('AUDIT_LOG')}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                  viewMode === 'AUDIT_LOG'
                    ? 'bg-violet-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Immutable Audit Log ({auditEvents.length})
              </button>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        {viewMode === 'ACTIONS' && (
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-navy-800">
            {/* Filter Tabs */}
            <div className="flex items-center gap-1.5 flex-wrap">
              {[
                { id: 'ALL', label: 'All Operations' },
                { id: 'COMPLETED', label: 'Completed' },
                { id: 'REVERSED', label: 'Reversed (Undone)' },
                { id: 'PENDING', label: 'Pending / Ready' },
                { id: 'BLOCKED', label: 'Blocked' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setFilterTab(tab.id)}
                  className={`text-xs px-3 py-1 rounded-lg font-medium transition-colors ${
                    filterTab === tab.id
                      ? 'bg-navy-750 text-violet-300 border border-violet-500/40'
                      : 'bg-navy-950/70 text-slate-400 hover:text-slate-200 border border-navy-800'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative min-w-[220px]">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search action history..."
                className="w-full pl-9 pr-3 py-1.5 bg-navy-950 border border-navy-750 rounded-lg text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-violet-500/80"
              />
            </div>
          </div>
        )}
      </div>

      {/* Main Ledger Content */}
      {viewMode === 'ACTIONS' ? (
        filteredActions.length === 0 ? (
          <div className="bg-navy-900 border border-dashed border-navy-750 rounded-2xl p-12 text-center">
            <History className="w-8 h-8 text-slate-400 mx-auto mb-2 opacity-50" />
            <div className="text-sm font-semibold text-slate-300">No actions recorded in this view</div>
            <p className="text-xs text-slate-400 mt-1">
              Actions will appear here as you submit instructions via the Action Planner.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredActions.map((action) => {
              const canUndo = action.status === 'EXECUTED' && action.is_reversible;
              const isUndoing = undoingId === action.id;

              return (
                <div
                  key={action.id}
                  className="bg-navy-900 border border-navy-750/70 hover:border-navy-650 rounded-xl p-4 shadow-md transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <PolicyBadge decision={action.policy_decision} size="sm" />
                      <StatusBadge status={action.status} />
                      <span className="font-mono text-xs text-violet-400 px-2 py-0.5 rounded bg-navy-950 border border-navy-800">
                        {action.action_type}
                      </span>
                      <span className="text-[11px] text-slate-400 font-mono">
                        {new Date(action.created_at).toLocaleString()}
                      </span>
                    </div>

                    <h4 className="text-sm font-semibold text-slate-100">{action.title}</h4>

                    <div className="text-xs text-slate-400 flex items-center gap-3 flex-wrap">
                      <span>Reason: {action.policy_reason}</span>
                      {action.execution_result?.message && (
                        <span className="text-emerald-400">
                          Result: {action.execution_result.message}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions / Undo column */}
                  <div className="flex items-center gap-2 shrink-0">
                    {canUndo && (
                      <button
                        type="button"
                        disabled={isUndoing || isLoading}
                        onClick={() => handleUndo(action.id)}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-purple-950/80 hover:bg-purple-900 text-purple-200 border border-purple-500/40 shadow transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
                        title="Rollback this operation in SQLite database"
                      >
                        <RotateCcw className={`w-3.5 h-3.5 ${isUndoing ? 'animate-spin' : ''}`} />
                        {isUndoing ? 'Undoing...' : 'Undo Action'}
                      </button>
                    )}

                    {action.status === 'REVERSED' && (
                      <span className="inline-flex items-center gap-1 text-xs text-purple-400 bg-purple-950/40 px-2.5 py-1 rounded border border-purple-800/40">
                        <RotateCcw className="w-3 h-3" /> Reversed
                      </span>
                    )}

                    {!action.is_reversible && action.status === 'EXECUTED' && (
                      <span className="text-xs text-slate-400">Non-reversible</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : (
        /* Immutable Audit Log Table */
        <div className="bg-navy-900 border border-navy-750/80 rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-navy-950 text-slate-400 font-mono uppercase text-[11px] border-b border-navy-800">
                <tr>
                  <th className="py-3 px-4">Event ID</th>
                  <th className="py-3 px-4">Event Type</th>
                  <th className="py-3 px-4">Action ID</th>
                  <th className="py-3 px-4">Details</th>
                  <th className="py-3 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/60 font-mono">
                {auditEvents.map((evt) => (
                  <tr key={evt.id} className="hover:bg-navy-850/50 transition-colors">
                    <td className="py-3 px-4 text-slate-400">#{evt.id}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                          evt.event_type === 'ACTION_UNDONE'
                            ? 'bg-purple-950 text-purple-300 border border-purple-700/50'
                            : evt.event_type === 'ACTION_EXECUTED'
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-700/50'
                            : evt.event_type === 'POLICY_EVALUATED'
                            ? 'bg-navy-800 text-violet-300 border border-violet-800/40'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {evt.event_type}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-violet-400">
                      {evt.action_id ? `${evt.action_id.slice(0, 8)}...` : '—'}
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-slate-300">
                      {JSON.stringify(evt.details)}
                    </td>
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {new Date(evt.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
