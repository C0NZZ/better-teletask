# WXT Port Notes

Port of the Better Tele-Task vanilla WebExtension to the [WXT](https://wxt.dev) framework.
Keeps all prior functionality, produces builds for Chrome MV3, Firefox MV2, and Firefox MV3 from a single source.

## Why WXT

- **One manifest source, multiple targets.** Write in MV3 format; WXT converts to MV2 where needed (host_permissions → permissions, `action` → `browser_action`, `web_accessible_resources` object-form → string array).
- **Unified `browser` global.** Replaces the vendored `browser-polyfill.min.js` — WXT picks `browser` or `chrome` at runtime.
- **Auto-imports.** `defineContentScript`, `browser`, `defineConfig` are available without explicit imports inside entrypoints.
- **Vite bundling.** Static `import` works in content scripts, so we no longer need the `import(browser.runtime.getURL('tweaks.js'))` dynamic-import trick.
- **Public assets + WAR generation.** Files in `public/` are copied verbatim; we just declare `fonts/*` once as a web-accessible resource.

## Final Layout

```
.
├── wxt.config.ts              # single source of manifest truth
├── package.json               # wxt dep + per-target build scripts
├── entrypoints/
│   ├── main.content.js        # tweaks content script (video-player hooks)
│   ├── subtitles.content.js   # subtitle-injection content script
│   └── popup/
│       ├── index.html
│       ├── main.js
│       └── style.css
├── utils/
│   └── tweaks.js              # tweak functions, imported by main.content.js
└── public/
    ├── fonts/                 # .woff2 files + fonts.css
    └── icons/                 # 32/48/64 png
```

## File-by-file Changes

| Before | After | Why |
|---|---|---|
| `manifest.json` | `wxt.config.ts` | WXT generates manifest per target (`chrome-mv3`, `firefox-mv2`, `firefox-mv3`). Written in MV3 form. |
| `main.js` | `entrypoints/main.content.js` | Wrapped IIFE in `defineContentScript({ matches, main })`. `matches` moved from manifest into the entrypoint. |
| `tweaks.js` (loaded via `runtime.getURL` dynamic import) | `utils/tweaks.js` (static `import`) | WXT/Vite bundles both files together, so runtime URL juggling is unnecessary. |
| `subtitles.js` | `entrypoints/subtitles.content.js` | Same as main: wrapped in `defineContentScript`. Otherwise logic-identical (fixed an implicit-global `text`/`message` to `let`). |
| `browser-polyfill.min.js` | removed | WXT's unified `browser` replaces it. |
| `popup/index.html` | `entrypoints/popup/index.html` | Removed `<script src="browser-polyfill.min.js">`. Changed asset paths to absolute `/fonts/...`, `/icons/...` (public-asset convention). Added `<title>` for MV3 action title. |
| `popup/popup.js` | `entrypoints/popup/main.js` | Imports `./style.css` (Vite bundles it) and `browser` from `wxt/browser`. Logic unchanged. |
| `popup/style.css` | `entrypoints/popup/style.css` | Unchanged — now a Vite-imported asset. |
| `fonts/` | `public/fonts/` | `public/` is copied unmodified; referenced from code via `/fonts/...` or `browser.runtime.getURL('/fonts/fonts.css')`. |
| `icons/` | `public/icons/` | Same rationale. |

### Non-obvious code change: `runtime.getURL` path

Original:
```js
link.href = browser.runtime.getURL('fonts/fonts.css');
```
WXT requires the leading slash for public assets:
```js
link.href = browser.runtime.getURL('/fonts/fonts.css');
```

### Non-obvious code change: dynamic → static import

Original (content script couldn't use ESM imports directly, so it runtime-loaded a module URL):
```js
const { removeResizeLimit, ... } = await import(browser.runtime.getURL('tweaks.js'));
```
WXT (bundled):
```js
import { removeResizeLimit, ... } from '../utils/tweaks.js';
```

## How `wxt.config.ts` Maps to Each Target

Authored once in MV3 shape:
```ts
manifest: {
  permissions: ['activeTab', 'storage'],
  host_permissions: ['https://btt.makeruniverse.de/*'],
  action: { default_icon: 'icons/32.png', default_title: 'Better Tele-Task' },
  web_accessible_resources: [
    { resources: ['fonts/*'], matches: ['https://www.tele-task.de/*'] },
  ],
  browser_specific_settings: {
    gecko: { id: '{…}', strict_min_version: '140.0',
             data_collection_permissions: { required: ['authenticationInfo'] } },
    gecko_android: { strict_min_version: '142.0' },
  },
}
```

WXT-produced output differences:

| Field | MV3 output | MV2 output |
|---|---|---|
| `manifest_version` | `3` | `2` |
| host permissions | `host_permissions: [...]` | merged into `permissions: [...]` |
| toolbar icon | `action: {...}` | `browser_action: {...}` |
| WAR | `[{ resources, matches }]` | `["fonts/*"]` |
| content scripts | generated from `entrypoints/*.content.js` | same |

Content-script `matches` come from the `defineContentScript` call, so both scripts automatically get the same `https://www.tele-task.de/lecture/video/*` match and are merged into one `content_scripts` entry.

## WXT Concepts Used Here

- **`entrypoints/`** — every file/folder here becomes a bundle target. Naming rules used:
  - `*.content.js` → content script
  - `popup/index.html` → popup page
- **`defineContentScript({ matches, main })`** — `main(ctx)` runs in the page. Top-level code in these files runs at build time (Node), not in the browser — all runtime code lives inside `main`.
- **`public/`** — static pass-through. Reference with absolute paths (`/icons/32.png`). In content scripts you additionally need `browser.runtime.getURL('/...')` **and** a WAR entry.
- **`browser` auto-import** — available in every entrypoint without `import`. In the popup JS it is imported explicitly (`import { browser } from 'wxt/browser'`) because auto-imports work differently for plain `.js` bundled via Vite-HTML entries, and the explicit import is always safe.
- **`wxt prepare`** — generates `.wxt/` with TS types and virtual module shims. Run automatically via the `postinstall` script.

## Build & Run

```bash
npm install            # also runs `wxt prepare`

# Chrome / Chromium (MV3, the default)
npm run dev            # launch browser + HMR
npm run build          # produces .output/chrome-mv3/
npm run zip            # produces a chrome-mv3 .zip

# Firefox MV2 (matches the pre-port manifest)
npm run dev:firefox
npm run build:firefox  # → .output/firefox-mv2/
npm run zip:firefox

# Firefox MV3
npm run dev:firefox-mv3
npm run build:firefox-mv3  # → .output/firefox-mv3/
npm run zip:firefox-mv3
```

Load unpacked: point the browser at the matching `.output/<target>/` folder.

## CORS and the Background Script

`fetch()` inside a content script is treated by the browser as coming from the **host page's origin** (`www.tele-task.de`). `btt.makeruniverse.de` doesn't send `Access-Control-Allow-Origin`, so the browser blocks it with a CORS error.

Background scripts (service workers in MV3, background pages in MV2) fetch from the **extension origin**, which the browser exempts from CORS when `host_permissions` covers the URL. The fix:

1. `entrypoints/background.js` — listens for `{ type: 'FETCH_SUBTITLE', url, apiKey }` messages, performs the fetch, returns `{ ok, text }` or `{ ok, error }`.
2. `entrypoints/subtitles.content.js` — replaces the direct `fetch()` call with `browser.runtime.sendMessage(...)`.

The listener returns `true` from `onMessage` to keep the response channel open for the async fetch result (required by the WebExtension spec).

## Notes / Gotchas

- `data_collection_permissions` is a recent Firefox addition; kept under `browser_specific_settings.gecko` and ignored by Chrome.
- The MV2 Firefox target still works because Firefox hasn't forced MV3. The MV3 Firefox target is included for future-proofing, but Firefox MV3 still loads content scripts similarly (no service worker here since we have no background script).
- No background script exists — all logic is in content scripts or the popup — so nothing to port to a service worker.
- The script-injection trick in `removeResizeLimit` (appending an inline `<script>` with `textContent`) still works and reaches the page's main world. WXT also offers `injectScript` if that pattern needs to become more structured later.
