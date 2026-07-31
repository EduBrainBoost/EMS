/**
 * SSID-EMS Frontend Health Contract Tests
 * Run with: npx jest frontend/tests/healthContract.test.ts
 * If Jest/Node is unavailable, see docs/EMS_LOCAL_BUILD_RUNBOOK.md
 */

import {
  validateHealthResponse,
  validateReadinessResponse,
  validateVersionResponse,
} from "../src/healthContract";

describe("HealthResponse validator", () => {
  it("accepts a valid health response", () => {
    expect(
      validateHealthResponse({
        service: "SSID-EMS",
        status: "ok",
        started: false,
        mode: "local_scaffold",
      })
    ).toBe(true);
  });

  it("rejects an invalid health response", () => {
    expect(
      validateHealthResponse({
        service: "SSID-EMS",
        status: "error",
        started: false,
        mode: "local_scaffold",
      })
    ).toBe(false);
  });
});

describe("ReadinessResponse validator", () => {
  it("accepts a valid readiness response", () => {
    expect(
      validateReadinessResponse({
        service: "SSID-EMS",
        status: "not_ready",
        reason: "local_scaffold_no_service_start",
        started: false,
        mode: "local_scaffold",
      })
    ).toBe(true);
  });
});

describe("VersionResponse validator", () => {
  it("accepts a valid version response", () => {
    expect(
      validateVersionResponse({
        service: "SSID-EMS",
        version: "0.1.0-scaffold",
        mode: "local_scaffold",
      })
    ).toBe(true);
  });
});
