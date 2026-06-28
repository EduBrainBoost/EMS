/**
 * EMS Frontend App — Local Rebuild Status Screen
 * No real API calls. No external assets. No branding overkill.
 */

import React from "react";
import { EMS_BACKEND_PORT, EMS_FRONTEND_PORT, ENV_MODE, SERVICE_NAME, VERSION } from "./config";

const App: React.FC = () => {
  return (
    <div style={{ fontFamily: "monospace", padding: 24 }}>
      <h1>{SERVICE_NAME}</h1>
      <p>Version: {VERSION}</p>
      <p>Mode: {ENV_MODE}</p>
      <p>Frontend Port: {EMS_FRONTEND_PORT}</p>
      <p>Backend Port: {EMS_BACKEND_PORT}</p>
      <p>Status: <strong>NOT STARTED</strong> (rebuild phase)</p>
      <p>No services are running. This is a static readiness screen.</p>
    </div>
  );
};

export default App;
