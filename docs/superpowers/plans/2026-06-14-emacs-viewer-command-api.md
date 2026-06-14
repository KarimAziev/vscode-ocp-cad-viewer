# Emacs Viewer Command API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone websocket `viewer_command` API so Emacs/xwidgets can rotate, pan, zoom, and switch views without mouse events or browser focus.

**Architecture:** Extend the existing standalone `C:` command path to forward validated `viewer_command` payloads to the browser client. Add a browser-side dispatcher that applies camera changes through existing viewer methods and emits normal status updates. Keep Emacs integration protocol-oriented: documentation shows how Emacs can send JSON commands, while full Emacs package code remains outside this Apache-2.0 repository.

**Tech Stack:** Python 3, Flask-Sock standalone server, `websockets.sync.client`, `orjson`, browser JavaScript in the shared viewer templates, pytest.

---

## File Structure

- Modify `ocp_vscode/standalone.py`: validate and forward `viewer_command` messages from `C:` websocket commands to the browser client.
- Modify `ocp_vscode/comms.py`: expose `viewer_command(...)` and make `send_command({"type": "viewer_command", ...})` no-response.
- Modify `resources/viewer.html`: add browser-side command dispatcher and camera operations for VS Code/webview resource copy.
- Modify `ocp_vscode/templates/viewer.html`: add the same browser-side command dispatcher and camera operations for standalone Flask template copy.
- Create `tests/test_viewer_command.py`: focused unit tests for server forwarding, malformed command handling, no-response client behavior, and helper payload shape.
- Create `docs/emacs.md`: document raw protocol commands and the intended Emacs command/keymap shape.

## Task 1: Standalone Forwarding Tests

**Files:**
- Create: `tests/test_viewer_command.py`
- Modify: none
- Test: `tests/test_viewer_command.py`

- [ ] **Step 1: Write failing tests for standalone forwarding**

Create `tests/test_viewer_command.py` with this content:

```python
"""Tests for the standalone viewer_command websocket protocol."""

import orjson

from ocp_vscode.standalone import Viewer


class FakeBrowserClient:
    """Minimal websocket-like browser client for forwarding tests."""

    def __init__(self):
        self.sent = []

    def send(self, data):
        self.sent.append(data)


def _viewer_with_browser(browser=None):
    """Create a Viewer shell without starting Flask or backend services."""
    viewer = Viewer.__new__(Viewer)
    viewer.debug = False
    viewer.javascript_client = browser
    viewer.not_registered_called = False

    def not_registered():
        viewer.not_registered_called = True

    viewer.not_registered = not_registered
    viewer.debug_print = lambda *args: None
    return viewer


def test_viewer_command_payload_is_forwarded_to_browser():
    browser = FakeBrowserClient()
    viewer = _viewer_with_browser(browser)
    payload = b'{"type":"viewer_command","command":"view","value":"front"}'

    assert viewer._forward_viewer_command(payload) is True

    assert browser.sent == [payload]
    assert viewer.not_registered_called is False


def test_viewer_command_without_browser_is_not_forwarded():
    viewer = _viewer_with_browser(browser=None)
    payload = b'{"type":"viewer_command","command":"view","value":"front"}'

    assert viewer._forward_viewer_command(payload) is False

    assert viewer.not_registered_called is True


def test_valid_viewer_command_requires_command_string():
    assert Viewer._is_viewer_command(
        {"type": "viewer_command", "command": "view", "value": "front"}
    )
    assert not Viewer._is_viewer_command({"type": "viewer_command"})
    assert not Viewer._is_viewer_command({"type": "viewer_command", "command": 4})
    assert not Viewer._is_viewer_command("viewer_command")


def test_malformed_viewer_command_is_ignored_without_forwarding():
    browser = FakeBrowserClient()
    viewer = _viewer_with_browser(browser)
    payload = orjson.dumps({"type": "viewer_command"})
    cmd = orjson.loads(payload)

    assert Viewer._is_viewer_command(cmd) is False

    assert browser.sent == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_viewer_command.py -q
```

