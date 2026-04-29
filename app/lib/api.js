export const API_BASE_URL =
  process.env.NEXT_PUBLIC_AGENTGUARD_API_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

export const WORKSPACE_ID =
  process.env.NEXT_PUBLIC_AGENTGUARD_WORKSPACE_ID || "default";

async function getClerkToken() {
  if (typeof window === "undefined") {
    return null;
  }

  const clerk = window.Clerk;
  if (!clerk?.session) {
    return null;
  }

  return clerk.session.getToken();
}

export async function apiFetch(path, options = {}) {
  const token = await getClerkToken();
  const headers = {
    "x-workspace-id": WORKSPACE_ID,
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    ...options,
    headers,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json();
}
