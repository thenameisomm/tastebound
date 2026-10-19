"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UseDebouncedSearchOptions<T> {
  searchFn: (query: string) => Promise<T[]>;
  debounceMs?: number;
  minQueryLength?: number;
  enabled?: boolean;
}

interface UseDebouncedSearchResult<T> {
  results: T[];
  loading: boolean;
  error: Error | null;
  search: (query: string) => void;
  clear: () => void;
}

export function useDebouncedSearch<T>({
  searchFn,
  debounceMs = 300,
  minQueryLength = 2,
  enabled = true,
}: UseDebouncedSearchOptions<T>): UseDebouncedSearchResult<T> {
  const [results, setResults] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [query, setQuery] = useState("");

  const abortControllerRef = useRef<AbortController | null>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const executeSearch = useCallback(
    async (searchQuery: string) => {
      if (!enabled) return;
      if (searchQuery.length < minQueryLength) {
        setResults([]);
        return;
      }

      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      setLoading(true);
      setError(null);

      try {
        const data = await searchFn(searchQuery);
        if (mountedRef.current && !abortControllerRef.current?.signal.aborted) {
          setResults(data);
        }
      } catch (err) {
        if (mountedRef.current && !abortControllerRef.current?.signal.aborted) {
          if (err instanceof Error && err.name !== "AbortError") {
            setError(err);
            setResults([]);
          }
        }
      } finally {
        if (mountedRef.current && !abortControllerRef.current?.signal.aborted) {
          setLoading(false);
        }
      }
    },
    [searchFn, minQueryLength, enabled]
  );

  const search = useCallback(
    (searchQuery: string) => {
      setQuery(searchQuery);
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      debounceTimerRef.current = setTimeout(() => {
        executeSearch(searchQuery);
      }, debounceMs);
    },
    [executeSearch, debounceMs]
  );

  const clear = useCallback(() => {
    setQuery("");
    setResults([]);
    setError(null);
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return { results, loading, error, search, clear };
}
