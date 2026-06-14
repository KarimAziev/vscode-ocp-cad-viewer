# Emacs Viewer Command API Design

## Context

This fork targets standalone, Emacs-first usage of OCP CAD Viewer. Emacs will open
the standalone viewer URL in xwidgets:

```text
http://127.0.0.1:<port>/viewer
```

The user does not want to drive the 3D view through browser mouse gestures or the
current `three-cad-viewer` modifier-key scheme. The desired interaction model is
close to the OpenSCAD preview workflow in
`/Users/km/.emacs.d/straight/repos/scad-ts-mode/scad-ts-mode.el`: ordinary Emacs
commands and keybindings rotate, pan, zoom, and jump to fixed views.

The existing standalone viewer already has a websocket command channel:

- `C:` messages are command messages from Python or other clients.
- `L:` registers the browser client.
- `U:` sends browser status updates back to the standalone server.
- The server currently forwards only a few command types, such as `screenshot`
  and `set_relative_time`, to the browser.

The missing piece is a stable, non-mouse viewer command protocol.

## Goals

- Add a generic `viewer_command` protocol over the existing standalone websocket.
- Keep Emacs integration thin: Emacs sends JSON commands instead of injecting
  JavaScript or simulating mouse events.
- Support the same navigation categories as the existing OpenSCAD preview mode:
  rotate, pan, zoom, fixed views, and reset.
- Preserve the current mouse behavior for compatibility, but stop treating it as
  the primary interface for this fork.
- Keep VS Code-specific changes out of the first implementation unless needed to
  preserve shared files.

## Non-Goals

- Do not fork or patch `three-cad-viewer` unless the public viewer methods are
  insufficient.
- Do not implement a full Emacs package inside this Apache-2.0 repository.
  A small documentation example is acceptable. Copying GPL Emacs code from
  `scad-ts-mode.el` into this repository is out of scope.
- Do not replace the existing `modifier_keys` configuration.
- Do not require browser focus for navigation commands.

## Protocol

Clients send commands to the standalone websocket using the existing command
prefix:

```text
C:{"type":"viewer_command","command":"rotate","axis":"x","delta":10}
```

`viewer_command` messages are fire-and-forget. The sender does not wait for an
immediate command response. Current camera state remains available through the
existing `status` command, using normal status updates from the browser.

Initial command vocabulary:

```json
{"type":"viewer_command","command":"view","value":"front"}
{"type":"viewer_command","command":"reset"}
{"type":"viewer_command","command":"rotate","axis":"x","delta":10}
{"type":"viewer_command","command":"rotate","axis":"z","delta":-10}
{"type":"viewer_command","command":"pan","direction":"left","step":10}
{"type":"viewer_command","command":"pan","direction":"right","step":10}
{"type":"viewer_command","command":"pan","direction":"up","step":10}
{"type":"viewer_command","command":"pan","direction":"down","step":10}
{"type":"viewer_command","command":"pan","direction":"forward","step":10}
{"type":"viewer_command","command":"pan","direction":"backward","step":10}
{"type":"viewer_command","command":"zoom","delta":100}
{"type":"viewer_command","command":"set","position":[0,0,0],"target":[0,0,0],"quaternion":[0,0,0,1],"zoom":1.2}
```

Allowed fixed view values are:

```text
iso, left, right, top, bottom, rear, front
```

The `set` command is an escape hatch for absolute camera restoration. Each field
is optional; the browser applies only fields present in the payload.

## Standalone Server Changes

`ocp_vscode/standalone.py` should forward `viewer_command` payloads from `C:`
messages to the registered browser websocket client, using the same registration
path as `screenshot` and `set_relative_time`.

If no browser is registered, the server should use the existing
`not_registered()` behavior and continue serving future websocket messages.

Malformed command payloads should not terminate the websocket loop. The server
should ignore invalid `viewer_command` messages after logging in debug mode.

## Python Client Changes

`ocp_vscode/comms.py` should treat `viewer_command` as a no-response command, so
`send_command({"type": "viewer_command", ...})` does not block waiting for a
browser reply.

