# Remote-controlling Rust GUI apps on macOS

Native app-control tools can reliably target a Rust GUI only when macOS sees the
process as an application. A binary launched directly with `cargo run` or from
`target/debug/` may draw a normal window, but it has no registered `.app`
identity and can be absent from the controller's app inventory.

The reliable workflow is:

1. Build the debug binary.
2. Wrap that exact binary in a temporary `.app` with an `Info.plist` and stable
   bundle identifier.
3. Target the `.app` by absolute path through the native app-control tool.
4. Use app control for keyboard, pointer, menus, and accessibility state.
5. Use exact-window PNG capture when color or translucent-layer fidelity
   matters.

## macOS permissions

The process hosting the agent—Terminal, Ghostty, VS Code, Codex, or another
desktop app—needs both:

- System Settings → Privacy & Security → Screen Recording
- System Settings → Privacy & Security → Input Monitoring

Fully quit and restart the host app after granting either permission. macOS may
silently drop input events until it is restarted.

Verify input injection before debugging the Rust app:

```sh
uv run --with pyobjc-framework-Quartz python -c "
import Quartz, time
def pos():
    point = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    return (point.x, point.y)
print('before', pos())
event = Quartz.CGEventCreateMouseEvent(
    None,
    Quartz.kCGEventMouseMoved,
    (1190, 490),
    Quartz.kCGMouseButtonLeft,
)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
time.sleep(0.5)
print('after ', pos())
"
```

If `before` equals `after`, stop. Fix permissions and restart the host before
trying app automation.

## Preferred: use the project's packager

Reuse an existing packaging script when one can accept a debug binary. This
preserves the product's executable name, bundle identifier, and plist.

Typical shape:

```sh
cargo build -p my-app
python3 tools/package.py \
  --os macos \
  --binary target/debug/my-app \
  --out /tmp/my-app-bundle \
  --version debug
```

This still tests `target/debug/my-app`; packaging only copies that binary into
an application bundle.

Target the absolute `.app` path first. For example, with a native computer-use
API:

```js
var state = await sky.get_app_state({
  app: "/tmp/my-app-bundle/MyApp.app",
  disableDiff: true,
});
nodeRepl.write(state.text);
```

An app name or bundle identifier may work after Launch Services has seen the
bundle, but the absolute path is the least ambiguous first target.

## Minimum application-bundle shape

If a project has no packager, create a temporary local bundle with this shape:

```text
MyApp.app/
└── Contents/
    ├── Info.plist
    └── MacOS/
        └── my-app
```

`Info.plist` needs at least:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>my-app</string>
  <key>CFBundleIdentifier</key>
  <string>dev.example.my-app.debug</string>
  <key>CFBundleName</key>
  <string>MyApp</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
</dict>
</plist>
```

Requirements:

- `CFBundleExecutable` exactly matches the file under `Contents/MacOS/`.
- The executable bit is set.
- `CFBundleIdentifier` is stable and unique.
- Build locally; do not download or run an untrusted bundle.
- Put temporary bundles under a task-specific directory in `/tmp`, not in the
  repo or a release output directory.

Example for a binary at `target/debug/my-app`:

```sh
RUST_GUI_BUNDLE_ROOT="$(mktemp -d /tmp/rust-gui-control.XXXXXX)"
RUST_GUI_APP="$RUST_GUI_BUNDLE_ROOT/MyApp.app"
RUST_GUI_CONTENTS="$RUST_GUI_APP/Contents"

mkdir -p "$RUST_GUI_CONTENTS/MacOS"
cp target/debug/my-app "$RUST_GUI_CONTENTS/MacOS/my-app"
chmod +x "$RUST_GUI_CONTENTS/MacOS/my-app"

plutil -create xml1 "$RUST_GUI_CONTENTS/Info.plist"
/usr/libexec/PlistBuddy \
  -c "Add :CFBundleExecutable string my-app" \
  -c "Add :CFBundleIdentifier string dev.example.my-app.debug" \
  -c "Add :CFBundleName string MyApp" \
  -c "Add :CFBundlePackageType string APPL" \
  "$RUST_GUI_CONTENTS/Info.plist"

