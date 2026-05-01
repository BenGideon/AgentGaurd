import { AgentGuardError } from "./errors";
import type { AgentGuardConfig, CallActionResponse, SimulationParams, SimulationResponse } from "./types";

type RequestOptions = {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
  useAgentKey?: boolean;
  useAuthToken?: boolean;
};

export class AgentGuard {
  private readonly apiKey: string;
  private readonly baseUrl: string;
  private readonly workspaceId: string;
  private readonly authToken?: string;

  constructor(config: AgentGuardConfig) {
    if (!config.apiKey) {
      throw new AgentGuardError("AgentGuard apiKey is required");
    }

    this.apiKey = config.apiKey;
    this.baseUrl = (config.baseUrl || "http://localhost:8000").replace(/\/+$/, "");
    this.workspaceId = config.workspaceId || "default";
    this.authToken = config.authToken;
  }

  async callAction(action: string, input: any): Promise<CallActionResponse> {
    const response = await this.request("/actions/call", {
      method: "POST",
      useAgentKey: true,
      body: { action, input },
    });

    if (response.status === "completed") {
      return { status: "completed", result: response.result, raw: response };
    }

    if (response.status === "pending_approval") {
      return {
        status: "pending_approval",
        approvalId: String(response.approval_id),
        raw: response,
      };
    }

    if (response.status === "blocked") {
      throw new AgentGuardError(response.message || "Action blocked", {
        status: response.status,
        data: response,
      });
    }

    throw new AgentGuardError("Unexpected AgentGuard action response", {
      status: response.status,
      data: response,
    });
  }

  async simulate(params: SimulationParams): Promise<SimulationResponse> {
    const agentId = params.agent_id || (await this.resolveAgentId());

    return this.request("/simulate", {
      method: "POST",
      useAuthToken: true,
      body: {
        agent_id: agentId,
        action: params.action,
        input: params.input,
      },
    });
  }

  async listActions(): Promise<any> {
    return this.request("/actions", { method: "GET" });
  }

  private async resolveAgentId(): Promise<string> {
    const agents = await this.request("/agents", { method: "GET" });
    const agent = Array.isArray(agents)
      ? agents.find((item) => item?.api_key === this.apiKey)
      : null;

    if (!agent?.id) {
      throw new AgentGuardError("agent_id is required for simulation when the API key cannot be resolved");
    }

    return agent.id;
  }

  private async request(path: string, options: RequestOptions = {}): Promise<any> {
    const headers: Record<string, string> = {
      "x-workspace-id": this.workspaceId,
      ...(options.headers || {}),
    };

    if (options.useAgentKey) {
      headers["x-agent-key"] = this.apiKey;
    }

    if (options.useAuthToken) {
      if (!this.authToken) {
        throw new AgentGuardError("authToken is required for this request");
      }
      headers.Authorization = `Bearer ${this.authToken}`;
    }

    let body: string | undefined;
    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(options.body);
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method: options.method || "GET",
      headers,
      body,
    });

    const data = await this.parseResponse(response);

    if (!response.ok) {
      throw new AgentGuardError(this.errorMessage(data, response), {
        statusCode: response.status,
        data,
      });
    }

    return data;
  }

  private async parseResponse(response: Response): Promise<any> {
    const text = await response.text();
    if (!text) {
      return null;
    }

    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  private errorMessage(data: any, response: Response): string {
    if (typeof data === "string" && data.trim()) {
      return data;
    }

    if (data?.detail) {
      return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    }

    if (data?.message) {
      return data.message;
    }

    return `AgentGuard request failed with status ${response.status}`;
  }
}
