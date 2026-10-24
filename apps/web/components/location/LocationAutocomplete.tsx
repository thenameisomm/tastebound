"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { useDebouncedSearch } from "./useDebouncedSearch";
import type { LocationResult } from "@repo/contracts/location";
import { api } from "@/lib/api";

interface LocationAutocompleteProps {
  value?: LocationResult | null;
  onChange: (location: LocationResult | null) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  label?: string;
  error?: string;
  searchType?: "place" | "destination" | "locality" | "city";
  limit?: number;
}

function formatLocation(location: LocationResult): string {
  const parts = [location.name];
  if (location.region && location.region !== location.countryName) {
    parts.push(location.region);
  }
  parts.push(location.countryName);
  return parts.join(", ");
}

export function LocationAutocomplete({
  value,
  onChange,
  placeholder = "Search for a city, landmark, or destination…",
  disabled = false,
  required = false,
  label = "Destination",
  error,
  searchType = "place",
  limit = 10,
}: LocationAutocompleteProps) {
  const id = useId();
  const listboxId = useId();
  const [open, setOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [query, setQuery] = useState(() => (value ? formatLocation(value) : ""));
  const lastValueRef = useRef<LocationResult | null>(value ?? null);
  const listboxRef = useRef<HTMLUListElement>(null);

  const searchFn = useMemo(
    () => async (query: string): Promise<LocationResult[]> => {
      const payload = await api.get<{ entities: LocationResult[] }>(
        `/v1/qloo/search?q=${encodeURIComponent(query)}&type=${searchType}&limit=${limit}`
      );
      return payload.entities || [];
    },
    [searchType, limit]
  );

  const { results, loading, error: searchError, search, clear } = useDebouncedSearch<
    LocationResult
  >({
    searchFn,
    debounceMs: 250,
    minQueryLength: 2,
    enabled: !disabled,
  });

  useEffect(() => {
    if (value) {
      setQuery(formatLocation(value));
      lastValueRef.current = value;
    } else if (lastValueRef.current) {
      setQuery("");
      lastValueRef.current = null;
    }
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setQuery(newValue);
    if (value) {
      lastValueRef.current = null;
      onChange(null);
    }
    search(newValue);
    setOpen(true);
    setHighlightedIndex(-1);
  };

  const handleSelect = (location: LocationResult) => {
    setQuery(formatLocation(location));
    lastValueRef.current = location;
    onChange(location);
    setOpen(false);
    setHighlightedIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || results.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlightedIndex((prev) => Math.min(prev + 1, results.length - 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlightedIndex((prev) => Math.max(prev - 1, -1));
        break;
      case "Enter":
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < results.length) {
          const selected = results[highlightedIndex];
          if (selected) {
            handleSelect(selected);
          }
        }
        break;
      case "Escape":
        setOpen(false);
        setHighlightedIndex(-1);
        break;
      case "Tab":
        if (highlightedIndex >= 0 && highlightedIndex < results.length) {
          const selected = results[highlightedIndex];
          if (selected) {
            handleSelect(selected);
          }
        }
        setOpen(false);
        break;
    }
  };

  const handleBlur = () => {
    setTimeout(() => {
      setOpen(false);
      setHighlightedIndex(-1);
    }, 200);
  };

  const handleClear = () => {
    setQuery("");
    lastValueRef.current = null;
    onChange(null);
    clear();
    setOpen(false);
    setHighlightedIndex(-1);
  };

  useEffect(() => {
    if (highlightedIndex >= 0 && listboxRef.current) {
      const option = listboxRef.current.children[highlightedIndex] as HTMLElement;
      option?.scrollIntoView({ block: "nearest" });
    }
  }, [highlightedIndex]);

  return (
    <div className="field">
      <label htmlFor={id} className="label">
        {label}
        {required && <span aria-hidden="true">*</span>}
      </label>
      <div className="autocomplete">
        <input
          id={id}
          type="text"
          className="input"
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results.length > 0) {
              setOpen(true);
            }
          }}
          onBlur={handleBlur}
          disabled={disabled}
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-expanded={open}
          aria-activedescendant={
            highlightedIndex >= 0 ? `${id}-option-${highlightedIndex}` : undefined
          }
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          aria-busy={loading}
        />
        {loading && <span className="autocompleteSpinner" aria-hidden="true" />}
        {value && !loading && (
          <button
            type="button"
            className="autocompleteClear"
            onClick={handleClear}
            aria-label="Clear selection"
          >
            ×
          </button>
        )}
      </div>

      {open && results.length > 0 && (
        <ul
          ref={listboxRef}
          id={listboxId}
          role="listbox"
          className="autocompleteMenu"
          aria-label="Location suggestions"
        >
          {results.map((location, index) => (
            <li
              key={location.id}
              id={`${id}-option-${index}`}
              role="option"
              aria-selected={index === highlightedIndex}
              className={`autocompleteOption ${index === highlightedIndex ? "autocompleteOptionActive" : ""}`}
              onClick={() => handleSelect(location)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              <span className="autocompleteOptionName">{location.name}</span>
              <span className="autocompleteOptionMeta">
                {location.region && location.region !== location.countryName
                  ? `${location.region}, ${location.countryName}`
                  : location.countryName}
              </span>
            </li>
          ))}
        </ul>
      )}

      {open && results.length === 0 && !loading && (
        <div className="autocompleteMenu autocompleteEmpty">
          No locations found for &ldquo;{query}&rdquo;
        </div>
      )}

      {(searchError || error) && (
        <p id={`${id}-error`} className="autocompleteError" role="alert">
          {searchError?.message || error}
        </p>
      )}
    </div>
  );
}