echo "$RUST_GUI_APP"
```

Code signing is not required merely to remote-control a locally built debug
bundle. Signing, entitlements, notarization, release packaging, and publishing
are separate workflows and require their normal authorization.

## Control workflow

Start every control session by reading fresh app state:

```js
var state = await sky.get_app_state({ app: appPath, disableDiff: true });
nodeRepl.write(state.text);
```

Then:

- Prefer accessibility element actions over coordinates when elements are
  exposed.
- Use app-targeted key presses instead of global keyboard injection.
- After every action, fetch state again before choosing the next action.
- Re-derive accessibility element indexes from the new state; indexes can
  become stale after any UI change.
- Treat remote click coordinates as coordinates in the controller's current
  app screenshot unless that controller explicitly documents another space.
- Use a freshly captured full screenshot before coordinate actions.

Example:

```js
await sky.press_key({ app: appPath, key: "super+alt+v" });
state = await sky.get_app_state({ app: appPath });
nodeRepl.write(state.text);
```

Raw custom-rendered surfaces often expose only the window and menu bar through
accessibility. Coordinate input is expected for those surfaces; verify success
through observable app state such as a cursor offset, inspector value, selected
row, or a follow-up screenshot.

### Hover-only verification

Some app-control APIs expose click and drag but not pointer movement. Options,
in preference order:

1. Use a remote pointer-move or hover action when available.
2. Use a debug-only forced-hover hook when the app provides one (e.g. an
   env var like `MYAPP_FORCE_HOVER=0x52`).
3. Raise the bundled app, then inject a Quartz `kCGEventMouseMoved` event.
4. Click a harmless target only when changing selection/cursor state is
   acceptable, and restore that state afterward.

Do not claim hover follows the pointer based only on a forced-hover screenshot.
Use at least two real pointer positions or another observable event-driven
check.

## Capture workflow

Remote app screenshots are best for:

- understanding current UI state;
- reading accessibility output;
- locating controls for the next action;
- quick visual checks.

They may be JPEG-compressed or diff/mask images. Do not use them as the only
evidence for subtle alpha, gradients, one-pixel seams, or exact color hierarchy.

For visual-quality verification:

1. List windows and record the exact `CGWindowID` and bounds.
2. Capture that window by ID as PNG.
3. Reuse the known ID for later captures instead of relisting a background
   window.
4. Capture only the app window, not a full display.

Use the project's capture helper when it has one; otherwise `screencapture -l`
against the recorded window ID:

```sh
# list windows for the app, note the CGWindowID
uv run --with pyobjc-framework-Quartz python -c "
import Quartz
for w in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID):
    if w.get('kCGWindowOwnerName') == 'MyApp':
        print(w['kCGWindowNumber'], w.get('kCGWindowBounds'))
"

screencapture -l WINDOW_ID -o /tmp/my-app-window.png
```

If `screencapture -l` fails with “could not create image from window,” fall back
to `CGWindowListCreateImage` for that exact window and write it with
`CGImageDestination`. On macOS 15 the SDK marks the API unavailable to direct
Swift calls even though the runtime symbol remains present; bind the symbol
dynamically or use a tested project helper.

## Troubleshooting

### `Invalid app` for a visible Rust window

The process is probably a bare executable. Confirm that the controller's app
inventory has no entry, then wrap the debug binary in `.app` form and target the
absolute bundle path.

### App is controllable but pointer actions miss

- Refresh full app state and screenshot.
- Confirm whether coordinates are app-screenshot-relative or global.
- Use an obvious harmless target and verify through app state.
- Account for title bars, window shadows, display origins, and Retina scaling
  only when using global/native coordinates; do not apply those transforms to
  screenshot-relative coordinates.

### Global pointer moves but hover does not update

- Ensure the app is frontmost or raised.
- Move from outside the target surface to inside it so the app receives enter
  and move events.
- Wait at least 0.5 seconds before capture.
- Confirm the point lies over real content; custom viewers may intentionally
  paint no hover over EOF or empty space.

### Remote screenshot is black except for changed regions

The controller returned a diff or mask image. Request fresh state with diffing
disabled, then capture again. If the controller still returns a mask, use the
exact-window PNG path.

### AppleScript cannot activate the app

Bare binaries are not reliably AppleScript-addressable. Bundle first. Prefer
app-targeted control actions over scripting activation by process name.

## Session cleanup

- Restore any appearance, view mode, wrapping, width, or selection state changed
  during verification.
- Terminate the temporary app after the checks.
- Leave temporary bundles under `/tmp`; do not commit them.
- Do not turn debug packaging into a release, signing, tagging, or publishing
  action.
