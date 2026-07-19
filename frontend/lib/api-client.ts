import axios, { AxiosError, type AxiosRequestConfig } from "axios";

import { clearToken, getToken } from "@/lib/auth";
import type { APIResponse } from "@/lib/types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const client = axios.create({ baseURL: API_BASE_URL });

client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      clearToken();
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

function unwrapApiResponse<T>(payload: APIResponse<T>): T {
  if (!payload || typeof payload !== "object" || !("success" in payload) || !("data" in payload)) {
    throw new Error("Unexpected API response format");
  }
  if (payload.success === false) {
    throw new Error(payload.message || "Request failed");
  }
  return payload.data as T;
}

function messageFromErrorPayload(
  data: { message?: unknown; detail?: unknown; data?: unknown } | undefined
): string | null {
  if (data?.data && typeof data.data === "object" && "errors" in data.data) {
    const errors = (data.data as { errors?: unknown }).errors;
    if (Array.isArray(errors) && errors.length > 0) {
      const firstError = errors[0] as { msg?: unknown } | undefined;
      if (typeof firstError?.msg === "string") return firstError.msg;
    }
  }
  if (typeof data?.message === "string") return data.message;
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) return "Validation error";
  if (data?.detail && typeof data.detail === "object" && "message" in data.detail) {
    return String((data.detail as { message: string }).message);
  }
  return null;
}

export function apiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: unknown; detail?: unknown; data?: unknown } | undefined;
    return messageFromErrorPayload(data) ?? error.message;
  }
  if (error instanceof Error && error.message) return error.message;
  return "Something went wrong. Please try again.";
}

export function isRequestCanceled(error: unknown): boolean {
  return axios.isCancel(error) || (axios.isAxiosError(error) && error.code === "ERR_CANCELED");
}

export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const res = await client.get<APIResponse<T>>(url, config);
  return unwrapApiResponse(res.data);
}

export async function apiPost<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const res = await client.post<APIResponse<T>>(url, body, config);
  return unwrapApiResponse(res.data);
}

export async function apiPut<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const res = await client.put<APIResponse<T>>(url, body, config);
  return unwrapApiResponse(res.data);
}

export async function apiPatch<T>(url: string, body?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const res = await client.patch<APIResponse<T>>(url, body, config);
  return unwrapApiResponse(res.data);
}

export async function apiDelete(url: string, config?: AxiosRequestConfig): Promise<void> {
  const res = await client.delete<APIResponse<null>>(url, config);
  unwrapApiResponse(res.data);
}

export async function apiDownload(url: string, config?: AxiosRequestConfig): Promise<Blob> {
  try {
    const res = await client.get(url, { ...config, responseType: "blob" });
    return res.data as Blob;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
      const text = await error.response.data.text();
      try {
        const payload = JSON.parse(text) as { message?: unknown; detail?: unknown; data?: unknown };
        const message = messageFromErrorPayload(payload);
        if (message) throw new Error(message);
      } catch (parseError) {
        if (parseError instanceof Error && parseError.name !== "SyntaxError") {
          throw parseError;
        }
      }
      if (text) throw new Error(text);
    }
    throw error;
  }
}

export default client;