Expected: FAIL with errors like:

```text
AttributeError: 'Viewer' object has no attribute '_forward_viewer_command'
AttributeError: type object 'Viewer' has no attribute '_is_viewer_command'
```

## Task 2: Standalone Forwarding Implementation

**Files:**
- Modify: `ocp_vscode/standalone.py`
- Test: `tests/test_viewer_command.py`

- [ ] **Step 1: Add validation and forwarding helpers**

In `ocp_vscode/standalone.py`, inside `class Viewer`, place these methods after `not_registered` and before `handle_message`:

```python
    @staticmethod
    def _is_viewer_command(cmd):
        """Return True when cmd is a browser-forwarded viewer command."""
        return (
            isinstance(cmd, dict)
            and cmd.get("type") == "viewer_command"
            and isinstance(cmd.get("command"), str)
        )

    def _forward_viewer_command(self, data):
        """Forward a validated viewer_command payload to the browser client."""
        if self.javascript_client is None:
            self.not_registered()
            return False
        self.javascript_client.send(data)
        return True
```

- [ ] **Step 2: Forward viewer_command from the command branch**

In `ocp_vscode/standalone.py`, in `Viewer.handle_message`, add this branch after the `set_relative_time` branch:

```python
                elif Viewer._is_viewer_command(cmd):
                    self.debug_print(
                        f"[{message_type}] Received viewer_command:",
                        cmd.get("command"),
                    )
                    self._forward_viewer_command(data)

                elif isinstance(cmd, dict) and cmd.get("type") == "viewer_command":
                    self.debug_print(
                        f"[{message_type}] Ignored malformed viewer_command:",
                        cmd,
                    )
```

The resulting command branch should keep the existing `status`, `config`, `screenshot`, and `set_relative_time` behavior intact.

- [ ] **Step 3: Run forwarding tests**

Run:

```bash
pytest tests/test_viewer_command.py -q
```

Expected: the standalone forwarding tests pass, while later comms tests do not exist yet.

- [ ] **Step 4: Commit standalone forwarding**

Run:

```bash
git add ocp_vscode/standalone.py tests/test_viewer_command.py
git commit -m "feat: forward standalone viewer commands"
```

## Task 3: Python Client No-Response Tests

**Files:**
- Modify: `tests/test_viewer_command.py`
- Test: `tests/test_viewer_command.py`

- [ ] **Step 1: Add comms tests**

Append these tests to `tests/test_viewer_command.py`:

```python
class DummyWebsocket:
    """Context-manager websocket that records sends and fails on recv."""

    def __init__(self):
        self.sent = []
        self.recv_called = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def send(self, data):
        self.sent.append(data)

    def recv(self):
        self.recv_called = True
        raise AssertionError("viewer_command must not wait for recv()")


def test_send_command_viewer_command_does_not_wait_for_response(monkeypatch):
    from ocp_vscode import comms

    dummy = DummyWebsocket()

    def fake_connect(url, close_timeout):
        assert url == "ws://127.0.0.1:39888"
        assert close_timeout == 0.05
        return dummy

    monkeypatch.setattr(comms, "connect", fake_connect)

    result = comms.send_command(
        {"type": "viewer_command", "command": "view", "value": "front"},
        port=39888,
    )

    assert result == {}
    assert dummy.recv_called is False
    assert dummy.sent == [
        b'C:{"type":"viewer_command","command":"view","value":"front"}'
    ]


def test_viewer_command_helper_builds_payload(monkeypatch):
    from ocp_vscode import comms

    calls = []

    def fake_send_command(data, port=None, title=None, timeit=False):
        calls.append(
            {
                "data": data,
                "port": port,
                "title": title,
                "timeit": timeit,
            }
        )
        return {}

    monkeypatch.setattr(comms, "send_command", fake_send_command)

    assert comms.viewer_command("rotate", axis="x", delta=10, port=39888) == {}

    assert calls == [
        {
            "data": {
                "type": "viewer_command",
                "command": "rotate",
                "axis": "x",
                "delta": 10,
            },
            "port": 39888,
            "title": None,
            "timeit": False,
        }
    ]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/test_viewer_command.py -q
```

