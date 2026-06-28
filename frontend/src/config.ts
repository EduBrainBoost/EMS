/**
 * EMS Frontend Configuration — Local Rebuild Only
 * No secrets. No .env. No provider configs.
 */

export const EMS_FRONTEND_PORT: number = 3100;
export const EMS_BACKEND_PORT: number = 8100;
export const forbiddenPorts: number[] = [3000, 3001, 3002, 3210, 5173, 4321, 8000];
export const serviceStartAllowed: boolean = false;
export const ENV_MODE: string = "local_rebuild";
export const SERVICE_NAME: string = "EMS";
export const VERSION: string = "0.1.0-rebuild";
export const REMOTE_URL: string = "https://github.com/EduBrainBoost/EMS.git";

export function validatePorts(): { valid: boolean; violations: number[] } {
  const violations: number[] = [];
  for (const port of [EMS_FRONTEND_PORT, EMS_BACKEND_PORT]) {
    if (forbiddenPorts.includes(port)) {
      violations.push(port);
    }
  }
  return { valid: violations.length === 0, violations };
}
