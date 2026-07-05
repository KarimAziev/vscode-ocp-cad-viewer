"""Tests for standalone static asset serving."""

import ocp_vscode.standalone as standalone
from ocp_vscode.standalone import Viewer


def test_cleanup_ignores_unstarted_port(monkeypatch):
    monkeypatch.setattr(standalone, "PORT", 0)

    def fail_if_called(port):
        raise AssertionError(f"del_port should not be called for port {port}")

    monkeypatch.setattr(standalone, "del_port", fail_if_called)

    standalone.cleanup()


def test_serves_three_cad_viewer_js_from_node_modules_fallback(tmp_path, monkeypatch):
    static_root = tmp_path / "static"
    node_dist = tmp_path / "node_modules" / "three-cad-viewer" / "dist"
    node_dist.mkdir(parents=True)
    (node_dist / "three-cad-viewer.esm.js").write_text(
        "export const fallback = true;\n", encoding="utf-8"
    )

    monkeypatch.setattr(standalone, "STATIC_ROOT", static_root, raising=False)
    monkeypatch.setattr(standalone, "THREE_CAD_VIEWER_DIST", node_dist, raising=False)

    viewer = Viewer({"port": 0})
    response = viewer.app.test_client().get("/static/js/three-cad-viewer.esm.js")

    assert response.status_code == 200
    assert response.text == "export const fallback = true;\n"


def test_serves_three_cad_viewer_css_from_node_modules_fallback(tmp_path, monkeypatch):
    static_root = tmp_path / "static"
    node_dist = tmp_path / "node_modules" / "three-cad-viewer" / "dist"
    node_dist.mkdir(parents=True)
    (node_dist / "three-cad-viewer.css").write_text(
        ".viewer { display: block; }\n", encoding="utf-8"
    )

    monkeypatch.setattr(standalone, "STATIC_ROOT", static_root, raising=False)
    monkeypatch.setattr(standalone, "THREE_CAD_VIEWER_DIST", node_dist, raising=False)

    viewer = Viewer({"port": 0})
    response = viewer.app.test_client().get("/static/css/three-cad-viewer.css")

    assert response.status_code == 200
    assert response.text == ".viewer { display: block; }\n"
