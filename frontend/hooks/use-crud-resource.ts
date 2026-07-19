"use client";

import * as React from "react";

import { apiDelete, apiErrorMessage, apiGet, apiPost, apiPut, isRequestCanceled } from "@/lib/api-client";
import type { PaginatedResponse } from "@/lib/types";
import { toast } from "sonner";

interface UseCrudResourceOptions {
  pageSize?: number;
  extraParams?: Record<string, string | undefined>;
}

export function useCrudResource<T extends { id: string }>(endpoint: string, options: UseCrudResourceOptions = {}) {
  const { pageSize = 20, extraParams } = options;

  const [items, setItems] = React.useState<T[]>([]);
  const [total, setTotal] = React.useState(0);
  const [totalPages, setTotalPages] = React.useState(0);
  const [page, setPage] = React.useState(1);
  const [search, setSearch] = React.useState("");
  const [debouncedSearch, setDebouncedSearch] = React.useState("");
  const [isLoading, setIsLoading] = React.useState(true);
  const [refreshTick, setRefreshTick] = React.useState(0);

  React.useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(t);
  }, [search]);

  React.useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const extraParamsKey = JSON.stringify(extraParams ?? {});

  React.useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    setIsLoading(true);

    const params: Record<string, string | number> = { page, page_size: pageSize };
    if (debouncedSearch) params.search = debouncedSearch;
    if (extraParams) {
      for (const [key, value] of Object.entries(extraParams)) {
        if (value) params[key] = value;
      }
    }

    apiGet<PaginatedResponse<T>>(endpoint, { params, signal: controller.signal })
      .then((res) => {
        if (cancelled) return;
        if (res.total > 0 && res.total_pages > 0 && page > res.total_pages) {
          setPage(res.total_pages);
          return;
        }
        setItems(res.items);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      })
      .catch((error) => {
        if (!cancelled && !isRequestCanceled(error)) toast.error(apiErrorMessage(error));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint, page, pageSize, debouncedSearch, extraParamsKey, refreshTick]);

  const refetch = React.useCallback(() => setRefreshTick((t) => t + 1), []);

  const create = React.useCallback(
    async (payload: unknown) => {
      const created = await apiPost<T>(endpoint, payload);
      refetch();
      return created;
    },
    [endpoint, refetch]
  );

  const update = React.useCallback(
    async (id: string, payload: unknown) => {
      const updated = await apiPut<T>(`${endpoint}/${id}`, payload);
      refetch();
      return updated;
    },
    [endpoint, refetch]
  );

  const remove = React.useCallback(
    async (id: string) => {
      await apiDelete(`${endpoint}/${id}`);
      refetch();
    },
    [endpoint, refetch]
  );

  return {
    items,
    total,
    totalPages,
    page,
    setPage,
    search,
    setSearch,
    isLoading,
    refetch,
    create,
    update,
    remove,
  };
}
