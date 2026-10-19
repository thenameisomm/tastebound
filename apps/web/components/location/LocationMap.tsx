"use client";

import { useEffect, useRef, useState } from "react";
import type { SelectedLocation } from "@repo/contracts/location";

interface LocationMapProps {
  value?: SelectedLocation | null;
  onChange: (location: SelectedLocation | null) => void;
  height?: number;
  zoom?: number;
  showMarker?: boolean;
  disabled?: boolean;
}

const DEFAULT_CENTER: [number, number] = [39.8283, -98.5795]; // USA center
const DEFAULT_ZOOM = 4;

export function LocationMap({
  value,
  onChange,
  height = 300,
  zoom = DEFAULT_ZOOM,
  showMarker = true,
  disabled = false,
}: LocationMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markerRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    if (disabled) return;

    const initMap = async () => {
      try {
        // Dynamic import to avoid SSR issues
        const L = await import("leaflet");

        // Fix for Leaflet marker icon issues
        delete (L.Icon.Default.prototype as any)._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
          iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
          shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
        });

        const map = L.map(mapRef.current!, {
          center: value ? [value.lat, value.lon] : DEFAULT_CENTER,
          zoom: value ? 10 : zoom,
          zoomControl: true,
          attributionControl: true,
          dragging: !disabled,
          touchZoom: !disabled,
          scrollWheelZoom: !disabled,
          doubleClickZoom: !disabled,
          boxZoom: !disabled,
          keyboard: !disabled,
        });

        // Add OpenStreetMap tiles
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution:
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
        }).addTo(map);

        mapInstanceRef.current = map;

        // Add marker for current value
        if (value && showMarker) {
          const marker = L.marker([value.lat, value.lon], {
            draggable: !disabled,
            title: value.name,
          }).addTo(map);

          marker.bindPopup(`<strong>${value.name}</strong><br>${value.countryName}`).openPopup();

          marker.on("dragend", (e: any) => {
            const { lat, lng } = e.target.getLatLng();
            onChange({
              ...value,
              lat,
              lon: lng,
            });
          });

          markerRef.current = marker;
        }

        // Handle map click to select location
        if (!disabled) {
          map.on("click", async (e: any) => {
            const { lat, lng } = e.latlng;

            // Reverse geocode using our API
            try {
              const response = await fetch(
                `/v1/qloo/search?q=${lat},${lng}&type=place&limit=1`
              );
              if (response.ok) {
                const data = await response.json();
                if (data.entities && data.entities.length > 0) {
                  const location = data.entities[0];
                  onChange({
                    id: location.id,
                    name: location.name,
                    countryCode: location.countryCode || "US",
                    countryName: location.countryName || "United States",
                    region: location.region || "",
                    lat,
                    lon: lng,
                    type: location.type || "place",
                  });

                  // Update marker
                  if (markerRef.current) {
                    markerRef.current.setLatLng([lat, lng]);
                    markerRef.current
                      .setPopupContent(
                        `<strong>${location.name}</strong><br>${location.countryName}`
                      )
                      .openPopup();
                  } else {
                    const newMarker = L.marker([lat, lng], { draggable: true }).addTo(map);
                    newMarker.bindPopup(
                      `<strong>${location.name}</strong><br>${location.countryName}`
                    ).openPopup();
                    markerRef.current = newMarker;
                  }
                }
              }
            } catch (err) {
              console.error("Reverse geocoding failed:", err);
              // Still allow selection with coordinates
              onChange({
                id: `manual-${lat}-${lng}`,
                name: `Selected location (${lat.toFixed(4)}, ${lng.toFixed(4)})`,
                countryCode: "US",
                countryName: "United States",
                region: "",
                lat,
                lon: lng,
                type: "place",
              });

              if (markerRef.current) {
                markerRef.current.setLatLng([lat, lng]);
                markerRef.current
                  .setPopupContent(
                    `<strong>Selected location</strong><br>${lat.toFixed(4)}, ${lng.toFixed(4)}`
                  )
                  .openPopup();
              } else {
                const newMarker = L.marker([lat, lng], { draggable: true }).addTo(map);
                newMarker
                  .bindPopup(
                    `<strong>Selected location</strong><br>${lat.toFixed(4)}, ${lng.toFixed(4)}`
                  )
                  .openPopup();
                markerRef.current = newMarker;
              }
            }
          });
        }

        // Handle marker drag
        map.on("dragend", () => {
          if (markerRef.current && value) {
            const { lat, lng } = markerRef.current.getLatLng();
            onChange({
              ...value,
              lat,
              lon: lng,
            });
          }
        });

        setMapLoaded(true);
      } catch (err) {
        console.error("Failed to initialize map:", err);
        setMapError("Failed to load map");
      }
    };

    if (mapRef.current && !mapInstanceRef.current) {
      initMap();
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        markerRef.current = null;
        setMapLoaded(false);
      }
    };
  }, [value, onChange, disabled, showMarker, zoom]);

  // Update marker when value changes externally
  useEffect(() => {
    if (mapInstanceRef.current && markerRef.current && value) {
      markerRef.current.setLatLng([value.lat, value.lon]);
      mapInstanceRef.current.setView([value.lat, value.lon], 10);
      markerRef.current
        .setPopupContent(`<strong>${value.name}</strong><br>${value.countryName}`)
        .openPopup();
    }
  }, [value]);

  if (!mapLoaded && !mapError) {
    return (
      <div
        className="w-full h-[300px] bg-gray-100 rounded-lg flex items-center justify-center"
        role="status"
        aria-label="Loading map"
      >
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div
        className="w-full h-[300px] bg-gray-100 rounded-lg flex items-center justify-center p-4"
        role="alert"
      >
        <p className="text-center text-gray-600">{mapError}</p>
      </div>
    );
  }

  return (
    <div
      ref={mapRef}
      className="w-full rounded-lg overflow-hidden"
      style={{ height: `${height}px` }}
      role="application"
      aria-label="Interactive map for location selection"
    />
  );
}
