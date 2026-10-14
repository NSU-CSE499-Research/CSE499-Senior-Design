const { test } = require('node:test');
const assert = require('node:assert/strict');
const P = require('../js/physics.js');
const coast = P.MISSIONS.coast, orbit = P.MISSIONS.orbit, dock = P.MISSIONS.dock;
const off = () => ({ x: 0, y: 0 });
const right = () => ({ x: 1, y: 0 });
const last = a => a[a.length - 1];
const close = (actual, expected, tolerance = 1e-7) => assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} differs from ${expected} by more than ${tolerance}`);

test('Force-free motion conserves the entire velocity vector and follows a straight line', () => {
  const start = { ...P.createState(coast), x: 10, y: -8, vx: 12, vy: -4 };
  const end = last(P.run(coast, start, 20, off));
  close(end.vx, 12); close(end.vy, -4); close(end.x, 250); close(end.y, -88); close(end.fuel, 100);
});
test('A constant thrust agrees with the analytic constant-acceleration solution', () => {
  const start = P.createState(coast), end = last(P.run(coast, start, 10, right));
  close(end.vx, coast.acceleration * 10); close(end.x, start.x + .5 * coast.acceleration * 100);
  close(end.fuel, 100 - coast.burnRate * 10); close(end.vy, 0);
});
test('Opposite burns cancel velocity while preserving the displacement already travelled', () => {
  const start = P.createState(coast);
  const midpoint = last(P.run(coast, start, 3, right));
  const end = last(P.run(coast, midpoint, 3, () => ({ x: -1, y: 0 })));
  close(end.vx, 0); close(end.x - start.x, coast.acceleration * 9); assert.ok(end.x > midpoint.x);
});
test('Diagonal input cannot exceed the thruster acceleration or double its fuel consumption', () => {
  const end = P.step(coast, P.createState(coast), { x: 1, y: 1 }, 1);
  close(Math.hypot(end.vx, end.vy), coast.acceleration); close(end.fuel, 100 - coast.burnRate);
});
test('Fuel exhaustion limits the final impulse and leaves a ballistic trajectory', () => {
  const start = { ...P.createState(coast), fuel: coast.burnRate * .25 };
  const burnt = P.step(coast, start, { x: 1, y: 0 }, 1);
  close(burnt.fuel, 0); close(burnt.vx, coast.acceleration * .25);
  const after = P.step(coast, burnt, { x: 1, y: 0 }, 10);
  close(after.fuel, 0); close(after.thrust, 0); close(after.vx, burnt.vx);
});
test('A full circular orbit approximately conserves specific energy and angular momentum', () => {
  const start = P.createState(orbit), radius = Math.hypot(start.x, start.y);
  const period = 2 * Math.PI * Math.sqrt(radius ** 3 / orbit.mu);
  const samples = P.run(orbit, start, period, off, 4, 10);
  const initialEnergy = P.metrics(orbit, start).specificEnergy, h0 = start.x * start.vy - start.y * start.vx;
  for (const s of samples) {
    assert.ok(Math.abs((P.metrics(orbit, s).specificEnergy - initialEnergy) / initialEnergy) < 1e-5);
    assert.ok(Math.abs((s.x * s.vy - s.y * s.vx - h0) / h0) < 1e-10);
    assert.ok(Math.abs(Math.hypot(s.x, s.y) - radius) / radius < 1e-4);
  }
  const end = last(samples);
  assert.ok(Math.hypot(end.x - start.x, end.y - start.y) < 200);
  assert.ok(P.metrics(orbit, end).gravity > 1);
});
test('Replay is deterministic, preserves its initial snapshot, and changes with a new control policy', () => {
  const start = P.createState(coast), untouched = { ...start };
  const a = P.run(coast, start, 20, P.demoControl);
  const b = P.run(coast, start, 20, P.demoControl);
  const alt = P.run(coast, start, 20, P.alternativeControl);
  assert.deepEqual(a, b); assert.deepEqual(start, untouched); assert.deepEqual(a[0], alt[0]);
  close(last(a).t, last(alt).t); assert.ok(last(alt).vx > last(a).vx + 40);
});
test('Rendezvous requires both a near position and a low relative speed', () => {
  const near = { ...P.createState(dock), x: dock.target.x, y: dock.target.y, vx: .4, vy: .3 };
  assert.equal(P.metrics(dock, near).docked, true);
  assert.equal(P.metrics(dock, { ...near, vx: 10 }).docked, false);
  assert.equal(P.metrics(dock, { ...near, x: dock.target.x + 13 }).docked, false);
});
test('The guided rendezvous reaches the target within the mission time and fuel budget', () => {
  const samples = P.run(dock, P.createState(dock), dock.duration, P.demoControl);
  const arrival = samples.find(s => P.metrics(dock, s).docked);
  assert.ok(arrival, 'Guided pilot failed to rendezvous'); assert.ok(arrival.fuel > 0); assert.ok(arrival.t < dock.duration);
});
test('A prograde burn raises orbital energy and later altitude', () => {
  const start = P.createState(orbit);
  const alt = P.run(orbit, start, 4000, P.alternativeControl, 4);
  assert.ok(P.metrics(orbit, last(alt)).specificEnergy > P.metrics(orbit, start).specificEnergy);
  assert.ok(P.metrics(orbit, last(alt)).altitude > P.metrics(orbit, start).altitude + 100000);
});
test('Changing integration step size does not change constant-force motion', () => {
  const start = P.createState(coast);
  const a = last(P.run(coast, start, 8, right, 1 / 30));
  const b = last(P.run(coast, start, 8, right, 1 / 120));
  close(a.x, b.x); close(a.vx, b.vx); close(a.fuel, b.fuel);
});
test('Surface contact ends a lunar trajectory instead of tunnelling through the Moon indefinitely', () => {
  const falling = { ...P.createState(orbit), x: orbit.radius + 5, y: 0, vx: -20, vy: 0 };
  const contact = P.step(orbit, falling, { x: 0, y: 0 }, 1);
  assert.equal(contact.impact, true); assert.deepEqual(P.step(orbit, contact, { x: 1, y: 0 }, 1), contact);
});
test('Invalid integration time steps are rejected', () => {
  [0, -1, Infinity, NaN].forEach(dt => assert.throws(() => P.step(coast, P.createState(coast), { x: 0, y: 0 }, dt)));
});
