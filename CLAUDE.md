# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A single wedding/Roka invitation microsite for Arjita & Archit (celebration: 18 July 2026), built as a **Design Component** (`.dc.html`) — a custom HTML dialect rendered client-side by a bundled React runtime, not a normal static site or a framework project. There is no package manager, build step, linter, or test suite in this repo — it's plain files served as-is.

## Running the project

The runtime does `fetch()` calls against its own origin (to re-fetch its own source, and to read the `<image-slot>` sidecar file), so **it must be served over HTTP — opening the `.dc.html` file directly via `file://` will not work.**

```bash
python3 admin_server.py 8848
# then open http://localhost:8848/RokaInvite.dc.html
```

`admin_server.py` is a local-only convenience server (drop-in replacement for `python3 -m http.server`) — it serves the site exactly the same, plus a `/admin` upload panel for swapping photo-slot images and the background-music file without hand-editing `.image-slots.state.json`/the `Audio()` call. Not part of the deployed site. Photo uploads there are resized/oriented/encoded the same way as `image-slot.js`'s own drop handler (see below). Requires `Pillow` (`pip install Pillow`) — falling back to plain `python3 -m http.server` still works for just viewing the site, but `/admin` won't exist.

React/ReactDOM are loaded from `unpkg.com` at runtime (see `REACT_URL`/`REACT_DOM_URL` in `support.js`), so the browser needs internet access even though nothing is bundled locally.

There's no lint or test command — verify changes by loading the page in a browser and checking the console for `[dc-runtime]` errors/warnings.

## Emergency rollback (restore the live site in one command)

The live site (`https://arjita-archit.vercel.app/`) auto-redeploys from `git push` to `main`. If a change you pushed misbehaves on a real phone (the photo section is the usual suspect), restore the last-known-good version with:

```bash
./rollback.sh            # restore the commit tagged 'stable' and push it live
./rollback.sh <ref>      # or restore any specific commit/tag, e.g. ./rollback.sh 5cbcbc6
```

`rollback.sh` makes a **new** commit that restores `RokaInvite.dc.html` from the `stable` tag and pushes — it never rewrites history, so it's safe to run anytime. Vercel redeploys the restored version in ~30s.

