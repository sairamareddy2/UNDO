import React from 'react';
import {
  LayoutDashboard,
  Layers,
  History,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  Sliders,
} from 'lucide-react';

export type NavTab = 'DASHBOARD' | 'PLANNER' | 'HISTORY';

interface Props {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  pendingApprovalsCount: number;
  completedCount: number;
}

export const Sidebar: React.FC<Props> = ({
  currentTab,
  onSelectTab,
  pendingApprovalsCount,
  completedCount,
}) => {
  const navItems = [
    {
      id: 'DASHBOARD' as NavTab,
      label: 'Dashboard',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      id: 'PLANNER' as NavTab,
      label: 'Action Planner',
      icon: Layers,
      badge: pendingApprovalsCount > 0 ? `${pendingApprovalsCount} Need Approval` : null,
      badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-600/50',
    },
    {
      id: 'HISTORY' as NavTab,
      label: 'Action History',
      icon: History,
      badge: completedCount > 0 ? `${completedCount}` : null,
      badgeColor: 'bg-navy-800 text-slate-300 border-navy-700',
    },
  ];

  return (
    <aside className="w-64 bg-navy-900 border-r border-navy-750/70 p-4 flex flex-col justify-between shrink-0">
      <div className="space-y-6">
        {/* Navigation Section */}
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 px-3 mb-2 font-semibold">
            Navigation
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;

              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-violet-600/20 text-violet-300 border border-violet-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-navy-850'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-violet-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-mono border ${
                        item.badgeColor || ''
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Policy Engine Rules Overview Card */}
        <div className="bg-navy-950/80 border border-navy-800 rounded-xl p-3.5 space-y-2.5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <span className="flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-violet-400" />
              Policy Matrix
            </span>
          </div>

          <div className="space-y-2 text-[11px]">
            <div className="flex items-center justify-between p-1.5 rounded bg-navy-900 border border-navy-800">
              <span className="text-slate-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                Grocery / Reminders
              </span>
              <span className="font-semibold text-emerald-400">ALLOW</span>
            </div>

            <div className="flex items-center justify-between p-1.5 rounded bg-navy-900 border border-navy-800">
              <span className="text-slate-400 flex items-center gap-1.5">
                <ShieldAlert className="w-3 h-3 text-amber-400" />
                Door Locks & Bulk
              </span>
              <span className="font-semibold text-amber-400">APPROVAL</span>
            </div>

            <div className="flex items-center justify-between p-1.5 rounded bg-navy-900 border border-navy-800">
              <span className="text-slate-400 flex items-center gap-1.5">
                <ShieldX className="w-3 h-3 text-rose-400" />
                Destructive / Unknown
              </span>
              <span className="font-semibold text-rose-400">BLOCK</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-4 border-t border-navy-800 text-[11px] text-slate-400 space-y-1">
        <div className="flex items-center justify-between">
          <span>Engine Status:</span>
          <span className="text-emerald-400 font-mono font-medium">Deterministic</span>
        </div>
        <div className="flex items-center justify-between">
          <span>AWS Adapter:</span>
          <span className="text-slate-400 font-mono">Milestone 2</span>
        </div>
      </div>
    </aside>
  );
};
