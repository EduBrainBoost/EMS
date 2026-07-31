import {
  demoMvpResult,
  renderMvpResultViewModel,
  validateMvpResultViewModel,
} from "../src/mvpResultContract";

describe("EMS MVP result contract", () => {
  it("renders a PASS result with audit evidence", () => {
    const model = renderMvpResultViewModel(demoMvpResult);
    expect(model.statusLabel).toBe("PASS");
    expect(model.auditEvidenceRef).toBe("ev_20260709_productization_01");
    expect(validateMvpResultViewModel(model)).toBe(true);
  });

  it("rejects PII-like fields and invalid statuses", () => {
    expect(validateMvpResultViewModel({ ...renderMvpResultViewModel(demoMvpResult), statusLabel: "MAYBE" })).toBe(false);
    expect(validateMvpResultViewModel({ ...renderMvpResultViewModel(demoMvpResult), email: "blocked.invalid" })).toBe(false);
  });
});
