import type {
  Action,
  ActionPlan,
  ApplicationState,
  AuditEvent,
  HealthStatus,
  McpStatus,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errorDetail = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const body = await response.json();
          if (body && body.detail) {
            errorDetail = body.detail;
          }
        } catch (_) {
          // Response body was not JSON
        }
        throw new Error(errorDetail);
      }
      return (await response.json()) as T;
    } catch (err: any) {
      console.error(`API Error on [${options.method || 'GET'} ${url}]:`, err);
      throw err;
    }
  }

  // Health & MCP Status
  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health');
  }

  async getMcpStatus(): Promise<McpStatus> {
    return this.request<McpStatus>('/mcp/status');
  }

  // Plans
  async createPlan(prompt: string): Promise<ActionPlan> {
    return this.request<ActionPlan>('/plans', {
      method: 'POST',
      body: JSON.stringify({ prompt }),
    });
  }

  async getPlans(): Promise<ActionPlan[]> {
    return this.request<ActionPlan[]>('/plans');
  }

  async getPlan(id: string): Promise<ActionPlan> {
    return this.request<ActionPlan>(`/plans/${id}`);
  }

  async executePlan(planId: string): Promise<ActionPlan> {
    return this.request<ActionPlan>(`/plans/${planId}/execute`, {
      method: 'POST',
    });
  }

  // Actions
  async listActions(filters?: { planId?: string; status?: string; policy?: string }): Promise<Action[]> {
    const params = new URLSearchParams();
    if (filters?.planId) params.append('plan_id', filters.planId);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.policy) params.append('policy', filters.policy);

    const qs = params.toString();
    return this.request<Action[]>(`/actions${qs ? `?${qs}` : ''}`);
  }

  async approveAction(actionId: string, notes?: string): Promise<Action> {
    return this.request<Action>(`/actions/${actionId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved: true, notes }),
    });
  }

  async rejectAction(actionId: string, notes?: string): Promise<Action> {
    return this.request<Action>(`/actions/${actionId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ approved: false, notes }),
    });
  }

  async executeAction(actionId: string): Promise<Action> {
    return this.request<Action>(`/actions/${actionId}/execute`, {
      method: 'POST',
    });
  }

  async undoAction(actionId: string): Promise<Action> {
    return this.request<Action>(`/actions/${actionId}/undo`, {
      method: 'POST',
    });
  }

  // Live Application State
  async getLiveState(): Promise<ApplicationState> {
    return this.request<ApplicationState>('/state');
  }

  async getAuditEvents(): Promise<AuditEvent[]> {
    return this.request<AuditEvent[]>('/state/audit-events');
  }

  async resetState(): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>('/state/reset', {
      method: 'POST',
    });
  }
}

export const api = new ApiService();
