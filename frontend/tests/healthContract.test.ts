/**
 * EMS Frontend Health Contract Tests
 * Run with: npx jest frontend/tests/healthContract.test.ts
 * If Jest/Node is unavailable, see docs/EMS_LOCAL_REBUILD_RUNBOOK.md
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
        service: "EMS",
        status: "not_started",
        started: false,
        mode: "local_rebuild",
      })
    ).toBe(true);
  });

  it("rejects an invalid health response", () => {
    expect(
      validateHealthResponse({
        service: "EMS",
        status: "ok",
        started: false,
        mode: "local_rebuild",
      })
    ).toBe(false);
  });
});

describe("ReadinessResponse validator", () => {
  it("accepts a valid readiness response", () => {
    expect(
      validateReadinessResponse({
        service: "EMS",
        status: "not_ready",
        reason: "local_rebuild_no_service_start",
        started: false,
        mode: "local_rebuild",
      })
    ).toBe(true);
  });
});

describe("VersionResponse validator", () => {
  it("accepts a valid version response", () => {
    expect(
      validateVersionResponse({
        service: "EMS",
        version: "0.1.0-rebuild",
        mode: "local_rebuild",
      })
    ).toBe(true);
  });
});