The **`stable`** tag marks the mobile-safe baseline (currently the pure-CSS scrapbook reveal at commit `5cbcbc6` — no scroll-coupled JS, so the photo section can't freeze). **After you confirm a newer version works on a real phone**, move the tag forward so future rollbacks return to it:

```bash
git tag -f -a stable -m "new known-good" HEAD   # re-point 'stable' at the current commit
git push -f origin stable                        # publish the moved tag
```

**Cache gotcha**: the sidecar `.image-slots.state.json` has no `Cache-Control` header under a plain static server, so browsers apply heuristic caching — a normal reload (even one that feels like a hard refresh) can serve a stale copy for several minutes right after editing it. `image-slot.js`'s fetch now uses `{ cache: 'no-store' }` to prevent this, but keep it in mind if you ever bypass that fetch (e.g. testing via curl) and the browser doesn't reflect a change you're sure landed on disk.

## Architecture

### The `.dc.html` format and its runtime

Each `*.dc.html` file contains:
- An `<x-dc>...</x-dc>` block: the template, written in plain-ish HTML with a small directive language (see below).
- A `<script type="text/x-dc" data-dc-script">` block defining `class Component extends DCLogic { ... }` — the page's logic/state, in the style of a React class component (`state`, `setState()`, `componentDidMount()`/`componentWillUnmount()`, and a `renderVals()` method that returns the flat values object the template interpolates against).

`support.js` is the runtime that parses and mounts this (`dc-runtime`). **It is a generated/vendored bundle — the header says "GENERATED from dc-runtime/src/*.ts — do not edit. Rebuild with `cd dc-runtime && bun run build`."** That source tree isn't present in this repo, so treat `support.js` as read-only; runtime behavior changes belong in the `.dc.html` files or `image-slot.js` instead.

Template directive syntax used throughout the `.dc.html` files:
- `{{ expr }}` — interpolation, resolved against the values returned by `renderVals()`. Supports dotted/bracket paths, `===`/`!==`/`==`/`!=`, `!`, literals — not a full JS expression evaluator.
- `<sc-if value="{{ cond }}" hint-placeholder-val="{{ ... }}">...</sc-if>` — conditional render.
- `<sc-for list="{{ arr }}" as="item">...</sc-for>` — list render (not currently used in this project, but supported by the runtime).
- `<x-import component-from-global-scope="name" from="./file.js">` — loads a plain script/custom-element module and mounts a global (used to pull in `image-slot.js`).
- camelCase inline `style="width:100px;height:100px"` attributes are supported directly (the runtime's encode step auto-converts camelCase attrs).

### Files in this repo

- **`RokaInvite.dc.html`** — the live invitation page. Flow: full-screen monogram particle-reveal overlay (canvas, tap to burst open) → scratch-to-reveal "Save the Date" card (canvas scratch mask, reveals at ~42% cleared) → countdown timer (hardcoded target: `new Date('2026-07-18T20:00:00+05:30')` in `_computeRemaining()`) → story blurb → scroll-driven photo collage (6 `<image-slot>` cards, see below) → celebration/venue blurbs → footer. All logic lives in one `Component` class handling canvas animation loops (`monoLoop`, sparkle background, confetti), scroll listeners, and the countdown interval.
- **`ScratchReveal.dc.html`** — a standalone earlier prototype of just the scratch-card interaction, decoupled from the main invite. Not linked from `RokaInvite.dc.html`; a historical/reference artifact.
- **`Curtain Reveal Options.dc.html`** — a side-by-side gallery of alternative reveal-animation concepts (wax-seal monogram, sparkle monogram, etc.) built to compare against the invite's palette. Design exploration, not part of the shipped page.
- **`_ds/teatro-ui-.../`** — a bound "Teatro UI" component library (React + Tailwind, shadcn-style HSL tokens; ships `CurtainReveal`, `ScratchToReveal`, `Countdown`, `RsvpCard`, etc. — see its own `README.md`). **This is available but not what `RokaInvite.dc.html` currently uses** — the shipped invite is hand-rolled with inline styles and vanilla canvas/JS, not these components. Don't assume the two are wired together.

### Photo slots and the image sidecar

`image-slot.js` defines a `<image-slot>` custom element for drag-and-drop image placeholders, used for the 6 photo-collage cards (`photo-main`, `photo-1`..`photo-5` in `RokaInvite.dc.html`).

- Dropped images are downscaled through a canvas (`toDataUrl()`), capped at `MAX_DIM` (1200px long side) and encoded as WebP at quality 0.85, then stored as a data URL in **`.image-slots.state.json`** (a flat `{ id: { u, s, x, y } }` map — `u` = data URL, `s/x/y` = zoom/pan crop state for the "reframe" pan/zoom feature).
- Persistence to disk only happens via `window.omelette.writeFile`, a host bridge that **does not exist when the page is served by a plain static server** (e.g. `python3 -m http.server`). Drops still render for the current browser session (in-memory), but won't survive a reload unless the real hosting environment (wherever `window.omelette` is injected) is present.
- The capture resolution is tied to `this.clientWidth` (the slot's on-screen size) at the moment of drop — a floor of 480px was added in `_ingest()` so a drop while the slot renders small (e.g. a narrow viewport) doesn't lock in a permanently blurry image, since the original file is discarded after ingest.
- To update slot images programmatically (bypassing the browser), write directly into `.image-slots.state.json` with base64-encoded WebP data URLs.

**Orientation gotcha**: when re-encoding source photos outside the browser, don't trust `sips` + `cwebp` blindly. `sips` can preserve a JPEG's EXIF orientation tag as metadata without physically rotating the pixels (seen with orientation value `4`, a vertical flip); `cwebp` does not read/apply that metadata, so the resulting WebP silently bakes in the wrong (e.g. upside-down) orientation even though a `sips`-generated preview looks correct. Use Python's `PIL.ImageOps.exif_transpose()` (or equivalent) to bake the correction into actual pixels *before* encoding, and verify by decoding the final `.webp` with `dwebp` and viewing that output directly — not the intermediate PNG.

- **`uploads/`** — static assets referenced directly via `<img src="./uploads/...">` (the monogram logo). Separate from `rokapics/`, which holds the couple's source photos used to populate the `.image-slots.state.json` sidecar (not referenced directly by any HTML `src`).
