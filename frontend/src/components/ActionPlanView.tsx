import React from 'react';
import { Play, Sparkles, Layers, CheckCircle2 } from 'lucide-react';
import type { ActionPlan } from '../types';
import { ActionCard } from './ActionCard';

interface Props {
  plan: ActionPlan | null;
  onApprove: (actionId: string) => Promise<void>;
  onReject: (actionId: string) => Promise<void>;
  onExecute: (actionId: string) => Promise<void>;
  onUndo: (actionId: string) => Promise<void>;
  onExecutePlan?: (planId: string) => Promise<void>;
  isExecutingPlan?: boolean;
}

export const ActionPlanView: React.FC<Props> = ({
  plan,
  onApprove,
  onReject,
  onExecute,
  onUndo,
  onExecutePlan,
  isExecutingPlan = false,
}) => {
  if (!plan) {
    return (
      <div className="bg-navy-900 border border-dashed border-navy-750 rounded-2xl p-12 text-center">
        <div className="w-12 h-12 rounded-2xl bg-navy-800 text-violet-400 mx-auto flex items-center justify-center mb-4 border border-violet-900/30">
          <Sparkles className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-slate-200 mb-1">No Active Action Plan</h3>
        <p className="text-xs text-slate-400 max-w-sm mx-auto">
          Enter an Alexa+ simulated voice instruction above to generate and govern an action plan.
        </p>
      </div>
    );
  }

  const eligibleCount = plan.actions.filter(
    (a) =>
      a.status === 'APPROVED' ||
      (a.status === 'PENDING' && a.policy_decision === 'ALLOW')
  ).length;

  const completedCount = plan.actions.filter((a) => a.status === 'EXECUTED' || a.status === 'REVERSED').length;

  return (
    <div className="space-y-4">
      {/* Plan Header Card */}
      <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-5 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-violet-950/70 text-violet-300 border border-violet-700/40">
                Plan ID: {plan.id.slice(0, 8)}...
              </span>
              <span className="text-xs text-slate-400">
                Created: {new Date(plan.created_at).toLocaleTimeString()}
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Layers className="w-5 h-5 text-violet-400" />
              "{plan.prompt}"
            </h2>
          </div>

          {/* Execute All Eligible button */}
          {eligibleCount > 0 && onExecutePlan && (
            <button
              type="button"
              disabled={isExecutingPlan}
              onClick={() => onExecutePlan(plan.id)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-900/40 transition-all hover:scale-105 active:scale-95 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Execute All Eligible ({eligibleCount})
            </button>
          )}

          {eligibleCount === 0 && completedCount > 0 && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/50 text-emerald-400 border border-emerald-500/30 text-xs font-medium">
              <CheckCircle2 className="w-4 h-4" />
              Plan Execution Finished
            </div>
          )}
        </div>

        {/* Plan summary chips */}
        <div className="mt-4 pt-3 border-t border-navy-800 flex items-center gap-3 flex-wrap text-xs">
          <span className="text-slate-400">
            Total Steps: <strong className="text-slate-200">{plan.actions.length}</strong>
          </span>
          <span className="text-emerald-400">
            ALLOW: <strong>{plan.actions.filter((a) => a.policy_decision === 'ALLOW').length}</strong>
          </span>
          <span className="text-amber-400">
            REQUIRE APPROVAL: <strong>{plan.actions.filter((a) => a.policy_decision === 'REQUIRE_APPROVAL').length}</strong>
          </span>
          <span className="text-rose-400">
            BLOCK: <strong>{plan.actions.filter((a) => a.policy_decision === 'BLOCK').length}</strong>
          </span>
        </div>
      </div>

      {/* Action Cards List */}
      <div className="space-y-3">
        {plan.actions.map((action) => (
          <ActionCard
            key={action.id}
            action={action}
            onApprove={onApprove}
            onReject={onReject}
            onExecute={onExecute}
            onUndo={onUndo}
          />
        ))}
      </div>
    </div>
  );
};
