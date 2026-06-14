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

Viewer commands use the existing websocket command channel. Each JSON payload is
prefixed with `C:` before being sent to the standalone websocket:

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

Reset to the default isometric view and resize:

```json
{"type":"viewer_command","command":"reset"}
```

Rotate by degrees around the viewer axes:

```json
{"type":"viewer_command","command":"rotate","axis":"x","delta":10}
{"type":"viewer_command","command":"rotate","axis":"x","delta":-10}
{"type":"viewer_command","command":"rotate","axis":"z","delta":10}
{"type":"viewer_command","command":"rotate","axis":"z","delta":-10}
```

Pan in screen-aligned directions:

```json
{"type":"viewer_command","command":"pan","direction":"left","step":10}
{"type":"viewer_command","command":"pan","direction":"right","step":10}
{"type":"viewer_command","command":"pan","direction":"up","step":10}
{"type":"viewer_command","command":"pan","direction":"down","step":10}
{"type":"viewer_command","command":"pan","direction":"forward","step":10}
{"type":"viewer_command","command":"pan","direction":"backward","step":10}
```

Zoom relative to the current camera zoom. Positive `delta` values increase
camera zoom; negative values decrease it.

```json
{"type":"viewer_command","command":"zoom","delta":100}
{"type":"viewer_command","command":"zoom","delta":-100}
```

Set absolute camera state. Each camera field is optional.

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

Python clients can use `viewer_command` instead of building the websocket
payload manually:

```python
from ocp_vscode.comms import viewer_command

viewer_command("view", value="front", port=3939)
viewer_command("rotate", axis="x", delta=10, port=3939)
viewer_command("pan", direction="left", step=10, port=3939)
viewer_command("zoom", delta=100, port=3939)
```

The helper is fire-and-forget: a `{}` return means the websocket payload was
sent, not that the browser accepted or applied the camera command. This command
channel is supported by the standalone viewer websocket and the VS Code viewer
command server; the standalone `/viewer` URL remains the simplest target for an
Emacs xwidget workflow.

## Emacs Command Shape

An Emacs integration can mirror the navigation shape used by
`scad-ts-preview-mode`, while sending the JSON protocol shown above. This is a
behavioral/keymap outline only; do not copy GPL implementation code from
`scad-ts-mode`.

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
i            iso view
0            reset
```

Prefix arguments should scale `delta` or `step` before sending JSON. For
example, an Emacs command can convert a numeric prefix into a larger rotate
`delta`, pan `step`, or zoom `delta`, then send a `C:`-prefixed
`viewer_command` websocket message.
