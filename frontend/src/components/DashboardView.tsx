import React from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  RotateCcw,
  Layers,
  ArrowUpRight,
  ShieldX,
  CheckCircle2,
} from 'lucide-react';
import type { Action, ActionPlan, ApplicationState } from '../types';
import { StateMonitor } from './StateMonitor';
import { PolicyBadge } from './PolicyBadge';
import { StatusBadge } from './StatusBadge';

interface Props {
  plans: ActionPlan[];
  actions: Action[];
  state: ApplicationState | null;
  onSelectTab: (tab: 'DASHBOARD' | 'PLANNER' | 'HISTORY') => void;
  onRefreshState: () => Promise<void>;
  onResetState: () => Promise<void>;
  onSelectPlan: (plan: ActionPlan) => void;
  isLoading?: boolean;
}

export const DashboardView: React.FC<Props> = ({
  plans,
  actions,
  state,
  onSelectTab,
  onRefreshState,
  onResetState,
  onSelectPlan,
  isLoading = false,
}) => {
  const pendingApprovals = actions.filter(
    (a) => a.policy_decision === 'REQUIRE_APPROVAL' && a.status === 'PENDING'
  ).length;

  const completedActions = actions.filter((a) => a.status === 'EXECUTED').length;
  const reversedActions = actions.filter((a) => a.status === 'REVERSED').length;
  const blockedActions = actions.filter((a) => a.status === 'BLOCKED').length;

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Pending Approvals</span>
            <div className="p-1.5 rounded-lg bg-amber-950/80 text-amber-400 border border-amber-600/40">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">{pendingApprovals}</div>
          <div className="text-[11px] text-amber-400 mt-1">Require explicit confirmation</div>
        </div>

        {/* Metric 2 */}
        <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Completed Actions</span>
            <div className="p-1.5 rounded-lg bg-emerald-950/80 text-emerald-400 border border-emerald-600/40">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">{completedActions}</div>
          <div className="text-[11px] text-emerald-400 mt-1">Confirmed database commits</div>
        </div>

        {/* Metric 3 */}
        <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Rollbacks (Undos)</span>
            <div className="p-1.5 rounded-lg bg-purple-950/80 text-purple-300 border border-purple-500/40">
              <RotateCcw className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">{reversedActions}</div>
          <div className="text-[11px] text-purple-300 mt-1">Reversed state snapshots</div>
        </div>

        {/* Metric 4 */}
        <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-4 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
            <span>Security Blocks</span>
            <div className="p-1.5 rounded-lg bg-rose-950/80 text-rose-400 border border-rose-600/40">
              <ShieldX className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">{blockedActions}</div>
          <div className="text-[11px] text-rose-400 mt-1">Zero-execution guardrails</div>
        </div>
      </div>

      {/* Live Application State Monitor */}
      <StateMonitor
        state={state}
        onRefresh={onRefreshState}
        onReset={onResetState}
        isLoading={isLoading}
      />

      {/* Two Column Section: Recent Plans + Pending / Recent Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Action Plans */}
        <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-navy-800 mb-3">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-violet-400" />
              Recent Alexa+ Action Plans
            </h3>
            <button
              type="button"
              onClick={() => onSelectTab('PLANNER')}
              className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 font-medium"
            >
              Open Planner <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {plans.length > 0 ? (
              plans.slice(0, 5).map((plan) => (
                <div
                  key={plan.id}
                  onClick={() => {
                    onSelectPlan(plan);
                    onSelectTab('PLANNER');
                  }}
                  className="p-3 rounded-xl bg-navy-950/70 border border-navy-800/80 hover:border-violet-500/40 hover:bg-navy-950 cursor-pointer transition-all flex items-center justify-between"
                >
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-slate-200 line-clamp-1">
                      "{plan.prompt}"
                    </p>
                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <span>{plan.actions.length} proposed steps</span>
                      <span>•</span>
                      <span>{new Date(plan.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                  <span className="text-xs text-violet-400 font-mono px-2 py-0.5 rounded bg-navy-900 border border-navy-750">
                    Review →
                  </span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-6 text-center">
                No action plans generated yet. Click "Open Planner" to create one.
              </div>
            )}
          </div>
        </div>

        {/* Recent Actions & Approvals */}
        <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-5 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-navy-800 mb-3">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Latest Action Governed Operations
            </h3>
            <button
              type="button"
              onClick={() => onSelectTab('HISTORY')}
              className="text-xs text-violet-400 hover:text-violet-300 flex items-center gap-1 font-medium"
            >
              Full Ledger <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
            {actions.length > 0 ? (
              actions.slice(0, 5).map((act) => (
                <div
                  key={act.id}
                  className="p-3 rounded-xl bg-navy-950/70 border border-navy-800/80 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <PolicyBadge decision={act.policy_decision} size="sm" />
                      <StatusBadge status={act.status} />
                    </div>
                    <span className="font-semibold text-slate-200 line-clamp-1">{act.title}</span>
                  </div>

                  <span className="text-[11px] text-slate-400 shrink-0 font-mono">
                    {new Date(act.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-6 text-center">
                No actions recorded yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
