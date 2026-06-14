"""Tests for the standalone viewer_command websocket protocol."""

import pytest

from ocp_vscode.standalone import Viewer


class FakeWebSocket:
    """Minimal websocket with receive and send behavior for protocol tests."""

    def __init__(self, incoming=None):
        self.incoming = list(incoming or [])
        self.sent = []

    def receive(self):
        if not self.incoming:
            raise StopIteration
        return self.incoming.pop(0)

    def send(self, data):
        self.sent.append(data)


def _viewer():
    """Create a Viewer shell without starting Flask or backend services."""
    viewer = Viewer.__new__(Viewer)
    viewer.debug = False
    viewer.javascript_client = None
    viewer.debug_print = lambda *args: None
    return viewer


def register_browser(viewer, browser_ws):
    """Register a browser websocket through the standalone protocol."""
    browser_ws.incoming = [b"L:{}"]
    with pytest.raises(StopIteration):
        viewer.handle_message(browser_ws)


def test_viewer_command_message_is_forwarded_from_command_websocket():
    viewer = _viewer()
    browser = FakeWebSocket()
    register_browser(viewer, browser)
    command_ws = FakeWebSocket(
        [b'C:{"type":"viewer_command","command":"view","value":"front"}']
    )

    with pytest.raises(StopIteration):
        viewer.handle_message(command_ws)

    assert browser.sent == ['{"type":"viewer_command","command":"view","value":"front"}']


def test_viewer_command_without_browser_reports_not_registered(capsys):
    viewer = _viewer()
    command_ws = FakeWebSocket(
        [b'C:{"type":"viewer_command","command":"view","value":"front"}']
    )

    with pytest.raises(StopIteration):
        viewer.handle_message(command_ws)

    captured = capsys.readouterr()
    assert "No browser registered" in captured.out


def test_malformed_viewer_command_is_ignored_without_forwarding(capsys):
    viewer = _viewer()
    browser = FakeWebSocket()
    register_browser(viewer, browser)
    command_ws = FakeWebSocket([b'C:{"type":"viewer_command"}'])

    with pytest.raises(StopIteration):
        viewer.handle_message(command_ws)

    assert browser.sent == []
    captured = capsys.readouterr()
    assert "No browser registered" not in captured.out
