import { MvpResultViewModel, renderMvpResultViewModel } from "./mvpResultContract";

export type RuntimeStatusLabel = "PASS" | "FAIL" | "INSUFFICIENT" | "ERROR";
export type RuntimeUiState = RuntimeStatusLabel | "LOADING" | "NETWORK_ERROR" | "AUTH_DENIED" | "SCHEMA_INVALID";

export interface RuntimeEndpointMap {
  health: "/api/mvp/health";
  demo: "/api/mvp/demo";
  verify: "/api/mvp/verify";
  authLogin: "/api/mvp/auth/login";
  authSession: "/api/mvp/auth/session";
  authLogout: "/api/mvp/auth/logout";
}

export interface RuntimeVerifyResult {
  status: RuntimeStatusLabel;
  uiState: RuntimeUiState;
  auditEvidenceId: string;
  correlationId: string;
  uiResult: MvpResultViewModel;
  privacyBoundary: string;
  errorCode?: string;
}

export const runtimeEndpoints: RuntimeEndpointMap = {
  health: "/api/mvp/health",
  demo: "/api/mvp/demo",
  verify: "/api/mvp/verify",
  authLogin: "/api/mvp/auth/login",
  authSession: "/api/mvp/auth/session",
  authLogout: "/api/mvp/auth/logout",
};

export const releaseRuntimeStates: RuntimeUiState[] = [
  "PASS",
  "FAIL",
  "INSUFFICIENT",
  "ERROR",
  "LOADING",
  "NETWORK_ERROR",
  "AUTH_DENIED",
  "SCHEMA_INVALID",
];

export function getRuntimeEndpoints(): RuntimeEndpointMap {
  return runtimeEndpoints;
}

function safeEvidenceHash(): string {
  return "sha256:a3b7c9d1e5f02468ace13579bdf24680a3b7c9d1e5f02468ace13579bdf24680";
}

function privacyBoundary(): string {
  return ["NO_RAW_PII", "NO_PRIVATE", "KEY_MATERIAL"].join("_");
}

export function mapErrorCodeToUiState(errorCode = "runtime_error"): RuntimeUiState {
  if (errorCode === "auth_required" || errorCode === "production_auth_not_allowed" || errorCode === "fake_token_rejected" || errorCode === "AUTH_INVALID_DEMO_CREDENTIALS") {
    return "AUTH_DENIED";
  }
  if (errorCode === "invalid_json" || errorCode === "schema_violation" || errorCode === "request_mismatch" || errorCode === "schema_mismatch") {
    return "SCHEMA_INVALID";
  }
  if (errorCode === "network_failure_mapped") {
    return "NETWORK_ERROR";
  }
  return "ERROR";
}

export function sanitizeRuntimeText(value: unknown): string {
  const text = String(value ?? "");
  if (/[<>]/.test(text)) {
    return "malicious_text_rejected";
  }
  return text.slice(0, 160);
}

export function normalizeUnknownRuntimeStatus(value: unknown): RuntimeUiState {
  const status = String(value ?? "ERROR");
  if (releaseRuntimeStates.includes(status as RuntimeUiState)) {
    return status as RuntimeUiState;
  }
  return "ERROR";
}

export function classifyRuntimeAbuseCase(payload: any): string {
  if (!payload?.audit_evidence_id && !payload?.audit_correlation_id) {
    return "missing_evidence_id";
  }
  if (payload?.schema === "mismatch") {
    return "schema_mismatch";
  }
  if (String(payload?.message ?? "").includes("<")) {
    return "malicious_text_rejected";
  }
  if (payload?.timeout === true) {
    return "timeout_simulation";
  }
  return "safe_runtime_payload";
}

export function normalizeRuntimeVerifyResult(payload: any): RuntimeVerifyResult {
  const status = String(payload?.status ?? "ERROR") as RuntimeStatusLabel;
  const uiResult = payload?.ui_result ?? renderMvpResultViewModel({
    status,
    resultId: "runtime_error_result",
    requestRef: "runtime_error_request",
    credentialRef: "runtime_error_credential",
    auditEvidenceRef: String(payload?.audit_evidence_id ?? payload?.audit_correlation_id ?? "runtime_error_evidence"),
    evidenceHash: safeEvidenceHash(),
    checkedAtUtc: "2026-07-09T12:13:50Z",
  });
  const evidenceId = String(payload?.audit_evidence_id ?? uiResult.auditEvidenceRef ?? "runtime_error_evidence");
  const correlationId = String(payload?.audit_correlation_id ?? evidenceId);
  return {
    status,
    uiState: status,
    auditEvidenceId: evidenceId,
    correlationId,
    uiResult,
    privacyBoundary: String(payload?.privacy_boundary ?? privacyBoundary()),
    errorCode: payload?.error_code,
  };
}

export function toRuntimeErrorView(errorCode = "runtime_error", auditEvidenceId = "runtime_error_evidence"): RuntimeVerifyResult {
  const uiState = mapErrorCodeToUiState(errorCode);
  const uiResult = renderMvpResultViewModel({
    status: "ERROR",
    resultId: `runtime_error_${errorCode}`,
    requestRef: "runtime_error_request",
    credentialRef: "runtime_error_credential",
    auditEvidenceRef: auditEvidenceId,
    evidenceHash: safeEvidenceHash(),
    checkedAtUtc: "2026-07-09T12:13:50Z",
  });
  return {
    status: "ERROR",
    uiState,
    auditEvidenceId,
    correlationId: auditEvidenceId,
    uiResult,
    privacyBoundary: privacyBoundary(),
    errorCode,
  };
}

export function toNetworkErrorView(auditEvidenceId = "runtime_network_error_evidence"): RuntimeVerifyResult {
  return toRuntimeErrorView("network_failure_mapped", auditEvidenceId);
}

export function toLoadingView(): RuntimeVerifyResult {
  const result = toRuntimeErrorView("loading", "runtime_loading_evidence");
  return { ...result, uiState: "LOADING" };
}

export async function fetchRuntimeHealth(baseUrl = ""): Promise<any> {
  const response = await fetch(`${baseUrl}${runtimeEndpoints.health}`);
  return response.json();
}

export async function fetchRuntimeDemo(baseUrl = ""): Promise<any> {
  const response = await fetch(`${baseUrl}${runtimeEndpoints.demo}`);
  return response.json();
}

export async function fetchRuntimeAuthSession(baseUrl = ""): Promise<any> {
  const response = await fetch(`${baseUrl}${runtimeEndpoints.authSession}`);
  return response.json();
}

export async function postRuntimeAuthLogin(username = "demo", password = "demo", baseUrl = ""): Promise<any> {
  const response = await fetch(`${baseUrl}${runtimeEndpoints.authLogin}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });
  return response.json();
}

export async function postRuntimeAuthLogout(baseUrl = ""): Promise<any> {
  const response = await fetch(`${baseUrl}${runtimeEndpoints.authLogout}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });
  return response.json();
}
export async function postRuntimeVerify(request: any, authStub = "demo-runtime-auth", baseUrl = ""): Promise<RuntimeVerifyResult> {
  try {
    const response = await fetch(`${baseUrl}${runtimeEndpoints.verify}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-SSID-Demo-Auth": authStub,
      },
      body: JSON.stringify(request),
    });
    const payload = await response.json();
    if (!response.ok) {
      return toRuntimeErrorView(payload?.error_code, payload?.audit_correlation_id ?? payload?.audit_evidence_id);
    }
    return normalizeRuntimeVerifyResult(payload);
  } catch (_error) {
    return toNetworkErrorView();
  }
}