Expected: FAIL with:

```text
AssertionError: viewer_command must not wait for recv()
AttributeError: module 'ocp_vscode.comms' has no attribute 'viewer_command'
```

## Task 4: Python Client Implementation

**Files:**
- Modify: `ocp_vscode/comms.py`
- Test: `tests/test_viewer_command.py`

- [ ] **Step 1: Export viewer_command**

In `ocp_vscode/comms.py`, add `"viewer_command"` to `__all__`:

```python
__all__ = [
    "send_data",
    "send_command",
    "viewer_command",
    "send_response",
    "set_port",
    "get_port",
    "listener",
    "is_pytest",
]
```

- [ ] **Step 2: Make viewer_command no-response**

In `_send`, replace:

```python
                        no_response_commands = ("screenshot", "set_relative_time")
```

with:

```python
                        no_response_commands = (
                            "screenshot",
                            "set_relative_time",
                            "viewer_command",
                        )
```

- [ ] **Step 3: Add the helper function**

In `ocp_vscode/comms.py`, place this function after `send_command`:

```python
def viewer_command(command, port=None, timeit=False, **kwargs):
    """Send a fire-and-forget viewer_command to the browser viewer."""
    data = {"type": "viewer_command", "command": command}
    data.update(kwargs)
    return send_command(data, port=port, timeit=timeit)
```

- [ ] **Step 4: Run comms tests**

Run:

