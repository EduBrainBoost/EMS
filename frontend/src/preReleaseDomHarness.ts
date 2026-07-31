export const PRE_RELEASE_DOM_E2E_STATUS = "DOM_E2E_READY";
export const PRE_RELEASE_BROWSER_BINARY_STATUS = "BROWSER_BINARY_NOT_REQUIRED_FOR_LOCAL_PRE_RC";
export const PRE_RELEASE_PRIVACY_STATUS = "NO_PII_NO_SECRETS";

export const preReleaseDomFixture = `<main data-testid="ssid-pre-release-dom-e2e">
  <h1>SSID MVP Pre-Release DOM E2E</h1>
  <section aria-label="Demo Flow">
    <h2>Demo Flow</h2>
    <p>Runtime Health visible</p>
    <p>Demo Flow visible</p>
  </section>
  <section aria-label="Verify Flow">
    <h2>Verify Flow</h2>
    <p>PASS</p>
    <p>FAIL</p>
    <p>INSUFFICIENT</p>
    <p>ERROR</p>
    <p>AUTH_DENIED</p>
    <p>NETWORK_ERROR</p>
    <p>SCHEMA_INVALID</p>
    <p>Evidence ID: evpre_demo_evidence_hash_ref</p>
    <p>Correlation ID: evpre_demo_correlation_ref</p>
  </section>
  <section aria-label="Safety">
    <h2>Safety</h2>
    <p>DOM_E2E_READY</p>
    <p>BROWSER_BINARY_NOT_REQUIRED_FOR_LOCAL_PRE_RC</p>
    <p>NO_PII_NO_SECRETS</p>
  </section>
</main>`;

export function renderPreReleaseDomFixture(): string {
  return preReleaseDomFixture;
}
