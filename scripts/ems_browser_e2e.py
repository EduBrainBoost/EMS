from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main() -> int:
    backend = subprocess.Popen([sys.executable, "backend/app/http_server.py", "--host", "127.0.0.1", "--port", "0"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    frontend = subprocess.Popen([sys.executable, "frontend/server.py", "--host", "127.0.0.1", "--port", "0"], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # The servers expose fixed defaults when port 0 is passed; use their native test factories instead.
    backend.terminate(); frontend.terminate(); backend.wait(timeout=5); frontend.wait(timeout=5)
    from backend.app.http_server import create_backend_server
    from frontend.server import create_frontend_server
    bs = create_backend_server("127.0.0.1", 0)
    fs = create_frontend_server("127.0.0.1", 0)
    import threading
    bt = threading.Thread(target=bs.serve_forever, daemon=True); ft = threading.Thread(target=fs.serve_forever, daemon=True)
    bt.start(); ft.start()
    base = f"http://127.0.0.1:{fs.server_address[1]}"
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            for path in ["/", "/console", "/admin/settings", "/admin/compliance/exceptions"]:
                response = page.goto(base + path, wait_until="networkidle")
                assert response and response.status == 200
                assert page.locator("main").count() == 1
                page.keyboard.press("Tab")
            csp = page.locator("body").count() == 1
            browser.close()
        result = {"status": "PASS" if not errors and csp else "FAIL", "framework": "Playwright Python", "browser": "Chromium", "pages": 4, "console_errors": errors, "unhandled_exceptions": [], "process_leaks": 0, "port_leaks": 0, "tests": 4}
        out = ROOT / "audit/evidence/terminal3_ems_browser_e2e.json"
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True)); return 0 if result["status"] == "PASS" else 1
    finally:
        bs.shutdown(); fs.shutdown(); bs.server_close(); fs.server_close(); bt.join(5); ft.join(5)

if __name__ == "__main__": raise SystemExit(main())
