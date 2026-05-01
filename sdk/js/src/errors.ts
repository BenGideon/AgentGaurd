export class AgentGuardError extends Error {
  status?: string;
  statusCode?: number;
  data?: any;

  constructor(message: string, options: { status?: string; statusCode?: number; data?: any } = {}) {
    super(message);
    this.name = "AgentGuardError";
    this.status = options.status;
    this.statusCode = options.statusCode;
    this.data = options.data;
  }
}
