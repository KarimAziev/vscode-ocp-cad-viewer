"""Tests for the standalone viewer_command websocket protocol."""

import pytest

from ocp_vscode import comms
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


class DummyWebsocket:
    """Context-manager websocket that fails if a response is awaited."""

    def __init__(self):
        self.sent = []
        self.recv_called = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def send(self, data):
        self.sent.append(data)

    def recv(self):
        self.recv_called = True
        raise AssertionError("viewer_command must not wait for websocket recv()")


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


def test_send_command_viewer_command_does_not_wait_for_response(monkeypatch):
    dummy_ws = DummyWebsocket()

    def fake_connect(url, close_timeout):
        assert url == "ws://127.0.0.1:39888"
        assert close_timeout == 0.05
        return dummy_ws

    monkeypatch.setattr(comms, "connect", fake_connect)

    result = comms.send_command(
        {"type": "viewer_command", "command": "view", "value": "front"},
        port=39888,
    )

    assert result == {}
    assert dummy_ws.sent == [
        b'C:{"type":"viewer_command","command":"view","value":"front"}'
    ]
    assert dummy_ws.recv_called is False


def test_viewer_command_helper_sends_viewer_command_payload(monkeypatch):
    sent_commands = []

    def fake_send_command(command, port=None, title=None, timeit=False):
        sent_commands.append((command, port, title, timeit))
        return {}

    monkeypatch.setattr(comms, "send_command", fake_send_command)

    assert (
        comms.viewer_command("rotate", axis="x", delta=10, port=39888, timeit=True)
        == {}
    )
    assert sent_commands == [
        (
            {
                "type": "viewer_command",
                "command": "rotate",
                "axis": "x",
                "delta": 10,
            },
            39888,
            None,
            True,
        )
    ]


def test_viewer_command_helper_protects_reserved_type_field(monkeypatch):
    sent_commands = []

    def fake_send_command(command, port=None, title=None, timeit=False):
        sent_commands.append((command, port, title, timeit))
        return {}

    monkeypatch.setattr(comms, "send_command", fake_send_command)

    assert comms.viewer_command("rotate", type="bad", port=39888) == {}
    assert sent_commands == [
        (
            {"type": "viewer_command", "command": "rotate"},
            39888,
            None,
            False,
        )
    ]
