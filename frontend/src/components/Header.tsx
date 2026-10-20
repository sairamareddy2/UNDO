import React from 'react';
import { Shield, Sparkles, Database, RotateCcw, Loader2 } from 'lucide-react';
import type { HealthStatus } from '../types';

interface Props {
  health: HealthStatus | null;
  onResetState: () => Promise<void>;
  isResetting?: boolean;
}

export const Header: React.FC<Props> = ({ health, onResetState, isResetting = false }) => {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="bg-navy-900/90 border-b border-navy-750/70 sticky top-0 z-30 backdrop-blur-md px-6 py-3.5">
      <div className="flex items-center justify-between">
        {/* Left: Branding & Tag */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-900/40">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-wider text-slate-100">
                  UNDO
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-800/40">
                  v1.0 Milestone
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium">
                Alexa+ Action Governance & Reversibility Layer
              </p>
            </div>
          </div>

          <div className="hidden lg:flex items-center gap-2 pl-4 border-l border-navy-750 text-xs">
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-navy-850 text-slate-300 border border-navy-750">
              <Sparkles className="w-3 h-3 text-violet-400" /> Alexa+ Web Track
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-navy-850 text-slate-400 border border-navy-750">
              AWS Builder Integration (Roadmap)
            </span>
          </div>
        </div>

        {/* Right: System Status & Reset */}
        <div className="flex items-center gap-3 text-xs">
          {/* Quick reset button */}
          <button
            type="button"
            disabled={isResetting}
            onClick={() => onResetState()}
            className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-800 hover:bg-navy-750 text-slate-300 hover:text-white border border-navy-700 transition-all text-xs"
            title="Reset database to demo state"
          >
            {isResetting ? <Loader2 className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
            <span>Reset Demo DB</span>
          </button>

          {/* SQLite Badge */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-950 border border-navy-750 font-mono text-slate-300">
            <Database className="w-3.5 h-3.5 text-violet-400" />
            <span>SQLite Active</span>
          </div>

          {/* Backend Status indicator */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-navy-950 border border-navy-750 text-slate-300">
            {isHealthy ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[11px] font-medium text-emerald-400">Backend Ready</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span className="text-[11px] font-medium text-amber-400">Connecting...</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
