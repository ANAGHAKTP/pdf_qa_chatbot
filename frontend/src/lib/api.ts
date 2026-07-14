const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Helper to retrieve auth headers
export function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Save authentication tokens
export function saveTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem("access_token", accessToken);
  localStorage.setItem("refresh_token", refreshToken);
}

// Clear authentication tokens
export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export async function request(
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Access token expired, attempt token refresh
    const refreshed = await attemptTokenRefresh();
    if (refreshed) {
      // Retry original request with new token
      return request(endpoint, options);
    } else {
      clearTokens();
      if (typeof window !== "undefined") {
        window.location.reload();
      }
      throw new Error("Session expired. Please login again.");
    }
  }

  if (response.status === 204) {
    return true;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong");
  }

  return data;
}

// Attempt JWT token refresh
async function attemptTokenRefresh(): Promise<boolean> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return false;

  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (response.ok) {
      const data = await response.json();
      saveTokens(data.access_token, data.refresh_token);
      return true;
    }
  } catch (err) {
    console.error("Token refresh failed:", err);
  }
  return false;
}
