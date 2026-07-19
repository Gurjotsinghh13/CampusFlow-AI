const TOKEN_KEY = "campusflow_token";

interface TokenPayload {
  sub?: unknown;
  exp?: unknown;
}

function base64UrlToBase64(value: string): string {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  return base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
}

function decodeTokenPayload(token: string | null): TokenPayload | null {
  if (!token) return null;
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;
    return JSON.parse(atob(base64UrlToBase64(payload))) as TokenPayload;
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

export function getTokenSubject(): string | null {
  return isAuthenticated() ? (decodeTokenPayload(getToken())?.sub as string) : null;
}

export function isAuthenticated(): boolean {
  const token = getToken();
  const payload = decodeTokenPayload(token);
  if (!token) return false;
  if (!payload || typeof payload.sub !== "string") {
    clearToken();
    return false;
  }

  if (typeof payload.exp !== "number" || payload.exp * 1000 <= Date.now()) {
    clearToken();
    return false;
  }

  return true;
}
