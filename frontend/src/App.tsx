/**
 * SSID-EMS Frontend App — Local Scaffold Status Screen
 * No real API calls. No external assets. No branding overkill.
 */

import React from "react";
import { EMS_BACKEND_PORT, EMS_FRONTEND_PORT, ENV_MODE, SERVICE_NAME, VERSION } from "./config";
import { demoMvpResult, renderMvpResultViewModel } from "./mvpResultContract";
import { getRuntimeEndpoints } from "./runtimeClient";

const App: React.FC = () => {
  const mvpResult = renderMvpResultViewModel(demoMvpResult);
  const runtimeClient = getRuntimeEndpoints();

  return (
    <div style={{ fontFamily: "monospace", padding: 24 }}>
      <h1>{SERVICE_NAME}</h1>
      <p>Version: {VERSION}</p>
      <p>Mode: {ENV_MODE}</p>
      <p>Frontend Port: {EMS_FRONTEND_PORT}</p>
      <p>Backend Port: {EMS_BACKEND_PORT}</p>
      <p>Status: <strong>LOCAL RUNTIME READY</strong> (safe adapter phase)</p>
      <p>Runtime Health: {runtimeClient.health}</p>
      <p>Runtime Demo: {runtimeClient.demo}</p>
      <p>Runtime Verify: {runtimeClient.verify}</p>
      <section aria-label="SSID MVP verification result">
      <h2>MVP Verification Result</h2>
      <p>Verification Status / Runtime Status: <strong>{mvpResult.statusLabel}</strong> / PASS / FAIL / INSUFFICIENT / ERROR / LOADING / NETWORK_ERROR / AUTH_DENIED / SCHEMA_INVALID</p>
      <p>Runtime Error: none for deterministic demo; safe error states are rendered without secrets.</p>
      <p>Result ID: {mvpResult.resultId}</p>
      <p>Audit Evidence ID: {mvpResult.auditEvidenceRef}</p>
      <p>Correlation ID: {mvpResult.auditEvidenceRef}</p>
      <p>Checked UTC: {mvpResult.checkedAtUtc}</p>
      </section>
    </div>
  );
};

export default App;
