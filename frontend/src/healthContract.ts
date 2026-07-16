/**
 * SSID-EMS Health Contract Types and Validators
 * No API calls. No forbidden port URLs.
 */

export interface HealthResponse {
  service: string;
  status: "ok";
  started: boolean;
  mode: string;
}

export interface ReadinessResponse {
  service: string;
  status: "not_ready";
  reason: string;
  started: boolean;
  mode: string;
}

export interface VersionResponse {
  service: string;
  version: string;
  mode: string;
}

export function validateHealthResponse(obj: unknown): obj is HealthResponse {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    o.service === "SSID-EMS" &&
    o.status === "ok" &&
    o.started === false &&
    o.mode === "local_scaffold"
  );
}

export function validateReadinessResponse(obj: unknown): obj is ReadinessResponse {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    o.service === "SSID-EMS" &&
    o.status === "not_ready" &&
    o.reason === "local_scaffold_no_service_start" &&
    o.started === false &&
    o.mode === "local_scaffold"
  );
}

export function validateVersionResponse(obj: unknown): obj is VersionResponse {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    o.service === "SSID-EMS" &&
    typeof o.version === "string" &&
    o.mode === "local_scaffold"
  );
}