```bash
pytest tests/test_viewer_command.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Python client support**

Run:

```bash
git add ocp_vscode/comms.py tests/test_viewer_command.py
git commit -m "feat: add viewer command client helper"
```

## Task 5: Browser Command Dispatcher

**Files:**
- Modify: `resources/viewer.html`
- Modify: `ocp_vscode/templates/viewer.html`
- Test: manual browser verification later in Task 8

- [ ] **Step 1: Add camera status and command helpers to `resources/viewer.html`**

In `resources/viewer.html`, place this code after `normalize(v)` and before `send(command, message)`:

```javascript
            function degreesToRadians(degrees) {
                return (degrees * Math.PI) / 180.0;
            }

            function isFiniteNumber(value) {
                return typeof value === "number" && Number.isFinite(value);
            }

            function cameraStatus() {
                if (!viewer) {
                    return;
                }
                _position = message["position"] = viewer.getCameraPosition();
                _quaternion = message["quaternion"] = viewer.getCameraQuaternion();
                _target = message["target"] = viewer.controls.getTarget().toArray();
                _zoom = message["zoom"] = viewer.getCameraZoom();
                _camera_distance = viewer.camera.camera_distance;
                send("status", message);
            }

            function refreshAfterCameraCommand() {
                if (!viewer) {
                    return;
                }
                if (viewer.gridHelper) {
                    viewer.gridHelper.clearCache();
                    viewer.gridHelper.update(viewer.getCameraZoom(), true);
                }
                viewer.update(true, true);
                cameraStatus();
            }

            function applyCameraTargetAndPosition(target, position) {
                viewer.setCameraTarget(target.toArray());
                viewer.setCameraPosition(position.toArray());
                const camera = viewer.camera.getCamera();
                camera.lookAt(target);
                viewer.setCameraQuaternion(camera.quaternion.toArray());
                refreshAfterCameraCommand();
            }

            function handleViewerCommand(data) {
                if (!viewer || !data || typeof data.command !== "string") {
                    return;
                }

                const command = data.command;
                if (command === "view") {
                    const views = ["iso", "left", "right", "top", "bottom", "rear", "front"];
                    if (views.includes(data.value)) {
                        viewer.setView(data.value);
                        refreshAfterCameraCommand();
                    }
                    return;
                }

                if (command === "reset") {
                    viewer.setView("iso");
                    viewer.resize();
                    refreshAfterCameraCommand();
                    return;
                }

                if (command === "set") {
                    if (Array.isArray(data.target)) {
                        viewer.setCameraTarget(data.target);
                    }
                    if (Array.isArray(data.position)) {
                        viewer.setCameraPosition(data.position);
                    }
                    if (Array.isArray(data.quaternion)) {
                        viewer.setCameraQuaternion(data.quaternion);
                    }
                    if (isFiniteNumber(data.zoom)) {
                        viewer.setCameraZoom(data.zoom);
                    }
                    refreshAfterCameraCommand();
                    return;
                }

                if (command === "zoom") {
                    const delta = isFiniteNumber(data.delta) ? data.delta : 0;
                    const currentZoom = viewer.getCameraZoom();
                    const nextZoom = Math.max(0.01, currentZoom + delta / 1000.0);
                    viewer.setCameraZoom(nextZoom);
                    refreshAfterCameraCommand();
                    return;
                }

                const camera = viewer.camera.getCamera();
                const target = viewer.controls.getTarget().clone();
                const position = camera.position.clone();

                if (command === "pan") {
                    const step = isFiniteNumber(data.step) ? data.step : 10;
                    const direction = data.direction;
                    const forward = target.clone().sub(position).normalize();
                    const up = camera.up.clone().normalize();
                    const right = forward.clone().cross(up).normalize();
                    const screenUp = right.clone().cross(forward).normalize();
                    const delta = position.clone().set(0, 0, 0);

                    if (direction === "left") {
                        delta.add(right.clone().multiplyScalar(-step));
                    } else if (direction === "right") {
                        delta.add(right.clone().multiplyScalar(step));
                    } else if (direction === "up") {
                        delta.add(screenUp.clone().multiplyScalar(step));
                    } else if (direction === "down") {
                        delta.add(screenUp.clone().multiplyScalar(-step));
                    } else if (direction === "forward") {
                        delta.add(forward.clone().multiplyScalar(step));
                    } else if (direction === "backward") {
                        delta.add(forward.clone().multiplyScalar(-step));
                    } else {
                        return;
                    }

                    applyCameraTargetAndPosition(target.add(delta), position.add(delta));
                    return;
                }

                if (command === "rotate") {
                    const delta = isFiniteNumber(data.delta) ? data.delta : 0;
                    const radians = degreesToRadians(delta);
                    const forward = target.clone().sub(position).normalize();
                    const up = camera.up.clone().normalize();
                    const right = forward.clone().cross(up).normalize();
                    const axis =
                        data.axis === "x"
                            ? right
                            : data.axis === "z"
                              ? up
                              : null;

                    if (axis == null) {
                        return;
                    }

                    const rotation = camera.quaternion.clone();
                    rotation.setFromAxisAngle(axis, radians);
                    const offset = position.sub(target).applyQuaternion(rotation);
                    applyCameraTargetAndPosition(target, target.clone().add(offset));
                }
            }
