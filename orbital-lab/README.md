# ORBITAL LAB

**Make space for discovery.**

A complete NASA-inspired editorial website and playable spaceflight learning prototype. Original Orbital Lab identity, NASA photographs, three interactive missions, prediction prompts, telemetry, and counterfactual replay.

## Open the website

1. Extract the entire ZIP.
2. Open the `orbital-lab` folder.
3. Double-click **`index.html`**.

No installation, API key, account, or internet connection is needed for the app. Keep the `assets`, `js`, and stylesheet files beside `index.html`. External science and image-credit links need an internet connection.

**বাংলায়:** ZIP extract করে `orbital-lab` folder-এর `index.html` খুলুন। কোনো installation লাগবে না। Demo দেখাতে **Watch a guided flight** চাপুন।

Use a current browser supporting Canvas, Pointer Events, and native HTML dialogs. Browser compatibility and visual layout still need a real browser review; see `docs/VERIFICATION.md`.

### Optional local server / code editor

Open this folder in VS Code or another editor. If Node.js 18 or newer is already installed:

```sh
npm start
```

Then visit `http://localhost:3000`. There are no npm dependencies and no `npm install` step. Stop the server with Ctrl+C. The optional server listens only on your own machine. You can also use your editor's ordinary static preview server.

## What is included

- A responsive homepage with an Apollo 8 Earthrise hero, mission collection, science articles, project notes, and image credits.
- Three functioning 2D missions: thrust and coast, rendezvous, and lunar orbit.
- Manual keyboard and touch control, guided demonstrations, pause, reset, and end-flight controls.
- Live speed, propellant, gravity, and mission-specific telemetry.
- A prediction question before manual flight, followed by explicit rule-based feedback.
- Real trace replay with a time scrubber and an alternate simulated control policy.
- JSON download containing the model settings, prediction, outcome, initial state, and both trajectories.
- Keyboard-accessible dialogs, visible focus indicators, a mobile menu, and reduced-motion styling.
- A dependency-free numerical test suite and local asset/wiring checks.

## Present it in three minutes

1. Introduce the homepage: “A spaceflight learning lab where students predict, experiment, and compare.”
2. Choose **Mission 01** and click **Watch a guided flight**. The craft burns for three seconds, then coasts. Its velocity stays constant after the burn.
3. At the end, drag the replay slider. Cyan is the recorded flight; orange keeps thrusting from exactly the same starting state.
4. Choose **Mission 02** and run the guided flight. Show that success requires both a small separation and a low relative speed.
5. Choose **Mission 03**. The engine stays off while gravity bends the trajectory. Time is accelerated by 240×.
6. Open **What if you made one different decision?** in the science section, then show **Download flight data** after a flight.

## Controls

| Control | Action |
| --- | --- |
| W / up arrow | Apply +Y thrust |
| S / down arrow | Apply −Y thrust |
| A / left arrow | Apply −X thrust |
| D / right arrow | Apply +X thrust |
| Release controls | Coast |
| Space, with the canvas focused | Pause or resume |
| On-screen arrows | Hold for touch/mouse thrust |
| Vectors | Show velocity and acceleration arrows |
| End flight | Stop now and build the alternate trajectory |
| Replay slider | Compare equal moments in both traces |
| Reset | Discard the current flight and return to the mission start |

These are directional thrusters, not attitude controls. Up always means +Y in the displayed frame. Manual controls are disabled during a guided demonstration. Leaving the browser tab/window pauses a running flight. Sessions remain in memory; download a trace before refreshing to keep it.

## Missions and counterfactuals

| Mission | Your experiment | Alternate control policy |
| --- | --- | --- |
| Thrust & coast | Pulse the thruster, release, and observe inertia | Continuous +X thrust |
| Rendezvous | Enter the target region below 1 m/s | All thrusters off |
| Orbit & free fall | Follow a 220 km initial circular lunar orbit | Prograde thrust for 300 simulated seconds, then coast |

Both branches use the same initial state, force model, fuel budget, and integration step. The alternate branch runs for the original flight's duration, unless it contacts the lunar surface first. Replay positions between recorded samples are interpolated for display. Flight integration uses fixed steps, independently of the rendering rate.

## Source map

| File | Responsibility |
| --- | --- |
| `index.html` | All page sections, mission cards, accessible controls, and dialog container |
| `styles.css` | Desktop, tablet, mobile, and reduced-motion styles |
| `js/physics.js` | Pure model, mission parameters, integration, metrics, and control policies |
| `js/app.js` | UI state, canvas rendering, input, predictions, replay, and JSON export |
| `assets/` | Local photographs, Moon texture, and original SVG favicon |
| `tests/` | Node.js numerical and package integrity checks |
| `server.cjs` | Optional loopback-only static server |
| `docs/` | Physics notes, credits, verification, and a three-person capstone plan |

Edit the colors in the `:root` variables in `styles.css`. Change text and sections in `index.html`. Change mission questions, initial conditions, or burn parameters in `js/physics.js`.

## Run the checks

With Node.js 18 or newer:

```sh
npm run check
```

This parses the JavaScript and runs the numerical and package tests. It does not launch or visually test a browser.

## Scope

This is an educational software prototype. The first two missions intentionally omit gravity and drag to isolate local-motion concepts. The orbital mission uses lunar central gravity and a constant-mass craft. It is not an actual zero-gravity machine, a professional navigation simulator, or a validated learning intervention.

Feedback is rule-based, not a trained AI model. Novelty and learning effectiveness require a prior-art review and user study. See `docs/PHYSICS.md` and `docs/CAPSTONE-NEXT-STEPS.md` for the model limits and next work.

The original code is under the MIT license. NASA-sourced imagery has separate attribution in `docs/CREDITS.md`. The project is not affiliated with NASA.
