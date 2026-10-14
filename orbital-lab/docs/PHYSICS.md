# Model and replay notes

## Coordinate and force model

The simulation uses meters, seconds, and meters per second. Screen +X points right and physical +Y points up. The display flips Y when projecting into the canvas.

Thrust is a commanded acceleration with constant spacecraft mass. Its magnitude is capped: diagonal input is normalized, so holding two directions does not create extra thrust. The propellant gauge is a model budget, not a calibrated tank or changing vehicle mass. Consumption scales with commanded thrust magnitude. When a step uses the remaining fuel, the impulse is averaged over that last integration step; thereafter thrust is zero.

Mission 1 and Mission 2 intentionally use zero gravitational acceleration and no drag. The target in Mission 2 is stationary in that simplified local inertial frame. This is a teaching exercise for relative position and velocity, not a model of real rendezvous dynamics in orbit.

Mission 3 uses:

- Lunar radius: 1,737,400 m.
- Lunar gravitational parameter: 4.9048695 × 10¹² m³/s².
- Initial altitude: 220,000 m above that spherical reference surface.
- Initial circular speed: sqrt(μ / r).
- Gravitational acceleration: **a = −μ r / |r|³**.
- Burn acceleration: 0.24 m/s² at full command.
- Simulated time: 240 seconds per real second.

These constants define the demo model; this implementation has not been calibrated against an operational lunar ephemeris. It omits the Earth's and Sun's gravity, lunar mass concentrations, terrain, spacecraft attitude, rotating reference frames, drag, and changing mass.

## Integration and sampling

The engine uses velocity Verlet, reevaluating gravity after the position update. Directional thrust is held constant for each step. Step sizes are 1/60 second for local missions and 4 seconds for the lunar mission. They are advanced from a fixed-step accumulator driven by the animation loop.

The loop caps a long wall-clock gap to avoid a large catch-up jump. A slow computer may therefore run more slowly than real time. The displayed simulated time is the authoritative time. Leaving the tab or window pauses a running flight.

States are recorded every six integration steps, with the final state retained. That is every 0.1 simulated second for local motion and every 24 simulated seconds for lunar orbit. During scrubbing, the display linearly interpolates adjacent recorded samples; the underlying integration itself does not use that interpolation.

## End conditions

- Thrust & coast: 22 simulated seconds.
- Rendezvous: separation strictly below 12 m and relative speed strictly below 1 m/s; otherwise 40 simulated seconds.
- Lunar orbit: 8,200 simulated seconds or surface contact.
- Any running/paused mission may be ended manually.

The surface check occurs after an integration step. It stops the trajectory when the position is at or inside the reference radius; it is not a sub-step collision solver. Craft and station icons are symbolic and are not physical collision geometry.

## Counterfactual branch

After the flight, the alternate branch starts from a copy of the original launch state, not from the replay cursor. All starting position, velocity, fuel, force-model parameters, and integration settings match. The control policy changes:

1. Coast: continuous +X thrust.
2. Rendezvous: no thrust, retaining the initial velocity.
3. Orbit: thrust along instantaneous velocity for the first 300 simulated seconds, then coast.

The second branch is integrated for the original flight's elapsed duration, or ends earlier at surface contact. It uses its own resulting position, velocity, and fuel state. It is not a translated copy of the first path.

## Visual conventions

Cyan denotes the recorded flight; dashed orange denotes the alternate trajectory. Velocity and acceleration arrows use different visual scales and are capped for readability. The viewport may zoom out to keep the non-orbital endpoints in view. The scale bar reports the current distance represented by 58 screen pixels.

Spacecraft orientation is symbolic: while firing it points along the thrust; while coasting it points along velocity. The simulator does not model rotational dynamics. The lunar texture is a visual illustration, not a terrain or navigation map.

## Learning feedback

Manual flight begins with an explicit multiple-choice prediction. Feedback compares that choice to the model's expected answer and adds observed numerical results. Guided flights do not invent a student prediction. No probability score, neural model, or hidden misconception diagnosis is implemented.

Sources for the conceptual explanations:

- [NASA Glenn — Newton's Laws of Motion](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/newtons-laws-of-motion/)
- [NASA — What Is Microgravity?](https://www.nasa.gov/learning-resources/for-kids-and-students/what-is-microgravity-grades-5-8/)
