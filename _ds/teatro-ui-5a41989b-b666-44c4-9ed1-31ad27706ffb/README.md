# Teatro UI — building with this design system

Teatro UI is a theatrical, Tuscan-elegant invitation kit (sage · cream · gold). It is **React + Tailwind CSS with shadcn-style HSL design tokens**. Compose screens from the shipped components and style your own layout glue with the token-backed Tailwind utilities below.

## Setup — no provider needed

Import the stylesheet once at the app root, then import components by name:

```jsx
import "@teatro/ui/styles.css";
import { CurtainReveal, Countdown, RsvpCard, ThankYou } from "@teatro/ui";
```

- The design tokens live on `:root` in the shipped stylesheet — there is **no ThemeProvider to wrap**. Components are styled the moment `styles.css` is present.
- Dark theme: add `class="dark"` to an ancestor (the `.dark` token block is included).
- Page surface: put `bg-background text-foreground font-body` on your root element so the page picks up the ivory ground, sage ink, and Lora body font.
- Entrance animations: blocks reveal on scroll. To render them statically (snapshots), wrap in the exported `<MotionConfig reducedMotion="always">`.

## The styling idiom — token-backed Tailwind utilities

Style with these utilities (each backed by a `--token`). For any value not covered, read the token directly: `style={{ color: "hsl(var(--olive))" }}`. **Do not invent color hexes** — every brand color is a token.

| Concern | Utilities (real, shipped) |
|---|---|
| Surfaces | `bg-background` (ivory) · `bg-card` / `bg-cream` · `bg-paper` |
| Text | `text-foreground` (sage ink) · `text-muted-foreground` · `text-primary` / `text-sage` / `text-sage-dark` · `text-gold` · `text-countdown` |
| Brand fills | `bg-primary text-primary-foreground` (sage CTA) · `bg-gold text-sage-dark` (gold) |
| Borders/ring | `border-border` · `border-input` · `border-sage` · `ring-gold` |
| Fonts | `font-display` (Cormorant Garamond) · `font-body` (Lora) · `font-script` (Great Vibes, cursive) |
| Elevation | `shadow-soft` · `shadow-elegant` · `shadow-lifted` (all sage-tinted) |
| Radius | `rounded-md` · `rounded-lg` · `rounded-xl` |
| Signature | `text-gradient-gold` (sage→olive→gold heading gradient) · `tracking-eyebrow` (uppercase label spacing) · `animate-shimmer` · `animate-shine-sweep` |

Other brand tones (`--olive`, `--terracotta`, `--gold-soft`, `--sage-light`) ship as **tokens**, not pre-built utilities — reach them inline: `style={{ color: "hsl(var(--olive))" }}`. `cn(...)` is exported (the shadcn `clsx` + `tailwind-merge` helper) for conditional classes.

## Where the truth lives

- **Tokens & styles:** the bound `styles.css` imports `_ds_bundle.css`, which holds the full `:root` token set (every `--token`) plus the compiled utility classes and fonts. Read it before styling.
- **Per component:** its `<Name>.d.ts` (the exact `<Name>Props` contract) and `<Name>.prompt.md` (usage). Prefer composing the real components over re-implementing their markup.

## Components

**Atoms:** `Button` (variants `sage|gold|outline|ghost|link`, sizes, `shine`), `Card`/`CardBody`, `Input`, `Textarea`, `Field`, `RadioChoice`, `Stepper`, `Divider`, `Eyebrow`, `SectionHeading`, `Badge`.

**Blocks (full invitation sections, prop-driven):** `CurtainReveal`, `ScratchToReveal`, `Countdown`, `StorySection`, `VenueSection`, `MenuSection`, `DressCode`, `GiftsRegistry`, `Transportation`, `RsvpCard`, `ThankYou`.

## Idiomatic example

```jsx
import "@teatro/ui/styles.css";
import { Countdown, StorySection, RsvpCard, ThankYou } from "@teatro/ui";

export default function Invite() {
  return (
    <main className="bg-background text-foreground font-body">
      <header className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
        <p className="font-sans text-xs uppercase tracking-eyebrow text-muted-foreground">
          Together with their families
        </p>
        <h1 className="font-display text-7xl font-bold text-gradient-gold">Sam &amp; Sofia</h1>
        <p className="font-script text-3xl text-gold">are getting married</p>
      </header>

      <Countdown targetDate="2027-09-10T17:00:00+02:00" />
      <StorySection kicker="How it began" title="Two hearts, one yes" script="our story"
        body="From a chance hello in Florence to forever." />
      <RsvpCard hashtag="#SamAndSofia" onSubmit={(data) => console.log(data)} />
      <ThankYou names="Sam & Sofia" hashtag="#SamAndSofia" />
    </main>
  );
}
```

# TeatroUI (@teatro/ui@0.1.0)

This design system is the published @teatro/ui React library, bundled as a single
browser global. All 22 components are the real upstream code.

## Where things are

- `_ds_bundle.js` — the whole-DS bundle at the project root; loads every component to `window.TeatroUI`. First line is a `/* @ds-bundle: … */` metadata header.
- `styles.css` — the single stylesheet entry: it `@import`s the tokens, fonts, and component styles (`_ds_bundle.css`). Link this one file.
- `components/<group>/<Name>/<Name>.prompt.md` (example JSX + variants), `<Name>.d.ts` (types), `<Name>.html` (variant grid).
- `tokens/*.css` — CSS custom properties, names verbatim from upstream.
- `fonts/` — `@font-face` files + `fonts.css` (when the package ships fonts).

For a specific component, `read_file("components/<group>/<Name>/<Name>.prompt.md")`.

## Loading

Add these two lines to your page once (React must be on the page first):

```html
<link rel="stylesheet" href="styles.css">
<script src="_ds_bundle.js"></script>
```

Components are then available at `window.TeatroUI.*`. Mount into a dedicated child node (e.g. `<div id="ds-root">`), not the host page's own React root, so the two trees don't collide:

```jsx
const { Badge } = window.TeatroUI;
ReactDOM.createRoot(document.getElementById('ds-root')).render(<Badge />);
```

## Tokens

109 CSS custom properties from @teatro/ui. Names are
preserved verbatim from upstream. They are declared inside `_ds_bundle.css` (this DS ships one compiled stylesheet rather than separate token files).

- **color** (8): `--tw-border-spacing-x`, `--tw-border-spacing-y`, `--tw-ring-offset-color`, …
- **spacing** (1): `--tw-ring-inset`
- **typography** (3): `--font-display`, `--font-body`, `--font-script`
- **radius** (1): `--radius`
- **shadow** (7): `--shadow-soft`, `--shadow-elegant`, `--shadow-lifted`, …
- **other** (89): `--background`, `--foreground`, `--paper`, …

## Components

### atoms
- `Badge`
- `Button`
- `Card`
- `Divider`
- `Eyebrow`
- `Field`
- `Input`
- `RadioChoice`
- `SectionHeading`
- `Stepper`
- `Textarea`

### blocks
- `Countdown`
- `CurtainReveal`
- `DressCode`
- `GiftsRegistry`
- `MenuSection`
- `RsvpCard`
- `ScratchToReveal`
- `StorySection`
- `ThankYou`
- `Transportation`
- `VenueSection`
