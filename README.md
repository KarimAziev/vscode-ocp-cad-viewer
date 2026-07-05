# About

This fork of the original VS Code extension for viewing
[build123d](https://github.com/gumyr/build123d) and
[CadQuery](https://github.com/cadquery/cadquery) objects adds
WebSocket-based remote control to the standalone browser viewer.

When the standalone viewer is open at
`http://127.0.0.1:<port>/viewer` in an Emacs xwidget or any other
JavaScript-capable browser, an external client can control the camera over the
viewer websocket protocol. This enables rotation, zooming, panning, fixed-view
switching, and reset commands without requiring browser focus or mouse input.

The primary client for this fork is the Emacs Lisp package
[KarimAziev/ocp-cad-viewer](https://github.com/KarimAziev/ocp-cad-viewer), but
the protocol is editor-agnostic: any editor, script, or tool that can send
websocket messages to `ws://127.0.0.1:<port>` can drive the viewer.

**Table of Contents**

> - [About](#about)
>     - [Installation](#installation)
>         - [Prerequisites](#prerequisites)
>         - [Installation within VS Code](#installation-within-vs-code)
>         - [Installation via CLI](#installation-via-cli)
>         - [Using this fork from another Python project](#using-this-fork-from-another-python-project)
>         - [Installation in code-server](#installation-in-code-server)
>     - [Usage](#usage)
>         - [Running code with VS Code's "Run" menu](#running-code-with-vs-codes-run-menu)
>         - [Running code using Jupyter extension](#running-code-using-jupyter-extension)
>         - [Standalone mode](#standalone-mode)
>         - [Emacs layer](#emacs-layer)
>         - [Viewer command API](#viewer-command-api)
>         - [Debugging code with visual debugging](#debugging-code-with-visual-debugging)
>         - [Library Manager](#library-manager)
>         - [Extra topics](#extra-topics)
>             - [Getting started](#getting-started)
>             - [Working with the viewer](#working-with-the-viewer)
>             - [Python `show*` commands](#python-show-commands)
>             - [Python API reference](#python-api-reference)
>             - [VS Code reference](#vs-code-reference)
>             - [Examples and snippets](#examples-and-snippets)
>             - [Other editors support](#other-editors-support)
>             - [Help](#help)
>     - [Development](#development)
>     - [Changes](#changes)
>     - [v3.4.0](#v340)

![](screenshots/overview.png)

A typical session is just a few lines of Python:

```python
# build123d
from build123d import Box
from ocp_vscode import show

show(Box(1, 2, 3))
```

```python
# CadQuery
import cadquery as cq
from ocp_vscode import show

show(cq.Workplane().box(1, 2, 3))
```

## Installation

### Prerequisites

- Necessary tools: `python` and `pip` or `uv pip`/`uv add` available in the Python environment that will be used for CAD development.
- For this fork's source checkout and Emacs workflow:
    - `git`
    - `uv` or another Python virtual environment manager
    - Node.js with `corepack`/`yarn`

**Notes**:

- To use OCP CAD Viewer, start VS Code from the commandline in the Python environment you want to use or select the right Python interpreter in VS Code first. **OCP CAD Viewer depends on VS Code using the right Python interpreter** (i.e. mamba / conda / pyenv / poetry / ... environment).
- For VSCodium, the extension is not available in the VS code market place. You need to download the the vsix file from the [release folder](https://github.com/bernhard-42/vscode-ocp-cad-viewer/releases) and install it manually.

### Installation within VS Code

<details><summary>Click to show</summary>
<p>

1. Open the VS Code Marketplace, and search and install _OCP CAD Viewer 3.4.0_.

    The Marketplace version is the upstream extension. To use this fork's VS
    Code extension build, install a VSIX built from this repository or from this
    fork's releases if available.

    Afterwards the OCP viewer is available in the VS Code sidebar:

    ![](screenshots/ocp_icon.png)

2. Clicking on it shows the OCP CAD Viewer UI with the viewer manager and the library manager:

    ![](screenshots/init.png)

    You have 3 options:
    - Prepare _OCP CAD Viewer_ for working with [build123d](https://github.com/gumyr/build123d): Press the _Quickstart build123d_ button.

        This will install _OCP_, _build123d_, _ipykernel_ (_jupyter_client_), _ocp_tessellate_ and _ocp_vscode_ via `pip`

        ![](screenshots/build123d_installed.png)

    - Prepare _OCP CAD Viewer_ for working with [CadQuery](https://github.com/cadquery/cadquery): Press the _Quickstart CadQuery_ button.

        This will install _OCP_, _CadQuery_, _ipykernel_ (_jupyter_client_), _ocp_tessellate_ and _ocp_vscode_ via `pip`

        ![](screenshots/cadquery_installed.png)

    - Ignore the quick starts and use the "Library Manager" to install the libraries via `pip` (per default, this can be changed in the VS Code settings). Install the needed library by pressing the down-arrow behind the library name (hover over the library name to see the button) in the "Library Manager" section of the _OCP CAD Viewer_ sidebar. For more details, see [here](./docs/install.md)

    Quickstart will also
    - (optionally) install the the [Jupyter extension for VS Code from Microsoft](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)
    - start the OCP viewer
    - create a demo file in a temporary folder to quickly see a simple usage example

**Notes:**

- Do not use the _OCP CAD Viewer_ logo to verify your _OCP CAD Viewer_ settings! The logo overwrites all your settings in VS Code with its own settings to always look the same on each instance. Use a simple own model for checking your configuration

- If you run into issues, see [Troubleshooting](docs/troubleshooting.md)

</p>
</details>

### Installation via CLI

If you aren't using VS Code, you can install/use this extension via command line

Since this is a python extension, it is recommended to install/activate a virtual environment first, (e.g. uv, venv, poetry, conda, pip, etc)

To use the fork-specific Emacs/standalone command API from a source checkout:

```bash
git clone https://github.com/KarimAziev/vscode-ocp-cad-viewer.git
cd vscode-ocp-cad-viewer

uv venv .venv
uv pip install -e .

corepack yarn install --frozen-lockfile
```

Install your CAD library into the same environment, for example:

```bash
uv pip install cadquery
# or
uv pip install build123d
```

Then start the standalone viewer:

```bash
.venv/bin/python -m ocp_vscode --port 3939
```

The viewer will be available at:

```text
http://127.0.0.1:3939/viewer
```

The `corepack yarn install --frozen-lockfile` step is needed for source
checkouts because the standalone browser viewer uses the `three-cad-viewer`
JavaScript/CSS assets from `node_modules` when release-packaged static assets
are not present.

If you install from PyPI, you get the upstream `ocp-vscode` package unless this
fork has been published separately:

- uv based virtual environments:

    ```
    source .venv/bin/activate  # to activate the uv virtual environment
    uv add ocp-vscode
    ```

- pip for other virtual environments:

    ```
    source .venv/bin/activate  # to activate venv virtual environments
    conda / mamba / micromamba activate <env>  # to activate conda like virtual environments
    pip install ocp-vscode
    ```

Notes:

- The extension is in pypi only [pypi](https://pypi.org/project/ocp-vscode/), so for conda, mamba or micromamba environments `pip` or `uv pip` needs to be used.
- The PyPI package does not necessarily include this fork's Emacs-first command
  API. Use the source checkout above when you need the fork-specific behavior.
- If you want to use the Studio mode with MaterialX support, see [PBR Studio](docs/pbr_studio.md#material-setup)

### Using this fork from another Python project

In a CAD project that already depends on upstream `ocp_vscode` or
`ocp-vscode`, replace that dependency with this fork.

For example, if a `requirements.txt` currently contains:

```text
build123d
bd_warehouse
ocp_vscode>=3.0.0
```

replace the `ocp_vscode` line with the fork:

```text
build123d
bd_warehouse
ocp-vscode @ git+https://github.com/KarimAziev/vscode-ocp-cad-viewer.git
```

Then install it in a regular venv:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For a `uv` project, add the fork directly:

```bash
uv add "ocp-vscode @ git+https://github.com/KarimAziev/vscode-ocp-cad-viewer.git"
```

If you are actively editing this fork locally, use an editable install instead:

```bash
# inside the CAD project
uv add --editable /Users/km/src/vscode-ocp-cad-viewer
```

or with plain pip:

```bash
# inside the CAD project's activated venv
python -m pip uninstall -y ocp-vscode ocp_vscode
python -m pip install -e /Users/km/src/vscode-ocp-cad-viewer
```

For a local editable `requirements.txt`, use:

```text
build123d
bd_warehouse
-e /Users/km/src/vscode-ocp-cad-viewer
```

The Python import remains unchanged:

```python
from ocp_vscode import show, set_port
from ocp_vscode.comms import viewer_command
```

### Installation in code-server

This extension is _not_ available on the [OpenVSX marketplace](https://open-vsx.org/) used by code-server. If you want to use it in [code-server](https://github.com/coder/code-server), you need to install it manually on the server running code-server:

1. Go to the [releases page](https://github.com/bernhard-42/vscode-ocp-cad-viewer/releases)
2. Download the latest `ocp-cad-viewer-<version>.vsix` file, e.g. using `wget <url of vsix file>`
3. Run `code-server --install-extension ocp-cad-viewer-<version>.vsix` to install the extension

## Usage

### Running code with VS Code's "Run" menu

The simplest way to run a Python script with OCP CAD Viewer is via VS Code's built-in **Run** menu:

- Edit the file as usual. Make sure `from ocp_vscode import ...` (or `import ocp_vscode`) is somewhere in the file — this matches the default `OcpCadViewer.advanced.autostartTriggers` and starts the viewer automatically when the file is opened.
- Use **Run > Run Without Debugging** (`Ctrl-F5` / on macOS `⌃F5`) for a plain run, or **Run > Start Debugging** (`F5`) to run under the Python debugger with visual debugging enabled (see [docs/debug.md](docs/debug.md)).
- Each `show(...)` call in your script is sent to the running viewer. If more than one viewer is open, `show` prompts in the terminal to choose which port to send to; call `set_port(<port>)` explicitly to skip the prompt.

### Running code using Jupyter extension

- Start the _OCP CAD Viewer_ by pressing the box-arrow button in the "Viewer Manager" section of the _OCP CAD Viewer_ sidebar (hover over the `ocp_vscode` entry to see the button).
- Import ocp_vscode and the CAD library by using the paste button behind the library names in the "Library Manager" section
- Use the usual Run menu to run the code

![Running code](screenshots/ocp_vscode_run.png)

### Standalone mode

Standalone mode allows you to use OCP CAD Viewer without VS Code: `python -m ocp_vscode`. This starts a Flask server reachable at `http://127.0.0.1:<port>` (default `http://127.0.0.1:3939`). See [docs/standalone.md](docs/standalone.md) for details, including the full CLI reference and how to run it in Docker.

In this fork, standalone mode is also the recommended entry point for Emacs:

```bash
.venv/bin/python -m ocp_vscode --port 3939
```

Open the viewer in a browser or Emacs xwidget:

```text
http://127.0.0.1:3939/viewer
```

Python code can then send CAD objects to the running viewer in the usual way:

```python
import cadquery as cq
from ocp_vscode import set_port, show

set_port(3939)
show(cq.Workplane().box(1, 2, 3))
```

### Emacs layer

Detailed Emacs installation, keybindings, and workflow are documented in the
separate Emacs package:
[KarimAziev/ocp-cad-viewer](https://github.com/KarimAziev/ocp-cad-viewer).

At a high level, start this fork's standalone viewer:

```bash
.venv/bin/python -m ocp_vscode --port 3939
```

Then use the Emacs package to open `http://127.0.0.1:3939/viewer` in an
xwidget and send websocket camera commands directly from Emacs.

### Viewer command API

This fork adds a generic command channel for viewer navigation. Raw websocket
messages use the existing command prefix `C:` followed by JSON:

```text
C:{"type":"viewer_command","command":"view","value":"front"}
```

Supported camera commands include:

```json
{"type":"viewer_command","command":"view","value":"front"}
{"type":"viewer_command","command":"view","value":"top"}
{"type":"viewer_command","command":"view","value":"iso"}
{"type":"viewer_command","command":"reset"}
{"type":"viewer_command","command":"rotate","axis":"x","delta":10}
{"type":"viewer_command","command":"rotate","axis":"z","delta":-10}
{"type":"viewer_command","command":"pan","direction":"left","step":10}
{"type":"viewer_command","command":"pan","direction":"up","step":10}
{"type":"viewer_command","command":"zoom","delta":100}
```

Python clients can use the helper instead of constructing websocket frames:

```python
from ocp_vscode.comms import viewer_command

viewer_command("view", value="front", port=3939)
viewer_command("rotate", axis="x", delta=10, port=3939)
viewer_command("pan", direction="left", step=10, port=3939)
viewer_command("zoom", delta=100, port=3939)
```

`viewer_command(...)` is fire-and-forget: a `{}` return means the websocket
payload was sent, not that the browser acknowledged or applied the command.

### Debugging code with visual debugging

After each step, the debugger checks all variables in `locals()` for being CAD objects and displays them with their variable name. See [docs/debug.md](docs/debug.md) for details.

### Library Manager

The "Library Manager" in the _OCP CAD Viewer_ sidebar lets you install or upgrade _build123d_, _cadquery_, _ipykernel_ and _ocp_tessellate_ from VS Code. See [docs/install.md](docs/install.md) for the default install commands, placeholder substitution, and `uv add` override.

### Extra topics

#### Getting started

- [Quickstart experience on Windows](docs/quickstart.md)
- [Install Libraries](docs/install.md)
- [Best practices](docs/best_practices.md)

#### Working with the viewer

- [Ports and connecting to a viewer](docs/ports.md)
- [Config files (`~/.ocpvscode`, `~/.ocpvscode_standalone`)](docs/config_files.md)
- [Use Jupyter to execute code](docs/run.md)
- [Standalone mode (use without VS Code)](docs/standalone.md)
- [Debug code with visual debugging](docs/debug.md)
- [Measurement tools](docs/measure.md)
- [Object selection tool](docs/selector.md)
- [Physical based rendering Studio](docs/pbr_studio.md)
- [ImageFace — use a 2-D image as a reference plane](docs/image_face.md)

#### Python `show*` commands

- [Use the `show` command](docs/show.md)
- [Use the `show_object` command](docs/show_object.md)
- [Use the `push_object` and `show_objects` command](docs/push_object.md)
- [Use the `show_all` command](docs/show_all.md)
- [Use the `set_viewer_config` command](docs/set_viewer_config.md)

#### Python API reference

- [Additional Python API](docs/api.md) (`save_screenshot`, `status`, `set_port`, …)
- [Animation](docs/animation.md)
- [Color maps](docs/colormaps.md)
- [Enums reference](docs/enums.md) (`Camera`, `Collapse`, `Render`, `AnalysisTool`, `UiTab`, `Studio*`)

#### VS Code reference

- [VS Code Settings reference](docs/settings.md)
- [VS Code Commands reference](docs/commands.md)

#### Examples and snippets

- [Download examples for build123d or cadquery](docs/examples.md)
- [Use the build123d snippets](docs/snippets.md)

#### Other editors support

- [Using OCP CAD Viewer with NeoVim](docs/editors.md)
- [Emacs standalone viewer control](docs/emacs.md)
- [Emacs Lisp control package](https://github.com/KarimAziev/ocp-cad-viewer)

#### Help

- [Troubleshooting](docs/troubleshooting.md)

## Development

This fork has two build surfaces:

- TypeScript for the VS Code extension.
- Python package/runtime files for standalone mode.

For a local source checkout:

```bash
uv venv .venv
uv pip install -e . pytest
corepack yarn install --frozen-lockfile
```

Compile the TypeScript extension code:

```bash
corepack yarn run compile
```

Run the focused standalone/viewer-command tests:

```bash
.venv/bin/python -m pytest \
  tests/test_standalone_static.py \
  tests/test_viewer_command.py \
  tests/test_standalone_cli.py \
  -q
```

The upstream Makefile still provides the broader test target:

```bash
make tests
```

For release packaging, `make dist` copies `three-cad-viewer` assets into
`ocp_vscode/static` and builds Python/VSIX artifacts. For local standalone
development, this fork can also serve those assets directly from
`node_modules/three-cad-viewer/dist` after `yarn install`.

## Changes

## v3.4.0

**Features**

- Detect in `show` and in the extension when backend is not running and show a Python warning and a VS Code error message
- Keep the last active tab active, so iterating over a feature in clipping or studio is easier
- Reuse the viewer component across show commands (clear instead of restart), allowing to keep active tab smoothly
- Properties tool now also shows diameter of circle and ellipse [three-cad-viewer #39](https://github.com/bernhard-42/three-cad-viewer/issues/39)
- The `analysis_tool` parameter allows to activate a specific analysis tool (`AnalysisTool.PROPERTIES`, `AnalysisTool.DISTANCE`, `AnalysisTool.SELECT`). It is consistently available with all `show` commands and `set_viewer_config`. [#219](https://github.com/bernhard-42/vscode-ocp-cad-viewer/issues/219)
- The `tab` parameter allows to activate a specific UI tab (`UiTab.TREE`, `UiTab.CLIP`, `UiTab.ZEBRA`, `UiTab.Material`, `UiTab.STUDIO`). It is consistently available with all `show` commands and `set_viewer_config`.
- `ShapeList`s are now expanded like normal lists to not hide the internal structure [#220](https://github.com/bernhard-42/vscode-ocp-cad-viewer/issues/220)
- Adapt material support to latest changes in build123d
- Rework and significant enhancement of the docs

**Fixes**

- Clean up backend shutdown on closing VS Code window or on quitting VS Code (cmd-Q/ctrl-Q) [three-cad-viewer #40](https://github.com/bernhard-42/three-cad-viewer/issues/40)
- Edge, vertices and faces show color indicator in the navigation tree again [three-cad-viewer #41](https://github.com/bernhard-42/three-cad-viewer/issues/41)
- Error message explains to drop --backend as a parameter when added accidentally to the standalone startup command [#221](https://github.com/bernhard-42/vscode-ocp-cad-viewer/issues/221)
- Lists and dicts of assemblies do not omit the label of the assembly when it has only one child [#224](https://github.com/bernhard-42/vscode-ocp-cad-viewer/issues/224)
- The parameter `modes` of `show*` is now properly threaded through ocp-tessellate so that skipping non-CAD objects is properly handled [#226](https://github.com/bernhard-42/vscode-ocp-cad-viewer/issues/226)
- Fixed race condition that could lead to a wrong dialog about missing ocp_vscode package in the current Python environment
- Document `ImageFace` handling [#223](https://github.com/bernhard-42/vscode-ocp-cad-viewer/issues/223)

For the change history see [CHANGELOG](./CHANGELOG.md)
