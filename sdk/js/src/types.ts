export type AgentGuardConfig = {
  apiKey: string;
  baseUrl?: string;
  workspaceId?: string;
  authToken?: string;
};

export type CallActionResponse =
  | { status: "completed"; result: any; raw: any }
  | { status: "pending_approval"; approvalId: string; raw: any };

export type SimulationParams = {
  action: string;
  input: any;
  agent_id?: string;
};

export type SimulationResponse = {
  decision: string;
  risk_level: string;
  matched_policy: any;
  reason: string;
};
