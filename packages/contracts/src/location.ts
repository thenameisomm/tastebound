/**
 * Shared location types for destination and market selection.
 * Generated from backend API contracts.
 */

export interface LocationResult {
  id: string;
  name: string;
  countryCode: string;
  countryName: string;
  region: string;
  lat: number;
  lon: number;
  type: 'place' | 'destination' | 'locality' | 'city';
  population?: number;
  timezone?: string;
}

export interface LocationSearchRequest {
  q: string;
  type?: 'place' | 'destination' | 'locality' | 'city';
  limit?: number;
}

export interface LocationSearchResponse {
  entities: LocationResult[];
  call_id?: string;
}

export interface SelectedLocation {
  id: string;
  name: string;
  countryCode: string;
  countryName: string;
  region: string;
  lat: number;
  lon: number;
  type: string;
}

export interface MarketLocation extends LocationResult {
  marketId: string;
  radiusKm: number;
  populationBand: number;
  presets: string[];
}
