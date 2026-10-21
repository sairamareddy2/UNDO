export type PolicyDecision = 'ALLOW' | 'REQUIRE_APPROVAL' | 'BLOCK';

export type ActionStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXECUTED'
  | 'REVERSED'
  | 'BLOCKED'
  | 'FAILED';

export interface Action {
  id: string;
  plan_id: string;
  action_type: string;
  title: string;
  parameters: Record<string, any>;
  policy_decision: PolicyDecision;
  policy_reason: string;
  status: ActionStatus;
  is_reversible: boolean;
  approval_decision?: 'APPROVED' | 'REJECTED' | null;
  approval_notes?: string | null;
  approval_decided_at?: string | null;
  before_state?: Record<string, any> | null;
  after_state?: Record<string, any> | null;
  execution_result?: {
    status?: string;
    message?: string;
    [key: string]: any;
  } | null;
  error_message?: string | null;
  created_at: string;
  executed_at?: string | null;
  reversed_at?: string | null;
}

export interface ActionPlan {
  id: string;
  prompt: string;
  status: string;
  created_at: string;
  updated_at: string;
  actions: Action[];
}

export interface GroceryItem {
  id: number;
  name: string;
  quantity: number;
  category: string;
  is_active: boolean;
  created_at: string;
}

export interface Reminder {
  id: number;
  title: string;
  remind_at: string;
  priority: string;
  is_active: boolean;
  created_at: string;
}

export interface DoorLock {
  id: string;
  name: string;
  is_locked: boolean;
  last_changed_at: string;
}

export interface ApplicationState {
  groceries: GroceryItem[];
  reminders: Reminder[];
  doors: DoorLock[];
}

export interface AuditEvent {
  id: number;
  action_id?: string | null;
  event_type: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface HealthStatus {
  status: string;
  app: string;
  environment: string;
  database_connected: boolean;
  gemini_connected?: boolean;
  gemini_model?: string | null;
  timestamp: string;
}

export interface McpStatus {
  status: 'online' | 'offline';
  reachable: boolean;
  endpoint: string;
  transport: string;
  tools_count: number;
  tools: string[];
}

// --- Safety Simulator Types ---

export type SimulationOverallStatus =
  | 'SAFE IN SIMULATION'
  | 'WARNINGS FOUND'
  | 'BLOCKED BY POLICY'
  | 'SIMULATION FAILED'
  | 'ROLLBACK UNVERIFIED';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface FailureScenario {
  name: string;
  category: string;
  status: 'PASSED' | 'FAILED' | 'WARNING' | 'UNSUPPORTED';
  expected: string;
  observed: string;
}

export interface ProposedChange {
  target: string;
  change_type: string;
  description: string;
  affected_records: number;
  details: Record<string, any>;
}

export interface ReversibilityReport {
  result: 'VERIFIED_REVERSIBLE' | 'NOT_REVERSIBLE' | 'ROLLBACK_FAILED' | 'NOT_TESTED';
  rollback_tested: boolean;
  state_restored: boolean;
  recovery_method: string;
  unverified_fields: string[];
}

export interface SafetyReport {
  simulation_id: string;
  action_id?: string | null;
  action_type: string;
  title: string;
  parameters: Record<string, any>;
  overall_status: SimulationOverallStatus;
  risk_level: RiskLevel;
  risk_rationale: string;
  policy_decision: PolicyDecision;
  policy_reason: string;
  requires_approval: boolean;
  initial_state_summary: Record<string, any>;
  proposed_changes: ProposedChange[];
  validation_results: Record<string, any>;
  failure_scenarios: FailureScenario[];
  reversibility: ReversibilityReport;
  warnings: string[];
  limitations: string[];
  timestamp: string;
}
