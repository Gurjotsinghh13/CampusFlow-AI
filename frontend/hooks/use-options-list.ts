"use client";

import * as React from "react";
import { toast } from "sonner";

import { apiErrorMessage, apiGet, isRequestCanceled } from "@/lib/api-client";
import type { PaginatedResponse } from "@/lib/types";

export function useOptionsList<T>(endpoint: string, params?: Record<string, string | undefined>) {
  const [items, setItems] = React.useState<T[]>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const paramsKey = JSON.stringify(params ?? {});

  React.useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    setIsLoading(true);

    async function loadOptions() {
      const baseQuery: Record<string, string | number> = { page_size: 100 };
      if (params) {
        for (const [key, value] of Object.entries(params)) {
          if (value) baseQuery[key] = value;
        }
      }

      const firstPage = await apiGet<PaginatedResponse<T>>(endpoint, {
        params: { ...baseQuery, page: 1 },
        signal: controller.signal,
      });
      const allItems = [...firstPage.items];

      for (let page = 2; page <= firstPage.total_pages; page += 1) {
        if (cancelled) break;
        const nextPage = await apiGet<PaginatedResponse<T>>(endpoint, {
          params: { ...baseQuery, page },
          signal: controller.signal,
        });
        allItems.push(...nextPage.items);
      }

      return allItems;
    }

    loadOptions()
      .then((nextItems) => {
        if (!cancelled) setItems(nextItems);
      })
      .catch((error) => {
        if (!cancelled && !isRequestCanceled(error)) {
          setItems([]);
          toast.error(apiErrorMessage(error));
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpoint, paramsKey]);

  return { items, isLoading };
}
