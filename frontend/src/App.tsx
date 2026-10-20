import React, { useState, useEffect, useCallback } from 'react';
import { api } from './services/api';
import type {
  Action,
  ActionPlan,
  ApplicationState,
  AuditEvent,
  HealthStatus,
  McpStatus,
} from './types';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import type { NavTab } from './components/Sidebar';
import { ChatInput } from './components/ChatInput';
import { ActionPlanView } from './components/ActionPlanView';
import { HistoryView } from './components/HistoryView';
import { DashboardView } from './components/DashboardView';
import { CheckCircle2, AlertTriangle, X } from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('DASHBOARD');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [mcpStatus, setMcpStatus] = useState<McpStatus | null>(null);
  const [plans, setPlans] = useState<ActionPlan[]>([]);
  const [activePlan, setActivePlan] = useState<ActionPlan | null>(null);
  const [actions, setActions] = useState<Action[]>([]);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [liveState, setLiveState] = useState<ApplicationState | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isCreatingPlan, setIsCreatingPlan] = useState<boolean>(false);
  const [isExecutingPlan, setIsExecutingPlan] = useState<boolean>(false);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message });
    setTimeout(() => {
      setNotification((prev) => (prev?.message === message ? null : prev));
    }, 5000);
  };

  const loadAllData = useCallback(async () => {
    try {
      const [h, m, p, a, s, aud] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getMcpStatus().catch(() => null),
        api.getPlans().catch(() => []),
        api.listActions().catch(() => []),
        api.getLiveState().catch(() => null),
        api.getAuditEvents().catch(() => []),
      ]);

      if (h) setHealth(h);
      if (m) setMcpStatus(m);
      setPlans(p);
      setActions(a);
      if (s) setLiveState(s);
      setAuditEvents(aud);

      // Keep active plan in sync
      if (activePlan) {
        const refreshedPlan = p.find((item: ActionPlan) => item.id === activePlan.id);
        if (refreshedPlan) setActivePlan(refreshedPlan);
      } else if (p.length > 0) {
        setActivePlan(p[0]);
      }
    } catch (err: any) {
      console.error('Failed to load initial data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [activePlan]);

  useEffect(() => {
    loadAllData();
    const interval = setInterval(() => {
      // Background poll health, MCP status & live state
      api.getHealth().then(setHealth).catch(() => {});
      api.getMcpStatus().then(setMcpStatus).catch(() => {});
      api.getLiveState().then(setLiveState).catch(() => {});
    }, 8000);
    return () => clearInterval(interval);
  }, [loadAllData]);

  // Handle plan creation
  const handleCreatePlan = async (prompt: string) => {
    setIsCreatingPlan(true);
    try {
      const newPlan = await api.createPlan(prompt);
      setActivePlan(newPlan);
      setPlans((prev) => [newPlan, ...prev]);
      setCurrentTab('PLANNER');
      showNotification('success', `Generated action plan with ${newPlan.actions.length} step(s).`);
      await loadAllData();
    } catch (err: any) {
      showNotification('error', `Failed to create plan: ${err.message}`);
    } finally {
      setIsCreatingPlan(false);
    }
  };

  // Handle action approval
  const handleApproveAction = async (actionId: string) => {
    try {
      const updated = await api.approveAction(actionId);
      showNotification('success', `Approved: ${updated.title}`);
      await loadAllData();
    } catch (err: any) {
      showNotification('error', `Approval failed: ${err.message}`);
    }
  };

  // Handle action rejection
  const handleRejectAction = async (actionId: string) => {
    try {
      const updated = await api.rejectAction(actionId);
      showNotification('info', `Rejected: ${updated.title}`);
      await loadAllData();
    } catch (err: any) {
      showNotification('error', `Rejection failed: ${err.message}`);
    }
  };

  // Handle action execution
  const handleExecuteAction = async (actionId: string) => {
    try {
      const executed = await api.executeAction(actionId);
      showNotification(
        'success',
        executed.execution_result?.message || `Executed: ${executed.title}`
      );
      await loadAllData();
    } catch (err: any) {
      showNotification('error', `Execution failed: ${err.message}`);
    }
  };

  // Handle action undo / reversal
  const handleUndoAction = async (actionId: string) => {
    try {
      const undone = await api.undoAction(actionId);
      showNotification('info', `Reversed & Restored state for: ${undone.title}`);
      await loadAllData();
    } catch (err: any) {
      showNotification('error', `Undo failed: ${err.message}`);
    }
  };

  // Handle executing all eligible actions in plan
  const handleExecutePlan = async (planId: string) => {
    setIsExecutingPlan(true);
    try {
      const updatedPlan = await api.executePlan(planId);
      setActivePlan(updatedPlan);
      showNotification('success', 'Executed all eligible approved actions in plan.');
      await loadAllData();
    } catch (err: any) {
      showNotification('error', `Plan execution error: ${err.message}`);
    } finally {
      setIsExecutingPlan(false);
    }
  };

  // Handle resetting simulated database state
  const handleResetState = async () => {
    try {
      await api.resetState();
      showNotification('info', 'Reset database entities to clean baseline.');
      await loadAllData();
    } catch (err: any) {
      showNotification('error', `Reset failed: ${err.message}`);
    }
  };

  const pendingApprovalsCount = actions.filter(
    (a) => a.policy_decision === 'REQUIRE_APPROVAL' && a.status === 'PENDING'
  ).length;

  const completedCount = actions.filter((a) => a.status === 'EXECUTED').length;

  return (
    <div className="min-h-screen bg-navy-950 text-slate-100 flex flex-col font-sans selection:bg-violet-900 selection:text-violet-200">
      {/* Top App Header */}
      <Header
        health={health}
        mcpStatus={mcpStatus}
        onResetState={handleResetState}
      />

      {/* Main Layout Container */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left Sidebar Navigation */}
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          pendingApprovalsCount={pendingApprovalsCount}
          completedCount={completedCount}
        />

        {/* Center Main Content Area */}
        <main className="flex-1 p-6 overflow-y-auto max-w-7xl mx-auto w-full space-y-6">
          {/* Toast Notification Banner */}
          {notification && (
            <div
              className={`p-3.5 rounded-xl border flex items-center justify-between shadow-lg text-xs font-medium animate-in fade-in slide-in-from-top-2 duration-200 ${
                notification.type === 'success'
                  ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-200'
                  : notification.type === 'error'
                  ? 'bg-rose-950/80 border-rose-500/40 text-rose-200'
                  : 'bg-violet-950/80 border-violet-500/40 text-violet-200'
              }`}
            >
              <div className="flex items-center gap-2">
                {notification.type === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                )}
                <span>{notification.message}</span>
              </div>
              <button
                type="button"
                onClick={() => setNotification(null)}
                className="text-slate-400 hover:text-white p-1 rounded transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Chat-style Command Input (Visible in Planner & Dashboard) */}
          {currentTab !== 'HISTORY' && (
            <ChatInput onSubmit={handleCreatePlan} isLoading={isCreatingPlan} />
          )}

          {/* Active Tab View Rendering */}
          {currentTab === 'DASHBOARD' && (
            <DashboardView
              plans={plans}
              actions={actions}
              state={liveState}
              onSelectTab={setCurrentTab}
              onRefreshState={loadAllData}
              onResetState={handleResetState}
              onSelectPlan={(plan) => setActivePlan(plan)}
              isLoading={isLoading}
            />
          )}

          {currentTab === 'PLANNER' && (
            <ActionPlanView
              plan={activePlan}
              onApprove={handleApproveAction}
              onReject={handleRejectAction}
              onExecute={handleExecuteAction}
              onUndo={handleUndoAction}
              onExecutePlan={handleExecutePlan}
              isExecutingPlan={isExecutingPlan}
            />
          )}

          {currentTab === 'HISTORY' && (
            <HistoryView
              actions={actions}
              auditEvents={auditEvents}
              onUndo={handleUndoAction}
              onRefresh={loadAllData}
              isLoading={isLoading}
            />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