```

- [ ] **Step 2: Dispatch viewer_command messages in `resources/viewer.html`**

In `resources/viewer.html`, in the `window.addEventListener("message", ...)` chain, add this branch after `set_relative_time` and before `backend_response`:

```javascript
                } else if (data.type === "viewer_command") {
                    handleViewerCommand(data);
```

- [ ] **Step 3: Reuse cameraStatus in `render()`**

In `resources/viewer.html`, replace this block in `render()`:

```javascript
                _position = message["position"] = viewer.getCameraPosition();
                _quaternion = message["quaternion"] = viewer.getCameraQuaternion();
                _target = message["target"] = viewer.controls.getTarget().toArray();
                _zoom = message["zoom"] = viewer.getCameraZoom();
                _camera_distance = viewer.camera.camera_distance;
```

with:

```javascript
                cameraStatus();
```

Keep the existing later `send("status", message);` call in place for now. The duplicate status message is acceptable during render and avoids changing render status semantics in the same task.

- [ ] **Step 4: Apply the same browser code to the standalone template**

Make the same three edits in `ocp_vscode/templates/viewer.html`:

- add the helper block after `normalize(v)` and before `send(command, message)`;
- add the `viewer_command` dispatch branch after `set_relative_time`;
- replace the render camera field assignment block with `cameraStatus();`.

- [ ] **Step 5: Run lightweight checks**

Run:

```bash
pytest tests/test_viewer_command.py -q
```

Expected: PASS.

Run:

```bash
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 6: Commit browser dispatcher**

Run:

```bash
git add resources/viewer.html ocp_vscode/templates/viewer.html
git commit -m "feat: handle browser viewer commands"
```

## Task 6: Emacs Protocol Documentation

**Files:**
- Create: `docs/emacs.md`
- Test: documentation review through exact command examples

- [ ] **Step 1: Add Emacs usage documentation**

Create `docs/emacs.md` with this content:

````markdown
# Emacs Standalone Viewer Control

The standalone viewer can be displayed in Emacs xwidgets and controlled through
the viewer websocket without browser focus or mouse gestures.

Start the standalone viewer:

```bash
python -m ocp_vscode --port 3939
```

Open this URL in an xwidget browser:

```text
http://127.0.0.1:3939/viewer
```

Viewer commands use the existing websocket command channel. Each payload is
prefixed with `C:`:

```text
C:{"type":"viewer_command","command":"view","value":"front"}
```

## Command Examples

Fixed views:

```json
{"type":"viewer_command","command":"view","value":"front"}
{"type":"viewer_command","command":"view","value":"rear"}
{"type":"viewer_command","command":"view","value":"left"}
{"type":"viewer_command","command":"view","value":"right"}
{"type":"viewer_command","command":"view","value":"top"}
{"type":"viewer_command","command":"view","value":"bottom"}
{"type":"viewer_command","command":"view","value":"iso"}
```

Reset:

```json
{"type":"viewer_command","command":"reset"}
```

Rotate:

```json
{"type":"viewer_command","command":"rotate","axis":"x","delta":10}
{"type":"viewer_command","command":"rotate","axis":"x","delta":-10}
{"type":"viewer_command","command":"rotate","axis":"z","delta":10}
{"type":"viewer_command","command":"rotate","axis":"z","delta":-10}
```

Pan:

```json
{"type":"viewer_command","command":"pan","direction":"left","step":10}
{"type":"viewer_command","command":"pan","direction":"right","step":10}
{"type":"viewer_command","command":"pan","direction":"up","step":10}
{"type":"viewer_command","command":"pan","direction":"down","step":10}
{"type":"viewer_command","command":"pan","direction":"forward","step":10}
{"type":"viewer_command","command":"pan","direction":"backward","step":10}
```

Zoom:

```json
{"type":"viewer_command","command":"zoom","delta":100}
{"type":"viewer_command","command":"zoom","delta":-100}
```

Absolute camera state:

```json
{
  "type": "viewer_command",
  "command": "set",
  "position": [100, 100, 100],
  "target": [0, 0, 0],
  "quaternion": [0, 0, 0, 1],
  "zoom": 1.2
}
```

## Python Helper

Python clients can use:

```python
from ocp_vscode.comms import viewer_command

viewer_command("view", value="front", port=3939)
viewer_command("rotate", axis="x", delta=10, port=3939)
viewer_command("pan", direction="left", step=10, port=3939)
viewer_command("zoom", delta=100, port=3939)
```

## Emacs Command Shape

An Emacs mode can mirror `scad-ts-preview-mode`:

```text
<right>      rotate z -step
<left>       rotate z +step
<up>         rotate x +step
<down>       rotate x -step
M-<left>     pan left
M-<right>    pan right
M-<up>       pan up
M-<down>     pan down
+            zoom in
-            zoom out
f            front view
t            top view
l            left view
r            right view
b            rear view
d            bottom view
```

Prefix arguments should scale `delta` or `step` before sending JSON.
````

- [ ] **Step 2: Run documentation checks**

Run:

```bash
rg -n "viewer_command|xwidgets|scad-ts-preview-mode" docs/emacs.md
```

Expected: matches in the command examples and Emacs command shape sections.

- [ ] **Step 3: Commit documentation**

Run:

```bash
git add docs/emacs.md
git commit -m "docs: describe emacs viewer commands"
```

## Task 7: Focused Test Suite

**Files:**
- Modify: none
- Test: `tests/test_viewer_command.py`, `tests/test_standalone_cli.py`

- [ ] **Step 1: Run protocol tests**

Run:

```bash
pytest tests/test_viewer_command.py -q
```

Expected: PASS.

- [ ] **Step 2: Run standalone regression tests**

Run:

```bash
pytest tests/test_standalone_cli.py -q
```

Expected: PASS. These tests spawn standalone viewer subprocesses and may take longer than the protocol unit tests.

- [ ] **Step 3: Run TypeScript compile to catch unrelated shared template regressions**

Run:

```bash
yarn run compile
```

Expected: PASS. This does not parse browser template JavaScript, but confirms the VS Code extension TypeScript still compiles.

## Task 8: Manual Browser Verification

**Files:**
- Modify: none
- Test: running standalone viewer and raw websocket commands

- [ ] **Step 1: Start standalone viewer**

Run:

```bash
python -m ocp_vscode --port 39889 --debug
```

Expected output includes:

```text
Info: OCP CAD Viewer runs at http://127.0.0.1:39889
```

Keep this process running until the manual verification steps are complete.

- [ ] **Step 2: Open the standalone viewer**

Open:

```text
http://127.0.0.1:39889/viewer
```

Expected: the browser registers, and the standalone process prints:

```text
Info: Browser as viewer client registered
```

- [ ] **Step 3: Send fixed view command**

In a separate shell, run:

```bash
python - <<'PY'
from ocp_vscode.comms import set_port, viewer_command
set_port(39889)
viewer_command("view", value="front")
PY
```

Expected: the browser view changes to the front view.

- [ ] **Step 4: Send rotate, pan, and zoom commands**

Run:

```bash
python - <<'PY'
from ocp_vscode.comms import set_port, viewer_command
set_port(39889)
viewer_command("rotate", axis="x", delta=10)
viewer_command("rotate", axis="z", delta=-10)
viewer_command("pan", direction="left", step=10)
viewer_command("pan", direction="up", step=10)
viewer_command("zoom", delta=100)
PY
```

Expected: the camera visibly rotates, pans, and zooms without browser mouse input.

- [ ] **Step 5: Confirm status readback**

Run:

```bash
python - <<'PY'
from ocp_vscode.comms import set_port
from ocp_vscode.config import status
set_port(39889)
s = status()
for key in ("position", "quaternion", "target", "zoom"):
    print(key, s.get(key))
PY
```

Expected: each key prints a non-empty value after the browser has processed commands.

## Task 9: Final Review

**Files:**
- Modify: none
- Test: final status and diff review

- [ ] **Step 1: Review repository status**

Run:

```bash
git status --short
```

Expected: only the user's pre-existing `.gitignore` modification remains unstaged, unless manual verification produced expected local artifacts.

- [ ] **Step 2: Review recent commits**

Run:

```bash
git log --oneline -6
```

Expected: commits from this plan appear above the design commit.

- [ ] **Step 3: Summarize result**

Report:

```text
Implemented standalone viewer_command API for Emacs/xwidgets usage.
Verified with pytest tests/test_viewer_command.py -q.
Verified with pytest tests/test_standalone_cli.py -q.
Verified with yarn run compile.
Manual browser verification: <completed or reason not run>.
Pre-existing .gitignore change left untouched.
```
