from __future__ import annotations

import importlib.util
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_server_module():
    path = REPO_ROOT / "frontend" / "server.py"
    spec = importlib.util.spec_from_file_location("ssid_ems_frontend_server_routes", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_canonical_admin_registry_has_unique_groups_and_all_routes():
    server = load_server_module()
    assert server.RESTORE_ROUTES == [
        "/console", "/live", "/office", "/team", "/board/[taskId]",
        "/content/[contentId]", "/memory/[docId]", "/governance/command-center",
        "/governance/remediation", "/governance/sot-status", "/operations",
        "/automation", "/knowledge", "/risk",
    ]
    assert server.ADMIN_ROUTES == [
        "/admin/compliance/exceptions", "/admin/compliance/jurisdictions",
        "/admin/audit/reports", "/admin/runtime/blockers", "/admin/settings",
        "/admin/settings/providers", "/admin/settings/integrations",
        "/admin/settings/feature-gates",
    ]
    assert len(set(server.RESTORE_ROUTES + server.ADMIN_ROUTES)) == 22
    assert {group for group, _label, _path in server.NAVIGATION} == {
        "Overview", "Operations", "Automation", "Knowledge", "Risk", "Governance", "Admin"
    }
    assert len({path for _group, _label, path in server.NAVIGATION}) == len(server.NAVIGATION)

    html = server.FrontendRequestHandler._index_html(object())
    registered_paths = set(re.findall(r"['\"](/[^'\"]+)['\"]", html))
    assert set(server.RESTORE_ROUTES + server.ADMIN_ROUTES) <= registered_paths
    assert "renderRoute" in html
    assert "breadcrumbs" in html


def test_frontend_server_serves_every_registered_spa_route():
    server = load_server_module()
    assert set(server.SPA_ROUTE_PREFIXES) >= set(server.RESTORE_ROUTES + server.ADMIN_ROUTES)


if __name__ == "__main__":
    test_canonical_admin_registry_has_unique_groups_and_all_routes()
    test_frontend_server_serves_every_registered_spa_route()
    print("ok")
