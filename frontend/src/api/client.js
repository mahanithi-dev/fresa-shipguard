export const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export function api(token) {
  return {
    async request(path, options = {}) {
      const res = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(options.headers || {}),
        },
      });
      if (!res.ok) {
        let errorMsg = res.statusText || "Request failed";
        try {
          const payload = await res.json();
          errorMsg = payload.detail || payload.message || JSON.stringify(payload);
        } catch (e) {
          // Fallback to status text
        }
        const err = new Error(errorMsg);
        err.status = res.status;
        err.retryAfter = res.headers.get("Retry-After");
        throw err;
      }
      const text = await res.text();
      try {
        return text ? JSON.parse(text) : null;
      } catch (e) {
        return text;
      }
    },
  };
}