Optionally add a tiny helper:

```python
def viewer_command(command, port=None, **kwargs):
    return send_command({"type": "viewer_command", "command": command, **kwargs}, port=port)
```

This helper is convenience only. The raw websocket protocol remains the stable
interface for Emacs.

## Browser Changes

The browser-side template should add a single dispatcher in the existing
`window.addEventListener("message", ...)` handler:

```javascript
if (data.type === "viewer_command") {
    handleViewerCommand(data);
}
```

`handleViewerCommand` should:

- Ignore commands until `viewer` exists.
- Validate command names and values defensively.
- Use existing viewer methods where available:
  - `viewer.setView(...)`
  - `viewer.setCameraPosition(...)`
  - `viewer.setCameraQuaternion(...)`
  - `viewer.setCameraTarget(...)`
  - `viewer.setCameraZoom(...)`
  - `viewer.getCameraPosition()`
  - `viewer.getCameraQuaternion()`
  - `viewer.controls.getTarget()`
- Send status updates through the existing notification/status path after camera
  changes, so Emacs can query current state through `status`.

`view` and absolute `set` should be implemented first because they map directly
to existing methods. Relative `rotate`, `pan`, and `zoom` should use the current
camera, target, and zoom state to compute a new camera state without dispatching
synthetic DOM events.

## Emacs Integration Shape

The intended Emacs package can mirror `scad-ts-preview-mode` without depending
on browser focus:

- defcustoms for port, rotate step, pan step, and zoom step.
- one low-level `ocp-viewer-send-command` function.
- command functions such as:
  - `ocp-viewer-rotate-x+`
  - `ocp-viewer-rotate-x-`
  - `ocp-viewer-rotate-z+`
  - `ocp-viewer-rotate-z-`
  - `ocp-viewer-pan-left`
  - `ocp-viewer-pan-right`
  - `ocp-viewer-pan-up`
  - `ocp-viewer-pan-down`
  - `ocp-viewer-zoom-in`
  - `ocp-viewer-zoom-out`
  - `ocp-viewer-front-view`
  - `ocp-viewer-back-view`
  - `ocp-viewer-left-view`
  - `ocp-viewer-right-view`
  - `ocp-viewer-top-view`
  - `ocp-viewer-bottom-view`
  - `ocp-viewer-reset-view`
- prefix arguments scale `delta` or `step` before sending JSON.
- optional transient menu with the same command set.

Suggested keymap parity:

```text
<right>      rotate negative z / yaw right
<left>       rotate positive z / yaw left
<up>         rotate positive x / pitch up
<down>       rotate negative x / pitch down
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
b            back/rear view
d            bottom view
```

The Emacs package may use xwidgets only for display. Navigation commands should
use the websocket protocol directly.

## Error Handling

- Unknown commands are ignored and logged only when viewer debug mode is enabled.
- Invalid numeric fields fall back to defaults or are ignored.
- Commands sent before a browser registers do not crash the server.
- Commands sent before a model is loaded do not crash the browser.
- `status` remains the way to read back the last known camera state.

## Testing

Focused automated coverage:

- Unit or integration test that the standalone server forwards a
  `viewer_command` payload to the registered browser client.
- Test that `send_command({"type": "viewer_command", ...})` returns without
  waiting for a browser response.
- Test that malformed `viewer_command` payloads do not terminate the server
  message loop.

Manual or browser-level verification:

- Open the standalone viewer in a browser or xwidget.
- Send raw websocket commands for fixed view, rotate, pan, and zoom.
- Confirm camera state changes visually.
- Confirm `status()` reflects updated `position`, `quaternion`, `target`, and
  `zoom` after commands.

## Implementation Order

1. Add standalone forwarding for `viewer_command`.
2. Add no-response handling and optional `viewer_command` Python helper.
3. Add browser dispatcher and implement `view`, `reset`, and absolute `set`.
4. Add relative `zoom`.
5. Add relative `rotate` and screen-aligned `pan`.
6. Add focused tests and a short Emacs protocol example.
