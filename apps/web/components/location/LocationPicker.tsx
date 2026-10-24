"use client";

import { useState } from "react";
import { LocationAutocomplete } from "./LocationAutocomplete";
import { LocationMap } from "./LocationMap";
import type { LocationResult, SelectedLocation } from "@repo/contracts/location";

interface LocationPickerProps {
  value?: SelectedLocation | null;
  onChange: (location: SelectedLocation | null) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  label?: string;
  error?: string;
  showMap?: boolean;
  mapHeight?: number;
  searchType?: "place" | "destination" | "locality" | "city";
  limit?: number;
}

export function LocationPicker({
  value,
  onChange,
  placeholder = "Search for a city, landmark, or destination…",
  disabled = false,
  required = false,
  label = "Destination",
  error,
  showMap = true,
  mapHeight = 300,
  searchType = "place",
  limit = 10,
}: LocationPickerProps) {
  const [localValue, setLocalValue] = useState<SelectedLocation | null>(value ?? null);

  const handleChange = (location: SelectedLocation | null) => {
    setLocalValue(location);
    onChange(location);
  };

  // Convert SelectedLocation to LocationResult for the autocomplete
  const autocompleteValue = localValue ? {
    id: localValue.id,
    name: localValue.name,
    countryCode: localValue.countryCode,
    countryName: localValue.countryName,
    region: localValue.region,
    lat: localValue.lat,
    lon: localValue.lon,
    type: localValue.type as "place" | "destination" | "locality" | "city",
  } : null;

  const handleAutocompleteChange = (location: LocationResult | null) => {
    if (!location || !Number.isFinite(location.lat) || !Number.isFinite(location.lon)) {
      setLocalValue(null);
      onChange(null);
      return;
    }
    const newValue: SelectedLocation = {
      id: location.id,
      name: location.name,
      countryCode: location.countryCode,
      countryName: location.countryName,
      region: location.region,
      lat: location.lat,
      lon: location.lon,
      type: location.type,
    };
    setLocalValue(newValue);
    onChange(newValue);
  };

  return (
    <div className="stack" style={{ gap: 16 }}>
      <LocationAutocomplete
        value={autocompleteValue}
        onChange={handleAutocompleteChange}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        label={label}
        error={error}
        searchType={searchType}
        limit={limit}
      />
      {showMap && (
        <div className="stackSm">
          <span className="kindTag">Map</span>
          <LocationMap
            value={localValue}
            onChange={handleChange}
            height={mapHeight}
            showMarker={true}
            disabled={disabled}
          />
        </div>
      )}
    </div>
  );
}
