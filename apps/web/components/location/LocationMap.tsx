"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import type { LeafletMouseEvent, Map as LeafletMap, Marker } from "leaflet";
import type { LocationResult, SelectedLocation } from "@repo/contracts/location";
import { api } from "@/lib/api";

interface LocationMapProps {
  value?: SelectedLocation | null;
  onChange: (location: SelectedLocation | null) => void;
  height?: number;
  zoom?: number;
  showMarker?: boolean;
  disabled?: boolean;
}

const DEFAULT_CENTER: [number, number] = [39.8283, -98.5795];
const DEFAULT_ZOOM = 4;
const FOCUS_ZOOM = 10;

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function hasCoordinates(
  location: Pick<SelectedLocation, "lat" | "lon"> | null | undefined,
): location is Pick<SelectedLocation, "lat" | "lon"> {
  return !!location && Number.isFinite(location.lat) && Number.isFinite(location.lon);
}

function popupContent(location: SelectedLocation): string {
  const country = location.countryName ? `<br>${escapeHtml(location.countryName)}` : "";
  return `<strong>${escapeHtml(location.name)}</strong>${country}`;
}

export function LocationMap({
  value,
  onChange,
  height = 300,
  zoom = DEFAULT_ZOOM,
  showMarker = true,
  disabled = false,
}: LocationMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<LeafletMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const leafletRef = useRef<typeof import("leaflet") | null>(null);
  const valueRef = useRef(value);
  const disabledRef = useRef(disabled);
  const onChangeRef = useRef(onChange);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  useEffect(() => {
    disabledRef.current = disabled;
  }, [disabled]);

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    let cancelled = false;

    const initMap = async () => {
      try {
        const L = await import("leaflet");
        if (cancelled || !mapRef.current || mapInstanceRef.current) return;
        leafletRef.current = L;

        delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
          iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
          shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        });

        const current = valueRef.current;
        const initialCenter: [number, number] = hasCoordinates(current)
          ? [current.lat, current.lon]
          : DEFAULT_CENTER;
        const map = L.map(mapRef.current, {
          center: initialCenter,
          zoom: hasCoordinates(current) ? FOCUS_ZOOM : zoom,
          zoomControl: false,
          attributionControl: true,
        });

        L.control.zoom({ position: "bottomright" }).addTo(map);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }).addTo(map);

        map.on("click", async (event: LeafletMouseEvent) => {
          if (disabledRef.current) return;
          const { lat, lng } = event.latlng;
          let selected: SelectedLocation = {
            id: `manual-${lat}-${lng}`,
            name: `Selected location (${lat.toFixed(4)}, ${lng.toFixed(4)})`,
            countryCode: "US",
            countryName: "United States",
            region: "",
            lat,
            lon: lng,
            type: "place",
          };

          try {
            const payload = await api.get<{ entities: LocationResult[] }>(
              `/v1/qloo/search?q=${lat},${lng}&type=place&limit=1`,
            );
            const location = payload.entities?.[0];
            if (location) {
              selected = {
                id: location.id,
                name: location.name,
                countryCode: location.countryCode || "US",
                countryName: location.countryName || "United States",
                region: location.region || "",
                lat,
                lon: lng,
                type: location.type || "place",
              };
            }
          } catch {
            // Keep the manual coordinate selection when reverse geocoding fails.
          }

          onChangeRef.current(selected);
        });

        mapInstanceRef.current = map;
        setMapLoaded(true);
      } catch {
        if (!cancelled) setMapError("The map could not load.");
      }
    };

    void initMap();

    return () => {
      cancelled = true;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        markerRef.current = null;
        leafletRef.current = null;
        setMapLoaded(false);
      }
    };
  }, [zoom]);

  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !mapLoaded) return;
    const handlers = [
      map.dragging,
      map.touchZoom,
      map.scrollWheelZoom,
      map.doubleClickZoom,
      map.boxZoom,
      map.keyboard,
    ];
    for (const handler of handlers) {
      if (disabled) handler.disable();
      else handler.enable();
    }
    if (markerRef.current?.dragging) {
      if (disabled) markerRef.current.dragging.disable();
      else markerRef.current.dragging.enable();
    }
  }, [disabled, mapLoaded]);

  useEffect(() => {
    const L = leafletRef.current;
    const map = mapInstanceRef.current;
    if (!L || !map || !mapLoaded) return;

    if (!value || !showMarker || !hasCoordinates(value)) {
      if (markerRef.current) {
        markerRef.current.remove();
        markerRef.current = null;
      }
      return;
    }

    if (!markerRef.current) {
      const marker = L.marker([value.lat, value.lon], {
        draggable: !disabledRef.current,
        title: value.name,
      }).addTo(map);
      marker.on("dragend", () => {
        const { lat, lng } = marker.getLatLng();
        const current = valueRef.current;
        if (current) onChangeRef.current({ ...current, lat, lon: lng });
      });
      markerRef.current = marker;
    } else {
      markerRef.current.setLatLng([value.lat, value.lon]);
    }

    markerRef.current.bindPopup(popupContent(value)).openPopup();
    map.setView([value.lat, value.lon], Math.max(map.getZoom(), FOCUS_ZOOM));
  }, [mapLoaded, showMarker, value]);

  return (
    <div className="mapFrame" style={{ height: `${height}px` }}>
      <div
        ref={mapRef}
        className="mapCanvas"
        role="application"
        aria-label="Interactive map for location selection"
      />
      {!mapLoaded && !mapError ? (
        <div className="mapLoading mapOverlay" role="status" aria-label="Loading map">
          <span className="mapSpinner" aria-hidden="true" />
          <span>Loading map…</span>
        </div>
      ) : null}
      {mapError ? (
        <div className="mapLoading mapError mapOverlay" role="alert">
          <p>{mapError}</p>
        </div>
      ) : null}
    </div>
  );
}
