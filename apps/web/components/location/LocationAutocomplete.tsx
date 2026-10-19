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
  const inputRef = useRef<HTMLInputElement>(null);
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

  const displayValue = useMemo(() => {
    if (!value) return "";
    return formatLocation(value);
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (!value || value.name !== newValue) {
      onChange(null);
    }
    search(newValue);
    setOpen(true);
    setHighlightedIndex(-1);
  };

  const handleSelect = (location: LocationResult) => {
    onChange(location);
    setOpen(false);
    setHighlightedIndex(-1);
    if (inputRef.current) {
      inputRef.current.value = formatLocation(location);
    }
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
    onChange(null);
    clear();
    setOpen(false);
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
      <div className="relative">
        <input
          ref={inputRef}
          id={id}
          type="text"
          className="input"
          placeholder={placeholder}
          value={displayValue}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (displayValue === "" && results.length > 0) {
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
        />
        {loading && (
          <span className="absolute right-3 top-1/2 -translate-y-1/2" aria-hidden="true">
            <svg
              className="animate-spin h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <circle
                cx={12}
                cy={12}
                r={10}
                strokeOpacity={0.25}
                strokeWidth={3}
              />
              <path
                d="M12 2a10 10 0 0 1 10 10"
                strokeLinecap="round"
                strokeWidth={3}
              />
            </svg>
          </span>
        )}
        {value && !loading && (
          <button
            type="button"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-500 hover:text-gray-700"
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
          className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-auto"
          aria-label="Location suggestions"
        >
          {results.map((location, index) => (
            <li
              key={location.id}
              id={`${id}-option-${index}`}
              role="option"
              aria-selected={index === highlightedIndex}
              className={`px-4 py-3 cursor-pointer transition-colors ${
                index === highlightedIndex ? "bg-blue-50" : "hover:bg-gray-50"
              }`}
              onClick={() => handleSelect(location)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              <div className="font-medium">{location.name}</div>
              <div className="text-sm text-gray-500">
                {location.region && location.region !== location.countryName
                  ? `${location.region}, ${location.countryName}`
                  : location.countryName}
              </div>
            </li>
          ))}
        </ul>
      )}

      {open && results.length === 0 && !loading && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-4 text-center text-gray-500">
          No locations found for "{displayValue}"
        </div>
      )}

      {(searchError || error) && (
        <p id={`${id}-error`} className="text-sm text-red-600" role="alert">
          {searchError?.message || error}
        </p>
      )}
    </div>
  );
}
