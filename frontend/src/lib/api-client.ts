const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

export class APIError extends Error {
  status: number;
  detail: any;

  constructor(message: string, status: number, detail: any) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.detail = detail;
  }
}

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
}

export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const token = sessionStorage.getItem("token");
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let url = `${BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;

  if (options.params) {
    const query = new URLSearchParams();
    Object.entries(options.params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        query.append(key, String(val));
      }
    });
    const queryString = query.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      sessionStorage.removeItem("token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    let errorDetail = "An unexpected error occurred.";
    let rawDetail: any = null;
    try {
      const data = await response.json();
      rawDetail = data;
      if (data && data.detail) {
        if (typeof data.detail === "string") {
          errorDetail = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorDetail = data.detail.map((d: any) => d.msg).join(", ");
        } else {
          errorDetail = JSON.stringify(data.detail);
        }
      }
    } catch {
      errorDetail = await response.text();
    }

    throw new APIError(errorDetail, response.status, rawDetail);
  }

  // Handle file downloads (blob streams)
  const contentType = response.headers.get("Content-Type");
  if (contentType && (contentType.includes("application/pdf") || contentType.includes("application/vnd.openxmlformats-officedocument") || contentType.includes("text/csv"))) {
    return (await response.blob()) as unknown as T;
  }

  // Handle empty responses
  if (response.status === 204) {
    return {} as T;
  }

  try {
    return await response.json();
  } catch {
    return {} as T;
  }
}
