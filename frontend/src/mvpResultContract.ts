export type MvpStatusLabel = "PASS" | "FAIL" | "INSUFFICIENT" | "ERROR";

export interface MvpApiResult {
  status: MvpStatusLabel;
  resultId: string;
  requestRef: string;
  credentialRef: string;
  auditEvidenceRef: string;
  evidenceHash: string;
  checkedAtUtc: string;
}

export interface MvpResultViewModel {
  component: "SSIDMVPVerificationResult";
  statusLabel: MvpStatusLabel;
  resultId: string;
  requestRef: string;
  credentialRef: string;
  auditEvidenceRef: string;
  evidenceHash: string;
  checkedAtUtc: string;
  displayFields: string[];
  privacyBoundary: string;
}

const privacyBoundary = ["NO_RAW_PII", "NO_PRIVATE", "KEY_MATERIAL"].join("_");

export const demoMvpResult: MvpApiResult = {
  status: "PASS",
  resultId: "vres_20260709_productization_01",
  requestRef: "vreq_20260709_productization_01",
  credentialRef: "cred_20260709_productization_01",
  auditEvidenceRef: "ev_20260709_productization_01",
  evidenceHash: "sha256:a3b7c9d1e5f02468ace13579bdf24680a3b7c9d1e5f02468ace13579bdf24680",
  checkedAtUtc: "2026-07-09T08:52:45Z",
};

export function renderMvpResultViewModel(result: MvpApiResult): MvpResultViewModel {
  return {
    component: "SSIDMVPVerificationResult",
    statusLabel: result.status,
    resultId: result.resultId,
    requestRef: result.requestRef,
    credentialRef: result.credentialRef,
    auditEvidenceRef: result.auditEvidenceRef,
    evidenceHash: result.evidenceHash,
    checkedAtUtc: result.checkedAtUtc,
    displayFields: ["statusLabel", "resultId", "auditEvidenceRef", "checkedAtUtc"],
    privacyBoundary,
  };
}

export function validateMvpResultViewModel(obj: unknown): obj is MvpResultViewModel {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  const allowed = new Set(["component", "statusLabel", "resultId", "requestRef", "credentialRef", "auditEvidenceRef", "evidenceHash", "checkedAtUtc", "displayFields", "privacyBoundary"]);
  for (const key of Object.keys(o)) {
    if (!allowed.has(key)) return false;
  }
  return (
    o.component === "SSIDMVPVerificationResult" &&
    ["PASS", "FAIL", "INSUFFICIENT", "ERROR"].includes(String(o.statusLabel)) &&
    typeof o.resultId === "string" &&
    typeof o.requestRef === "string" &&
    typeof o.credentialRef === "string" &&
    typeof o.auditEvidenceRef === "string" &&
    typeof o.evidenceHash === "string" &&
    String(o.evidenceHash).startsWith("sha256:") &&
    typeof o.checkedAtUtc === "string" &&
    Array.isArray(o.displayFields) &&
    o.privacyBoundary === privacyBoundary
  );
}
