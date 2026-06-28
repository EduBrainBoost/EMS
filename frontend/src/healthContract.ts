/**
 * EMS Health Contract Types and Validators
 * No API calls. No forbidden port URLs.
 */

export interface HealthResponse {
  service: string;
  status: "not_started";
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
    o.service === "EMS" &&
    o.status === "not_started" &&
    o.started === false &&
    o.mode === "local_rebuild"
  );
}

export function validateReadinessResponse(obj: unknown): obj is ReadinessResponse {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    o.service === "EMS" &&
    o.status === "not_ready" &&
    o.reason === "local_rebuild_no_service_start" &&
    o.started === false &&
    o.mode === "local_rebuild"
  );
}

export function validateVersionResponse(obj: unknown): obj is VersionResponse {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    o.service === "EMS" &&
    typeof o.version === "string" &&
    o.mode === "local_rebuild"
  );
}
