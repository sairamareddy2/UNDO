import React from 'react';
import { ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react';
import type { PolicyDecision } from '../types';

interface Props {
  decision: PolicyDecision;
  showIcon?: boolean;
  size?: 'sm' | 'md';
}

export const PolicyBadge: React.FC<Props> = ({ decision, showIcon = true, size = 'sm' }) => {
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm font-medium';

  switch (decision) {
    case 'ALLOW':
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full font-medium tracking-wide bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 ${sizeClasses}`}
          title="Policy: ALLOW (Action is safe for automated execution)"
        >
          {showIcon && <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />}
          ALLOW
        </span>
      );
    case 'REQUIRE_APPROVAL':
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full font-medium tracking-wide bg-amber-950/60 text-amber-300 border border-amber-500/40 ${sizeClasses}`}
          title="Policy: REQUIRE APPROVAL (High impact: requires human confirmation)"
        >
          {showIcon && <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />}
          REQUIRE APPROVAL
        </span>
      );
    case 'BLOCK':
      return (
        <span
          className={`inline-flex items-center gap-1.5 rounded-full font-medium tracking-wide bg-rose-950/60 text-rose-400 border border-rose-500/40 ${sizeClasses}`}
          title="Policy: BLOCK (Prohibited or invalid action)"
        >
          {showIcon && <ShieldX className="w-3.5 h-3.5 text-rose-400" />}
          BLOCK
        </span>
      );
    default:
      return null;
  }
};
