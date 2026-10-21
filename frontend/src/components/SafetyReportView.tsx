import React from 'react';
import {
  ShieldCheck,
  ShieldX,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  RotateCcw,
  Play,
  Check,
  Database,
  Layers,
  Info,
  X,
  Lock,
} from 'lucide-react';
import type { SafetyReport } from '../types';

interface Props {
  report: SafetyReport;
  onClose: () => void;
  onExecute?: () => void;
  onApprove?: () => void;
  isProcessing?: boolean;
}

export const SafetyReportView: React.FC<Props> = ({
  report,
  onClose,
  onExecute,
  onApprove,
  isProcessing = false,
}) => {
  const isBlocked = report.policy_decision === 'BLOCK';
  const needsApproval = report.requires_approval;

  // Status badge styling
  const getStatusBadge = () => {
    switch (report.overall_status) {
      case 'SAFE IN SIMULATION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 shadow-sm shadow-emerald-900/30">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            SAFE IN SIMULATION
          </span>
        );
      case 'WARNINGS FOUND':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-950/80 text-amber-300 border border-amber-500/40 shadow-sm shadow-amber-900/30">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            WARNINGS FOUND
          </span>
        );
      case 'BLOCKED BY POLICY':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-950/80 text-rose-300 border border-rose-500/40 shadow-sm shadow-rose-900/30">
            <ShieldX className="w-4 h-4 text-rose-400" />
            BLOCKED BY POLICY
          </span>
        );
      case 'ROLLBACK UNVERIFIED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-purple-950/80 text-purple-300 border border-purple-500/40 shadow-sm">
            <RotateCcw className="w-4 h-4 text-purple-400" />
            ROLLBACK UNVERIFIED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-950/80 text-rose-300 border border-rose-500/40 shadow-sm">
            <XCircle className="w-4 h-4 text-rose-400" />
            SIMULATION FAILED
          </span>
        );
    }
  };

  // Risk badge styling
  const getRiskBadge = () => {
    switch (report.risk_level) {
      case 'LOW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-700/40">
            RISK: LOW
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-amber-950/60 text-amber-300 border border-amber-700/40">
            RISK: MEDIUM
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-orange-950/60 text-orange-300 border border-orange-700/40">
            RISK: HIGH
          </span>
        );
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-bold bg-rose-950/80 text-rose-200 border border-rose-600/50">
            RISK: CRITICAL
          </span>
        );
    }
  };

  return (
    <div className="mt-4 bg-navy-950 border border-violet-900/40 rounded-xl p-4 sm:p-5 shadow-2xl space-y-4 animate-in fade-in duration-200">
      {/* Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-navy-800">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="w-8 h-8 rounded-lg bg-violet-950 flex items-center justify-center border border-violet-700/50 text-violet-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-100">
                Safety Simulator Report
              </h4>
              <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-navy-900 text-slate-400 border border-navy-800">
                {report.simulation_id}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Evaluated in isolated temporary sandbox · Real database remained completely untouched
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {getStatusBadge()}
          {getRiskBadge()}
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-navy-800/80 transition-colors"
            title="Dismiss report"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Rationale & Policy Callout */}
      <div className="bg-navy-900/90 border border-navy-800 rounded-lg p-3 text-xs space-y-1.5">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-violet-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-slate-300 font-semibold">Risk Analysis: </span>
            <span className="text-slate-300">{report.risk_rationale}</span>
          </div>
        </div>
        <div className="flex items-center gap-3 pt-1 text-[11px] text-slate-400 border-t border-navy-850">
          <span>
            Policy Engine:{' '}
            <strong className={
              report.policy_decision === 'ALLOW'
                ? 'text-emerald-400'
                : report.policy_decision === 'REQUIRE_APPROVAL'
                ? 'text-amber-400'
                : 'text-rose-400'
            }>
              {report.policy_decision}
            </strong>
          </span>
          <span>·</span>
          <span>
            Human Approval:{' '}
            <strong className={report.requires_approval ? 'text-amber-400' : 'text-slate-300'}>
              {report.requires_approval ? 'Required' : 'Not Required'}
            </strong>
          </span>
        </div>
      </div>

      {/* Proposed Changes Section */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
          <Database className="w-3.5 h-3.5 text-violet-400" />
          <span>Projected Database Changes ({report.proposed_changes.length})</span>
        </div>
        <div className="bg-navy-900 border border-navy-850 rounded-lg overflow-hidden">
          <div className="divide-y divide-navy-850">
            {report.proposed_changes.map((change, idx) => (
              <div key={idx} className="p-2.5 text-xs flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                    change.change_type === 'INSERT'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/40'
                      : change.change_type === 'UPDATE'
                      ? 'bg-blue-950 text-blue-300 border border-blue-800/40'
                      : change.change_type === 'DELETE'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800/40'
                      : 'bg-rose-950 text-rose-300 border border-rose-800/40'
                  }`}>
                    {change.change_type}
                  </span>
                  <span className="text-slate-300">{change.description}</span>
                </div>
                <div className="text-[11px] text-slate-400 font-mono">
                  Target: <span className="text-slate-300">{change.target}</span> · Records: {change.affected_records}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Deterministic Failure Scenarios */}
      <div className="space-y-1.5">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300">
          <Layers className="w-3.5 h-3.5 text-violet-400" />
          <span>Failure Injections &amp; Boundary Scenarios Tested ({report.failure_scenarios.length})</span>
        </div>
        <div className="bg-navy-900 border border-navy-850 rounded-lg overflow-hidden">
          <div className="divide-y divide-navy-850">
            {report.failure_scenarios.map((sc, idx) => (
              <div key={idx} className="p-2.5 text-xs space-y-1">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200">{sc.name}</span>
                    <span className="text-[10px] text-slate-400 bg-navy-800 px-1.5 py-0.5 rounded">
                      {sc.category}
                    </span>
                  </div>
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                    sc.status === 'PASSED'
                      ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/40'
                      : sc.status === 'WARNING'
                      ? 'bg-amber-950/80 text-amber-300 border border-amber-800/40'
                      : sc.status === 'UNSUPPORTED'
                      ? 'bg-slate-800 text-slate-400 border border-slate-700/50'
                      : 'bg-rose-950/80 text-rose-300 border border-rose-800/40'
                  }`}>
                    {sc.status === 'PASSED' && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                    {sc.status === 'WARNING' && <AlertTriangle className="w-3 h-3 text-amber-400" />}
                    {sc.status === 'FAILED' && <XCircle className="w-3 h-3 text-rose-400" />}
                    {sc.status === 'UNSUPPORTED' && <HelpCircle className="w-3 h-3 text-slate-400" />}
                    {sc.status}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400">
                  <span className="text-slate-400">Observed: </span>
                  <span className="text-slate-300">{sc.observed}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recovery & Reversibility Verification */}
      <div className="bg-navy-900/70 border border-navy-800 rounded-lg p-3 text-xs space-y-2">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-1.5 font-semibold text-slate-200">
            <RotateCcw className="w-3.5 h-3.5 text-purple-400" />
            <span>Rollback Verification</span>
          </div>
          <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
            report.reversibility.result === 'VERIFIED_REVERSIBLE'
              ? 'bg-purple-950 text-purple-300 border border-purple-700/50'
              : report.reversibility.result === 'NOT_REVERSIBLE'
              ? 'bg-rose-950 text-rose-300 border border-rose-700/50'
              : 'bg-amber-950 text-amber-300 border border-amber-700/50'
          }`}>
            {report.reversibility.result.replace(/_/g, ' ')}
          </span>
        </div>
        <p className="text-[11px] text-slate-300">
          <span className="text-slate-400">Method: </span>
          {report.reversibility.recovery_method}
        </p>
        <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-navy-850">
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Rollback Tested:</span>
            <strong className={report.reversibility.rollback_tested ? 'text-emerald-400' : 'text-slate-400'}>
              {report.reversibility.rollback_tested ? 'Yes' : 'No'}
            </strong>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">State Restored:</span>
            <strong className={report.reversibility.state_restored ? 'text-emerald-400' : 'text-slate-400'}>
              {report.reversibility.state_restored ? 'Verified (100% Match)' : 'Not Verified'}
            </strong>
          </div>
        </div>
      </div>

      {/* Warnings & Limitations Callout */}
      {(report.warnings.length > 0 || report.limitations.length > 0) && (
        <div className="bg-navy-900/50 border border-navy-800 rounded-lg p-3 text-[11px] space-y-2">
          {report.warnings.length > 0 && (
            <div className="space-y-1">
              <span className="font-semibold text-amber-400 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" /> Simulation Warnings:
              </span>
              <ul className="list-disc list-inside text-amber-200/90 pl-1 space-y-0.5">
                {report.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="space-y-1">
            <span className="font-semibold text-slate-400 flex items-center gap-1">
              <Info className="w-3.5 h-3.5 text-slate-400" /> Limitations &amp; Disclaimers:
            </span>
            <ul className="list-disc list-inside text-slate-400 pl-1 space-y-0.5">
              {report.limitations.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Footer Controls: Continue to Execution */}
      <div className="pt-3 border-t border-navy-800 flex items-center justify-between flex-wrap gap-3">
        <div className="text-[11px] text-slate-400">
          {isBlocked ? (
            <span className="text-rose-400 font-semibold flex items-center gap-1">
              <Lock className="w-3.5 h-3.5" /> Policy Engine blocks real execution of this action.
            </span>
          ) : (
            <span>Execution re-verifies policy and approval at runtime.</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-navy-850 hover:bg-navy-800 border border-navy-750 transition-colors"
          >
            Dismiss Report
          </button>

          {!isBlocked && needsApproval && onApprove && (
            <button
              type="button"
              disabled={isProcessing}
              onClick={onApprove}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              <Check className="w-3.5 h-3.5" />
              Approve for Execution
            </button>
          )}

          {!isBlocked && !needsApproval && onExecute && (
            <button
              type="button"
              disabled={isProcessing}
              onClick={onExecute}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-violet-600 hover:bg-violet-500 text-white shadow-md shadow-violet-900/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              Continue to Execution
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
