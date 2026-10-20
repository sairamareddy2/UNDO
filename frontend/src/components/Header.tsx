import React, { useState } from 'react';
import { Shield, Sparkles, Database, RotateCcw, Loader2, Cpu, ChevronDown, CheckCircle2, XCircle } from 'lucide-react';
import type { HealthStatus, McpStatus } from '../types';

interface Props {
  health: HealthStatus | null;
  mcpStatus: McpStatus | null;
  onResetState: () => Promise<void>;
  isResetting?: boolean;
}

export const Header: React.FC<Props> = ({ health, mcpStatus, onResetState, isResetting = false }) => {
  const [showMcpDetails, setShowMcpDetails] = useState(false);
  const isHealthy = health?.status === 'healthy';
  const isMcpOnline = mcpStatus?.reachable === true;

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
                  Day 2 · MCP Active
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
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-navy-850 text-violet-300 border border-violet-800/40 font-mono text-[11px]">
              <Cpu className="w-3 h-3 text-violet-400" /> Python MCP SDK (Streamable HTTP)
            </span>
          </div>
        </div>

        {/* Right: System Status, MCP Pill, Reset */}
        <div className="flex items-center gap-2.5 text-xs">
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

          {/* MCP Server Status Pill */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowMcpDetails(!showMcpDetails)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border font-mono text-[11px] transition-all ${
                isMcpOnline
                  ? 'bg-purple-950/80 border-purple-500/50 text-purple-200 hover:bg-purple-900/80 shadow-sm shadow-purple-900/20'
                  : 'bg-navy-950 border-navy-750 text-slate-400 hover:text-slate-200'
              }`}
              title="Click to view MCP tools and endpoint"
            >
              <Cpu className={`w-3.5 h-3.5 ${isMcpOnline ? 'text-purple-300' : 'text-slate-500'}`} />
              <span>
                MCP: {isMcpOnline ? `${mcpStatus?.tools_count || 7} Tools` : 'Standby (:8001)'}
              </span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {/* MCP Popover */}
            {showMcpDetails && (
              <div className="absolute right-0 mt-2 w-72 bg-navy-900 border border-navy-750 rounded-xl p-3.5 shadow-2xl z-50 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-navy-800 mb-2">
                  <span className="font-semibold text-slate-200">Official Python MCP Server</span>
                  <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono ${
                    isMcpOnline ? 'bg-emerald-950 text-emerald-300' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {isMcpOnline ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <XCircle className="w-3 h-3 text-slate-400" />}
                    {isMcpOnline ? 'Streamable HTTP' : 'Offline'}
                  </span>
                </div>

                <div className="space-y-1.5 text-[11px] font-mono mb-2 text-slate-400">
                  <div>
                    <span className="text-slate-500">Endpoint: </span>
                    <span className="text-violet-300">{mcpStatus?.endpoint || 'http://127.0.0.1:8001/mcp'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Transport: </span>
                    <span className="text-slate-300">Streamable HTTP (MCP SDK 2.x)</span>
                  </div>
                </div>

                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Exposed Governed Tools ({mcpStatus?.tools?.length || 7})
                </div>
                <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
                  {(mcpStatus?.tools || [
                    'list_groceries',
                    'get_household_state',
                    'get_action_history',
                    'add_grocery_item',
                    'create_reminder',
                    'set_door_lock',
                    'undo_action',
                  ]).map((t) => (
                    <div key={t} className="px-2 py-0.5 rounded bg-navy-950 font-mono text-[11px] text-violet-300 border border-navy-800">
                      {t}
                    </div>
                  ))}
                </div>
              </div>
            )}
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
