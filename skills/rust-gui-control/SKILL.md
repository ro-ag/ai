---
name: rust-gui-control
description: Use when remote-controlling, driving, testing, or screen-capturing a Rust GUI app on macOS with computer-use or app-control tools — especially when a cargo-built binary draws a window but the controller cannot target it ("Invalid app", missing from app inventory), when pointer/hover actions miss, or when exact-pixel window captures are needed for visual verification.
---

# Remote-controlling Rust GUI apps on macOS

App-control tools can target a Rust GUI only when macOS sees it as an application. A bare `cargo run` / `target/debug/` binary draws a window but has no registered `.app` identity and is absent from the controller's app inventory.

Workflow: build debug binary → wrap that exact binary in a temporary `.app` with stable bundle id → target the `.app` by absolute path → drive keyboard/pointer/menus via app control → use exact-window PNG capture when color/alpha fidelity matters.

## macOS permissions

The agent's host process (Terminal, Ghostty, VS Code, Codex, …) needs both:

- System Settings → Privacy & Security → Screen Recording
- System Settings → Privacy & Security → Input Monitoring

Fully quit and restart the host app after granting either — macOS silently drops input events until restart. Verify injection before debugging the Rust app:

```sh
uv run --with pyobjc-framework-Quartz python -c "
import Quartz, time
def pos():
    point = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    return (point.x, point.y)
print('before', pos())
event = Quartz.CGEventCreateMouseEvent(
    None, Quartz.kCGEventMouseMoved, (1190, 490), Quartz.kCGMouseButtonLeft)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
time.sleep(0.5)
print('after ', pos())
"
```

If `before` equals `after`, stop — fix permissions and restart the host first.

## Preferred: the project's packager

If the project has a packaging script that accepts a debug binary, use it — it preserves the product's executable name, bundle id, and plist:

```sh
cargo build -p my-app
python3 tools/package.py --os macos --binary target/debug/my-app --out /tmp/my-app-bundle --version debug
```

Packaging only copies the binary; you are still testing `target/debug/my-app`. Target the absolute `.app` path first (`ctl` = your controller's client object):

```js
var state = await ctl.get_app_state({ app: "/tmp/my-app-bundle/MyApp.app", disableDiff: true });
console.log(state.text);
```

App name or bundle id may work after Launch Services has seen the bundle, but the absolute path is the least ambiguous first target.

## Minimum bundle shape (no packager)

```text
MyApp.app/
└── Contents/
    ├── Info.plist
    └── MacOS/
        └── my-app
```

`Info.plist` minimum:

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

Requirements: `CFBundleExecutable` exactly matches the file in `Contents/MacOS/`; executable bit set; bundle id stable and unique; temporary bundles live under a task-specific dir in `/tmp`, never in the repo or release output.

Build it for a binary at `target/debug/my-app`:

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

Code signing is not required to remote-control a locally built debug bundle. Signing, entitlements, notarization, and release packaging are separate workflows needing their normal authorization.

## Control workflow

Start every session by reading fresh app state; re-read after every action before choosing the next one:

```js
var state = await ctl.get_app_state({ app: appPath, disableDiff: true });
console.log(state.text);
await ctl.press_key({ app: appPath, key: "super+alt+v" });
state = await ctl.get_app_state({ app: appPath });
```

- Prefer accessibility element actions over coordinates when elements are exposed; re-derive element indexes from each new state — they go stale on any UI change.
- Prefer app-targeted key presses over global keyboard injection.
- Treat remote click coordinates as relative to the controller's current app screenshot unless the controller documents another space; capture a fresh full screenshot before coordinate actions.
- Raw custom-rendered surfaces often expose only window + menu bar via accessibility. Coordinate input is expected there — verify success through observable app state (cursor offset, inspector value, selected row) or a follow-up screenshot.

### Hover-only verification

If the control API lacks pointer movement, in preference order:

1. Use a remote pointer-move/hover action if available.
2. Use a debug-only forced-hover hook if the app provides one (e.g. `MYAPP_FORCE_HOVER=0x52`).
3. Raise the bundled app, then inject a Quartz `kCGEventMouseMoved` event.
4. Click a harmless target only if changing selection/cursor state is acceptable; restore state afterward.

Never claim hover-follows-pointer from a forced-hover screenshot — use at least two real pointer positions or another event-driven check.

## Capture workflow

Remote app screenshots are for UI state, accessibility output, and locating controls. They may be JPEG-compressed or diff/mask images — not evidence for subtle alpha, gradients, 1px seams, or exact colors.

For visual-quality verification:

1. List windows; record the exact `CGWindowID` and bounds.
2. Capture that window by ID as PNG; reuse the known ID for later captures.
3. Capture only the app window, never the full display.

```sh
# list the app's windows, note the CGWindowID
uv run --with pyobjc-framework-Quartz python -c "
import Quartz
for w in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID):
    if w.get('kCGWindowOwnerName') == 'MyApp':
        print(w['kCGWindowNumber'], w.get('kCGWindowBounds'))
"

screencapture -l WINDOW_ID -o /tmp/my-app-window.png
```

If `screencapture -l` fails with "could not create image from window", fall back to `CGWindowListCreateImage` + `CGImageDestination`. On macOS 15 the SDK marks that API unavailable to direct Swift calls though the runtime symbol exists — bind it dynamically or use a tested project helper.

## Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `Invalid app` for a visible Rust window | Bare executable, no bundle → wrap in `.app`, target absolute bundle path. |
| Controllable but pointer actions miss | Stale state, or wrong coordinate space → refresh state + screenshot; verify whether coordinates are screenshot-relative or global; test on a harmless target. Apply title-bar/shadow/Retina transforms only to global coordinates, never to screenshot-relative ones. |
| Global pointer moves but hover doesn't update | App not frontmost, or no enter/move events → raise app, move from outside the surface inward, wait ≥0.5 s, confirm the point is over real content (custom viewers may paint no hover over EOF/empty space). |
| Screenshot black except changed regions | Controller returned a diff/mask → re-request state with `disableDiff: true`; if still a mask, use the exact-window PNG path. |
| AppleScript can't activate the app | Bare binaries aren't reliably AppleScript-addressable → bundle first; prefer app-targeted actions. |
| App hangs on first keychain/credential access | Not a control problem — see `memento show macos-dev-keychain-prompt-loop` and `macos-login-keychain-auth-failed` (unsigned-binary ACL loops, `errSecAuthFailed`, first-access signature-eval delay). |

## Session cleanup

- Restore any appearance, view mode, wrapping, width, or selection state changed during verification.
- Terminate the temporary app; leave temporary bundles in `/tmp`, never commit them.
- Do not turn debug packaging into a release, signing, tagging, or publishing action.
