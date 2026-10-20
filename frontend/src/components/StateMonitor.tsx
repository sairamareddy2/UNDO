import React from 'react';
import {
  ShoppingCart,
  Bell,
  Lock,
  Unlock,
  RefreshCw,
  Database,
  RotateCcw,
} from 'lucide-react';
import type { ApplicationState } from '../types';

interface Props {
  state: ApplicationState | null;
  onRefresh: () => Promise<void>;
  onReset?: () => Promise<void>;
  isLoading?: boolean;
}

export const StateMonitor: React.FC<Props> = ({
  state,
  onRefresh,
  onReset,
  isLoading = false,
}) => {
  return (
    <div className="bg-navy-900 border border-navy-750/80 rounded-2xl p-5 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-navy-800 mb-4">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-violet-400" />
          <h2 className="text-sm font-semibold text-slate-100 tracking-wide uppercase">
            Live SQLite Database State
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
            className="p-1.5 rounded-lg bg-navy-800 hover:bg-navy-750 text-slate-300 hover:text-white transition-colors"
            title="Refresh database state"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          {onReset && (
            <button
              type="button"
              onClick={onReset}
              disabled={isLoading}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-navy-800 hover:bg-navy-750 text-slate-300 hover:text-rose-300 border border-navy-700/60 transition-colors"
              title="Reset application entities back to baseline demo state"
            >
              <RotateCcw className="w-3 h-3" />
              Reset State
            </button>
          )}
        </div>
      </div>

      {/* Grid of entities: Doors, Groceries, Reminders */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 1. Smart Home Doors */}
        <div className="bg-navy-950/60 rounded-xl p-3.5 border border-navy-800/80">
          <div className="flex items-center justify-between mb-3 text-xs font-semibold text-slate-400">
            <span className="flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-violet-400" />
              Door Locks ({state?.doors?.length || 0})
            </span>
          </div>

          <div className="space-y-2">
            {state?.doors && state.doors.length > 0 ? (
              state.doors.map((door) => (
                <div
                  key={door.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-navy-900 border border-navy-750/60 text-xs"
                >
                  <span className="font-medium text-slate-200">{door.name}</span>
                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold ${
                      door.is_locked
                        ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/30'
                        : 'bg-amber-950/80 text-amber-300 border border-amber-500/40'
                    }`}
                  >
                    {door.is_locked ? (
                      <>
                        <Lock className="w-3 h-3 text-emerald-400" />
                        LOCKED
                      </>
                    ) : (
                      <>
                        <Unlock className="w-3 h-3 text-amber-400" />
                        UNLOCKED
                      </>
                    )}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-3 text-center">No door entities</div>
            )}
          </div>
        </div>

        {/* 2. Grocery List */}
        <div className="bg-navy-950/60 rounded-xl p-3.5 border border-navy-800/80">
          <div className="flex items-center justify-between mb-3 text-xs font-semibold text-slate-400">
            <span className="flex items-center gap-1.5">
              <ShoppingCart className="w-3.5 h-3.5 text-violet-400" />
              Simulated Groceries ({state?.groceries?.length || 0})
            </span>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {state?.groceries && state.groceries.length > 0 ? (
              state.groceries.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-navy-900 border border-navy-750/60 text-xs"
                >
                  <div className="flex flex-col">
                    <span className="font-medium text-slate-200">{item.name}</span>
                    <span className="text-[10px] text-slate-400">{item.category}</span>
                  </div>
                  <span className="font-mono px-2 py-0.5 rounded bg-navy-800 text-violet-300 border border-navy-700 text-xs font-semibold">
                    x{item.quantity}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-3 text-center">Grocery list is empty</div>
            )}
          </div>
        </div>

        {/* 3. Scheduled Reminders */}
        <div className="bg-navy-950/60 rounded-xl p-3.5 border border-navy-800/80">
          <div className="flex items-center justify-between mb-3 text-xs font-semibold text-slate-400">
            <span className="flex items-center gap-1.5">
              <Bell className="w-3.5 h-3.5 text-violet-400" />
              Reminders ({state?.reminders?.length || 0})
            </span>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {state?.reminders && state.reminders.length > 0 ? (
              state.reminders.map((rem) => (
                <div
                  key={rem.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-navy-900 border border-navy-750/60 text-xs"
                >
                  <div className="flex flex-col">
                    <span className="font-medium text-slate-200">{rem.title}</span>
                    <span className="text-[10px] text-violet-400">Scheduled: {rem.remind_at}</span>
                  </div>
                  <span className="uppercase text-[10px] px-1.5 py-0.5 rounded font-mono bg-navy-800 text-slate-400 border border-navy-700">
                    {rem.priority}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-3 text-center">No active reminders</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
