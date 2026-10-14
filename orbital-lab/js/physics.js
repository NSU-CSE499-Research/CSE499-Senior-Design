/* Orbital Lab — deterministic, SI-unit 2D teaching model. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.OrbitalPhysics = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const MOON_RADIUS = 1737400;
  const MOON_MU = 4.9048695e12;
  const orbitRadius = MOON_RADIUS + 220000;
  const MISSIONS = {
    coast: {
      id: 'coast', number: '01', name: 'The art of doing nothing', short: 'Thrust & coast',
      description: 'Give the spacecraft a short push. Release the thrusters and watch what happens next.',
      objective: 'Thrust for a few seconds, then coast. Does your speed disappear when the engine switches off?',
      question: 'When the thruster switches off, the spacecraft will…',
      choices: ['Keep its velocity', 'Gradually slow down', 'Stop immediately'], correct: 0,
      explanation: 'With no net force in this model, velocity stays constant. An engine changes velocity; it is not needed to maintain it.',
      initial: { x: -105, y: -12, vx: 0, vy: 0 }, target: null,
      gravity: false, acceleration: 3.2, burnRate: 2.2, timeScale: 1, duration: 22,
      view: 390, alternative: 'Keep thrusting', altDescription: 'The same launch state, with a continuous rightward burn instead of your control sequence.'
    },
    dock: {
      id: 'dock', number: '02', name: 'Arrive. Then stay.', short: 'Rendezvous',
      description: 'Closing the gap is only half the mission. Match velocity to stay beside the station.',
      objective: 'Reach the target ring within 12 m, at less than 1 m/s. Use opposite thrust to brake.',
      question: 'To remain beside a stationary target, you need to…',
      choices: ['Match position and velocity', 'Only reach its position', 'Keep accelerating toward it'], correct: 0,
      explanation: 'A rendezvous requires a small separation AND a small relative speed. Braking changes your velocity before you arrive.',
      initial: { x: -125, y: -38, vx: 10, vy: 1.5 }, target: { x: 92, y: 32 },
      gravity: false, acceleration: 3.6, burnRate: 1.7, timeScale: 1, duration: 40,
      view: 430, alternative: 'Never brake', altDescription: 'The same launch position and velocity, with every thruster left off.'
    },
    orbit: {
      id: 'orbit', number: '03', name: 'Fall around the Moon', short: 'Orbit & free fall',
      description: 'An orbit is a continuous fall. Follow the changing direction of velocity around the Moon.',
      objective: 'Watch one orbit with the engine off. Turn on vectors to see gravity bend the velocity direction.',
      question: 'With the engine off in a circular lunar orbit, gravity is…',
      choices: ['Still accelerating the craft', 'Zero outside the atmosphere', 'Balanced by an outward force'], correct: 0,
      explanation: 'Gravity supplies inward acceleration throughout the orbit. In the ideal engine-off model, a freely falling occupant and spacecraft accelerate together.',
      initial: { x: orbitRadius, y: 0, vx: 0, vy: Math.sqrt(MOON_MU / orbitRadius) }, target: null,
      gravity: true, mu: MOON_MU, radius: MOON_RADIUS,
      acceleration: 0.24, burnRate: 0.014, timeScale: 240, duration: 8200,
      view: 5700000, alternative: 'Add a prograde burn', altDescription: 'The same launch state, with a 300-second burn along the direction of motion, followed by coasting.'
    }
  };
  function createState(config) { return { ...config.initial, t: 0, fuel: 100, ax: 0, ay: 0, thrust: 0, impact: false }; }
  function gravity(config, x, y) {
    if (!config.gravity) return { x: 0, y: 0 };
    const r = Math.max(Math.hypot(x, y), config.radius);
    const k = -config.mu / (r * r * r);
    return { x: k * x, y: k * y };
  }
  function step(config, state, control, dt) {
    if (!Number.isFinite(dt) || dt <= 0) throw new Error('A positive finite time step is required.');
    if (state.impact) return { ...state };
    let cx = Number(control.x) || 0, cy = Number(control.y) || 0;
    const length = Math.hypot(cx, cy);
    if (length > 1) { cx /= length; cy /= length; }
    const magnitude = Math.hypot(cx, cy);
    const requestedFuel = config.burnRate * dt * magnitude;
    const fraction = requestedFuel > 0 ? Math.min(1, state.fuel / requestedFuel) : 0;
    const tx = cx * config.acceleration * fraction, ty = cy * config.acceleration * fraction;
    const g0 = gravity(config, state.x, state.y);
    const x = state.x + state.vx * dt + 0.5 * (g0.x + tx) * dt * dt;
    const y = state.y + state.vy * dt + 0.5 * (g0.y + ty) * dt * dt;
    const g1 = gravity(config, x, y);
    return {
      t: state.t + dt, x, y,
      vx: state.vx + (0.5 * (g0.x + g1.x) + tx) * dt,
      vy: state.vy + (0.5 * (g0.y + g1.y) + ty) * dt,
      fuel: Math.max(0, state.fuel - requestedFuel), ax: g1.x + tx, ay: g1.y + ty,
      thrust: Math.hypot(tx, ty), impact: !!config.gravity && Math.hypot(x, y) <= config.radius
    };
  }
  function demoControl(config, state) {
    if (config.id === 'coast') return { x: state.t < 3 - 1e-9 ? 1 : 0, y: 0 };
    if (config.id === 'orbit') return { x: 0, y: 0 };
    const dx = config.target.x - state.x, dy = config.target.y - state.y;
    // Smooth velocity command plus proportional braking, in the local inertial model.
    const distance = Math.hypot(dx, dy);
    const speed = Math.min(14, distance * 0.22);
    const desiredX = distance > 0 ? dx / distance * speed : 0;
    const desiredY = distance > 0 ? dy / distance * speed : 0;
    return { x: (desiredX - state.vx) * 1.4 / config.acceleration, y: (desiredY - state.vy) * 1.4 / config.acceleration };
  }
  function alternativeControl(config, state) {
    if (config.id === 'coast') return { x: 1, y: 0 };
    if (config.id === 'dock' || state.t >= 300) return { x: 0, y: 0 };
    const speed = Math.hypot(state.vx, state.vy) || 1;
    return { x: state.vx / speed, y: state.vy / speed };
  }
  function run(config, initial, duration, controlFn, dt = 1 / 60, sampleEvery = 6) {
    let state = { ...initial };
    const trace = [{ ...state }];
    let n = 0;
    while (state.t < initial.t + duration - 1e-9 && !state.impact) {
      state = step(config, state, controlFn(config, state), Math.min(dt, initial.t + duration - state.t));
      n++;
      if (n % sampleEvery === 0 || state.t >= initial.t + duration - 1e-9 || state.impact) trace.push({ ...state });
    }
    return trace;
  }
  function metrics(config, state) {
    const radius = Math.hypot(state.x, state.y);
    const speed = Math.hypot(state.vx, state.vy);
    const g = gravity(config, state.x, state.y);
    const distance = config.target ? Math.hypot(state.x - config.target.x, state.y - config.target.y) : null;
    return { speed, gravity: Math.hypot(g.x, g.y), altitude: config.gravity ? radius - config.radius : null,
      distance, docked: config.id === 'dock' && distance < 12 && speed < 1,
      specificEnergy: config.gravity ? speed * speed / 2 - config.mu / radius : speed * speed / 2 };
  }
  return { MISSIONS, MOON_RADIUS, MOON_MU, createState, gravity, step, metrics, demoControl, alternativeControl, run };
}));
