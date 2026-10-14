/* Orbital Lab interface. No framework, network, account, or build step. */
(() => {
  'use strict';
  const P = window.OrbitalPhysics;
  const $ = id => document.getElementById(id);
  const canvas = $('flight-canvas');
  const ctx = canvas.getContext('2d');
  const dialog = $('content-dialog');
  const moon = new Image(); moon.src = 'assets/moon.jpg';
  let config = P.MISSIONS.coast;
  let state = P.createState(config);
  let initial = { ...state }, trace = [{ ...state }], branch = [];
  let phase = 'idle', guided = false, prediction = null, sampleCounter = 0;
  let replayIndex = 1, replayPlaying = false, replayClock = 0;
  let simAccumulator = 0, lastFrame = 0, lastUiTime = 0, currentControl = { x: 0, y: 0 };
  let width = 700, height = 440, pixelRatio = 1, flightOutcome = '';
  let viewCenter = { x: 0, y: 0 }, viewScale = 1, visible = true;
  const held = new Set();
  const stars = Array.from({ length: 100 }, (_, i) => ({ x: fract(Math.sin(i * 127.1 + 12) * 43758.5453), y: fract(Math.sin(i * 311.7 + 8) * 12742.823), a: .13 + (i % 5) * .09 }));
  const directions = { up: { x: 0, y: 1 }, down: { x: 0, y: -1 }, left: { x: -1, y: 0 }, right: { x: 1, y: 0 } };
  function fract(n) { return n - Math.floor(n); }
  function timeLabel(t, orbit = false) {
    if (orbit) return `${String(Math.floor(t / 3600)).padStart(2, '0')}:${String(Math.floor(t % 3600 / 60)).padStart(2, '0')}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
    return `${String(Math.floor(t / 60)).padStart(2, '0')}:${(t % 60).toFixed(1).padStart(4, '0')}`;
  }
  function text(id, value) { $(id).textContent = value; }
  function value(id, number, unit, digits = 1) {
    $(id).replaceChildren(document.createTextNode(`${number.toFixed(digits)} `));
    const small = document.createElement('small'); small.textContent = unit; $(id).append(small);
  }
  function showToast(message) {
    text('toast', message); $('toast').classList.add('visible');
    clearTimeout(showToast.timeout); showToast.timeout = setTimeout(() => $('toast').classList.remove('visible'), 4200);
  }
  function openDialog(html) {
    if (phase === 'running') togglePause();
    replayPlaying = false;
    $('dialog-content').innerHTML = html;
    if (!dialog.open) dialog.showModal();
  }
  $('close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
  $('menu-toggle').addEventListener('click', () => {
    const open = $('main-nav').classList.toggle('open');
    $('menu-toggle').setAttribute('aria-expanded', String(open));
    $('menu-toggle').setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  });
  document.querySelectorAll('.main-nav a').forEach(link => link.addEventListener('click', () => {
    $('main-nav').classList.remove('open'); $('menu-toggle').setAttribute('aria-expanded', 'false');
    $('menu-toggle').setAttribute('aria-label', 'Open navigation');
  }));
  function releaseControls() {
    held.clear(); document.querySelectorAll('[data-direction]').forEach(button => button.classList.remove('pressed'));
    currentControl = { x: 0, y: 0 };
  }
  function selectMission(id) {
    if (!P.MISSIONS[id]) return;
    config = P.MISSIONS[id];
    document.querySelectorAll('[data-lab-mission]').forEach(button => {
      const active = button.dataset.labMission === id;
      button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active));
    });
    resetFlight();
    text('mission-number', config.number); text('active-mission-title', config.name); text('mission-objective', config.objective);
    text('viewport-label', config.gravity ? 'MOON-CENTERED INERTIAL FRAME' : 'LOCAL INERTIAL FRAME');
    text('rate-label', `SIMULATION / ${config.timeScale}× TIME`);
    text('secondary-label', config.id === 'dock' ? 'SEPARATION' : config.gravity ? 'ALTITUDE' : 'THRUST ACCEL.');
    text('model-note', config.gravity ? '2D lunar point-mass gravity · 240× time · SI units' : '2D inertial frame · no drag · constant mass');
    text('branch-name', config.alternative);
    render(); updateUI();
  }
  document.querySelectorAll('[data-mission]').forEach(button => button.addEventListener('click', () => {
    selectMission(button.dataset.mission);
    $('flight-lab').scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }));
  document.querySelectorAll('[data-lab-mission]').forEach(button => button.addEventListener('click', () => selectMission(button.dataset.labMission)));
  function resetFlight() {
    phase = 'idle'; guided = false; prediction = null; replayPlaying = false;
    state = P.createState(config); initial = { ...state }; trace = [{ ...state }]; branch = [];
    replayIndex = 1; replayClock = 0; simAccumulator = 0; sampleCounter = 0; flightOutcome = '';
    releaseControls(); $('replay-panel').hidden = true; $('result-actions').hidden = true;
    $('start-flight').hidden = false; $('demo-flight').hidden = false;
    $('pause-flight').disabled = true; $('finish-flight').disabled = true;
    $('pause-flight').querySelector('span').textContent = 'Pause';
    $('demo-flight').disabled = false; $('start-flight').disabled = false;
    $('replay-scrub').value = '1000'; text('replay-toggle', '▶ Replay');
    text('state-label', 'AWAITING PILOT');
    text('viewport-hint', config.id === 'coast' ? 'One small push can change everything.' : config.id === 'dock' ? 'Arrive gently. Position + velocity.' : 'Engine off. Gravity on.');
    text('tutor-message', config.id === 'coast' ? 'What do you think happens after the engine cuts out? Make a prediction, then put it to the test.' : config.id === 'dock' ? 'What makes a successful rendezvous? Predict first, then try matching both position and velocity.' : 'Is gravity still acting in orbit? Make your prediction, then watch the direction of the velocity vector.');
    updateUI(); render();
  }
  function requestPrediction() {
    const order = config.id === 'coast' ? [1, 0, 2] : config.id === 'dock' ? [2, 1, 0] : [0, 2, 1];
    openDialog(`<p class="eyebrow">MISSION ${config.number} / BEFORE WE LAUNCH</p><h2 id="dialog-title">Trust your intuition.<br>Then test it.</h2><p>${config.question}</p><form id="prediction-form"><fieldset class="prediction-options"><legend>Choose your prediction</legend>${order.map(i => `<label class="prediction-option"><input type="radio" name="prediction" value="${i}" required><span>${config.choices[i]}</span></label>`).join('')}</fieldset><button class="button button-orange" type="submit">Launch my flight <svg class="icon"><use href="#i-arrow"/></svg></button></form><p class="dialog-muted">Arrow keys or WASD: directional thrust. Space: pause.<br>${config.gravity ? 'Orbit time runs 240× faster. Watch first, then try a small burn.' : 'Tap or hold the on-screen arrow controls on a phone.'}</p>`);
    $('prediction-form').addEventListener('submit', event => {
      event.preventDefault(); const selected = new FormData(event.currentTarget).get('prediction');
      if (selected === null) return;
      prediction = Number(selected); dialog.close(); beginFlight(false);
    });
  }
  function beginFlight(isGuided) {
    const chosenPrediction = prediction;
    resetFlight(); prediction = isGuided ? null : chosenPrediction;
    guided = isGuided; phase = 'running';
    $('start-flight').hidden = true; $('demo-flight').hidden = true;
    $('pause-flight').disabled = false; $('finish-flight').disabled = false;
    text('state-label', guided ? 'GUIDED FLIGHT' : 'PILOT IN CONTROL');
    text('viewport-hint', guided ? 'Guided controls active. Watch the vectors.' : 'WASD / arrows to thrust. Space to pause.');
    text('tutor-message', config.id === 'coast' ? 'A cyan arrow shows velocity. Try a short burn, then release. Watch whether your speed changes while coasting.' : config.id === 'dock' ? 'The target ring is fixed in this local frame. Watch separation and speed together. Opposite thrust helps you brake.' : 'The cyan arrow is velocity. The blue arrow points inward: gravity is changing the direction even with the engine off.');
    canvas.focus({ preventScroll: true }); updateUI();
  }
  function togglePause() {
    if (phase !== 'running' && phase !== 'paused') return;
    phase = phase === 'running' ? 'paused' : 'running'; simAccumulator = 0; releaseControls();
    $('pause-flight').querySelector('span').textContent = phase === 'paused' ? 'Resume' : 'Pause';
    text('state-label', phase === 'paused' ? 'FLIGHT PAUSED' : guided ? 'GUIDED FLIGHT' : 'PILOT IN CONTROL');
  }
  function finishFlight(reason = 'completed') {
    if (phase !== 'running' && phase !== 'paused') return;
    phase = 'complete'; flightOutcome = reason; releaseControls();
    if (trace[trace.length - 1].t !== state.t) trace.push({ ...state });
    // Recompute alternate controls with the same initial state and elapsed duration.
    branch = P.run(config, initial, state.t, P.alternativeControl, config.timeScale / 60, 6);
    replayIndex = 1; replayPlaying = false; replayClock = state.t;
    $('pause-flight').disabled = true; $('finish-flight').disabled = true;
    $('start-flight').hidden = true; $('demo-flight').hidden = true; $('result-actions').hidden = false;
    $('replay-panel').hidden = false; $('replay-scrub').value = '1000'; text('replay-toggle', '▶ Replay');
    text('state-label', reason === 'impact' ? 'SURFACE CONTACT' : reason === 'docked' ? 'RENDEZVOUS ACHIEVED' : 'FLIGHT RECORDED');
    text('viewport-hint', 'Cyan: your flight. Orange: one different decision.');
    const endStats = P.metrics(config, state), altStats = P.metrics(config, branch[branch.length - 1]);
    let evidence;
    if (config.id === 'coast') evidence = `Your final speed: ${endStats.speed.toFixed(1)} m/s. Continuous rightward thrust: ${altStats.speed.toFixed(1)} m/s. ${config.explanation}`;
    else if (config.id === 'dock') evidence = `Your final separation: ${endStats.distance.toFixed(1)} m, at ${endStats.speed.toFixed(1)} m/s. Without thrust: ${altStats.distance.toFixed(1)} m away. ${endStats.docked ? 'You matched both position and velocity.' : 'Aim for less than 12 m separation and less than 1 m/s speed.'}`;
    else evidence = `Gravity now: ${endStats.gravity.toFixed(2)} m/s². Your altitude: ${(endStats.altitude / 1000).toFixed(0)} km. The orange replay adds an early prograde burn. ${reason === 'impact' ? 'The flight ended when the model crossed the lunar surface.' : 'Free fall and zero gravity are different ideas.'}`;
    const prefix = prediction === null ? 'Guided observation. ' : prediction === config.correct ? 'Your prediction matches the model. ' : 'A useful course correction. ';
    text('tutor-message', prefix + evidence);
    text('replay-time', timeLabel(state.t, config.gravity)); updateUI(); render();
    showToast(reason === 'docked' ? 'Rendezvous achieved. Compare your replay below.' : 'Flight recorded. Scrub the timeline to compare both paths.');
  }
  $('start-flight').addEventListener('click', requestPrediction);
  $('demo-flight').addEventListener('click', () => beginFlight(true));
  $('reset-flight').addEventListener('click', resetFlight);
  $('retry-flight').addEventListener('click', resetFlight);
  $('pause-flight').addEventListener('click', togglePause);
  $('finish-flight').addEventListener('click', () => finishFlight('ended-by-pilot'));
  $('show-vectors').addEventListener('change', render);
  $('replay-scrub').addEventListener('input', () => {
    replayIndex = Number($('replay-scrub').value) / 1000; replayClock = state.t * replayIndex; replayPlaying = false;
    text('replay-toggle', '▶ Replay'); updateUI(); render();
  });
  $('replay-toggle').addEventListener('click', () => {
    replayPlaying = !replayPlaying;
    if (replayPlaying && replayIndex >= .999) { replayClock = 0; replayIndex = 0; }
    text('replay-toggle', replayPlaying ? 'Ⅱ Pause replay' : '▶ Replay');
  });
  function exportFlight() {
    if (phase !== 'complete') return;
    const output = {
      project: 'Orbital Lab', schemaVersion: 1, exportedAt: new Date().toISOString(),
      mission: config.id, mode: guided ? 'guided' : 'manual', outcome: flightOutcome,
      prediction: prediction === null ? null : config.choices[prediction], expectedPrediction: config.choices[config.correct],
      units: { time: 's', position: 'm', velocity: 'm/s', acceleration: 'm/s^2', fuel: 'percent of initial model budget' },
      model: { dimensions: 2, integrator: 'velocity Verlet', stepSeconds: config.timeScale / 60, gravity: config.gravity ? 'lunar central point mass' : 'none', mu: config.mu || 0, radius: config.radius || 0, constantMass: true, drag: false, thrusterAcceleration: config.acceleration },
      initialState: initial, durationSeconds: state.t,
      alternative: { name: config.alternative, description: config.altDescription },
      originalTrace: trace, alternateTrace: branch,
      note: 'Educational model. Feedback is rule-based. No human study or research novelty is established by this demo.'
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(output, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = `orbital-lab-${config.id}-flight.json`;
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 10000);
    showToast('Your flight data is ready to download as JSON.');
  }
  $('export-flight').addEventListener('click', exportFlight);
  const keyMap = { ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right', w: 'up', s: 'down', a: 'left', d: 'right' };
  document.addEventListener('keydown', event => {
    if (dialog.open || ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) return;
    if (phase !== 'running' && phase !== 'paused') return;
    if (!visible) return;
    const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
    if (key === ' ' && (event.target === canvas || event.target === document.body)) {
      event.preventDefault(); if (!event.repeat) togglePause(); return;
    }
    if (!keyMap[key] || phase !== 'running' || guided) return;
    event.preventDefault(); held.add(keyMap[key]);
    document.querySelector(`[data-direction="${keyMap[key]}"]`).classList.add('pressed');
  });
  document.addEventListener('keyup', event => {
    const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
    if (keyMap[key]) { held.delete(keyMap[key]); document.querySelector(`[data-direction="${keyMap[key]}"]`).classList.remove('pressed'); }
  });
  document.querySelectorAll('[data-direction]').forEach(button => {
    button.addEventListener('pointerdown', event => {
      if (phase !== 'running' || guided) return;
      event.preventDefault(); button.setPointerCapture(event.pointerId); held.add(button.dataset.direction); button.classList.add('pressed');
    });
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(type => button.addEventListener(type, () => {
      held.delete(button.dataset.direction); button.classList.remove('pressed');
    }));
  });
  window.addEventListener('blur', () => { releaseControls(); if (phase === 'running') togglePause(); });
  document.addEventListener('visibilitychange', () => { if (document.hidden && phase === 'running') togglePause(); });
  function userControl() {
    let x = 0, y = 0; held.forEach(key => { x += directions[key].x; y += directions[key].y; });
    return { x, y };
  }
  function sampleAt(samples, t) {
    if (!samples.length) return state;
    if (t <= samples[0].t) return samples[0];
    if (t >= samples[samples.length - 1].t) return samples[samples.length - 1];
    let lo = 0, hi = samples.length - 1;
    while (lo + 1 < hi) { const mid = (lo + hi) >> 1; if (samples[mid].t < t) lo = mid; else hi = mid; }
    const a = samples[lo], b = samples[hi], mix = (t - a.t) / (b.t - a.t);
    const result = { ...a };
    ['t', 'x', 'y', 'vx', 'vy', 'fuel', 'ax', 'ay', 'thrust'].forEach(key => { result[key] = a[key] + (b[key] - a[key]) * mix; });
    return result;
  }
  function displayState() { return phase === 'complete' ? sampleAt(trace, state.t * replayIndex) : state; }
  function updateUI() {
    const shown = displayState(), stats = P.metrics(config, shown);
    value('speed-value', stats.speed / (config.gravity ? 1000 : 1), config.gravity ? 'km/s' : 'm/s', config.gravity ? 2 : 1);
    if (config.id === 'dock') value('secondary-value', stats.distance, 'm', 1);
    else if (config.gravity) value('secondary-value', stats.altitude / 1000, 'km', 0);
    else value('secondary-value', shown.thrust, 'm/s²', 1);
    value('fuel-value', shown.fuel, '%', 0); value('force-value', stats.gravity, 'm/s²', 2);
    $('fuel-bar').style.width = `${shown.fuel}%`; text('sim-time', 'T+ ' + timeLabel(shown.t, config.gravity));
    if (phase === 'complete') text('replay-time', timeLabel(shown.t, config.gravity));
  }
  function resize() {
    const box = canvas.getBoundingClientRect(); width = Math.max(1, box.width); height = Math.max(1, box.height);
    pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * pixelRatio); canvas.height = Math.round(height * pixelRatio);
    render();
  }
  function calculateView() {
    if (config.gravity) { viewCenter = { x: 0, y: 0 }; viewScale = Math.min(width, height - 70) / config.view; return; }
    let minX = -160, maxX = 170, minY = -70, maxY = 80;
    const points = phase === 'complete' ? [trace[trace.length - 1], branch[branch.length - 1], initial] : [state, initial];
    points.filter(Boolean).forEach(p => { minX = Math.min(minX, p.x - 35); maxX = Math.max(maxX, p.x + 35); minY = Math.min(minY, p.y - 40); maxY = Math.max(maxY, p.y + 40); });
    viewCenter = { x: (minX + maxX) / 2, y: (minY + maxY) / 2 };
    viewScale = Math.min((width - 80) / Math.max(config.view, maxX - minX), (height - 140) / Math.max(170, maxY - minY));
  }
  function screen(x, y) { return { x: width / 2 + (x - viewCenter.x) * viewScale, y: height / 2 - (y - viewCenter.y) * viewScale }; }
  function pathLine(samples, time, color, dashed = false) {
    if (samples.length < 2) return;
    ctx.beginPath(); let started = false;
    for (const sample of samples) {
      if (sample.t > time) break;
      const p = screen(sample.x, sample.y); if (!started) { ctx.moveTo(p.x, p.y); started = true; } else ctx.lineTo(p.x, p.y);
    }
    if (started) { const last = sampleAt(samples, time), p = screen(last.x, last.y); ctx.lineTo(p.x, p.y); }
    ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash(dashed ? [4, 5] : []); ctx.stroke(); ctx.setLineDash([]);
  }
  function arrow(x, y, dx, dy, color, label) {
    const length = Math.hypot(dx, dy); if (length < 3) return;
    const endX = x + dx, endY = y + dy, angle = Math.atan2(dy, dx);
    ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 1.1;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(endX, endY); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(endX, endY); ctx.lineTo(endX - 6 * Math.cos(angle - .45), endY - 6 * Math.sin(angle - .45)); ctx.lineTo(endX - 6 * Math.cos(angle + .45), endY - 6 * Math.sin(angle + .45)); ctx.closePath(); ctx.fill();
    if (label) { ctx.font = '9px monospace'; ctx.fillText(label, endX + 7, endY - 5); }
  }
  function drawMoon() {
    const center = screen(0, 0), radius = config.radius * viewScale;
    ctx.save(); ctx.beginPath(); ctx.arc(center.x, center.y, radius, 0, Math.PI * 2); ctx.clip();
    ctx.fillStyle = '#71767a'; ctx.fillRect(center.x - radius, center.y - radius, radius * 2, radius * 2);
    if (moon.complete && moon.naturalWidth) ctx.drawImage(moon, moon.naturalWidth * .24, 0, moon.naturalWidth * .5, moon.naturalHeight, center.x - radius, center.y - radius, radius * 2, radius * 2);
    const shade = ctx.createRadialGradient(center.x - radius * .55, center.y - radius * .4, 0, center.x + radius * .1, center.y + radius * .1, radius * 1.25);
    shade.addColorStop(0, '#ffffff08'); shade.addColorStop(.45, '#00000018'); shade.addColorStop(1, '#000000e8');
    ctx.fillStyle = shade; ctx.fillRect(center.x - radius, center.y - radius, radius * 2, radius * 2); ctx.restore();
    ctx.beginPath(); ctx.arc(center.x, center.y, radius + .5, 0, Math.PI * 2); ctx.strokeStyle = '#8aabb82c'; ctx.lineWidth = 1; ctx.stroke();
    ctx.font = '8px monospace'; ctx.fillStyle = '#c6d1d277'; ctx.textAlign = 'center'; ctx.fillText('THE MOON', center.x, center.y + 4); ctx.textAlign = 'left';
    ctx.beginPath(); ctx.arc(center.x, center.y, Math.hypot(initial.x, initial.y) * viewScale, 0, Math.PI * 2); ctx.setLineDash([2, 7]); ctx.strokeStyle = '#748d9d40'; ctx.stroke(); ctx.setLineDash([]);
  }
  function drawStation() {
    const p = screen(config.target.x, config.target.y);
    ctx.save(); ctx.translate(p.x, p.y);
    const r = Math.max(19, 12 * viewScale);
    ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.strokeStyle = '#8edfe264'; ctx.setLineDash([3, 4]); ctx.lineWidth = 1; ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = '#233e59'; ctx.strokeStyle = '#657c91';
    [-1, 1].forEach(side => { ctx.fillRect(side * 20 - 8, -17, 15, 35); ctx.strokeRect(side * 20 - 8, -17, 15, 35); });
    ctx.fillStyle = '#a9b6bd'; ctx.fillRect(-22, -2, 44, 4); ctx.fillRect(-5, -12, 10, 24);
    ctx.beginPath(); ctx.arc(0, 0, 6, 0, Math.PI * 2); ctx.fillStyle = '#e1e8eb'; ctx.fill();
    ctx.font = '8px monospace'; ctx.fillStyle = '#9abac8'; ctx.textAlign = 'center'; ctx.fillText('RENDEZVOUS TARGET', 0, -32); ctx.restore();
  }
  function drawCraft(shown, color, ghost = false) {
    const p = screen(shown.x, shown.y), stats = P.metrics(config, shown);
    const g = P.gravity(config, shown.x, shown.y);
    const orientation = shown.thrust > .001 ? Math.atan2(-(shown.ay - g.y), shown.ax - g.x) : stats.speed > .2 ? Math.atan2(-shown.vy, shown.vx) : 0;
    ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(orientation);
    if (shown.thrust > .001 && !ghost) { ctx.beginPath(); ctx.moveTo(-7, -4); ctx.lineTo(-20 - Math.min(12, shown.thrust * 2), 0); ctx.lineTo(-7, 4); ctx.fillStyle = '#fa754c'; ctx.fill(); }
    ctx.beginPath(); ctx.moveTo(13, 0); ctx.lineTo(-9, -7); ctx.lineTo(-5, 0); ctx.lineTo(-9, 7); ctx.closePath();
    ctx.fillStyle = ghost ? '#f65c3525' : '#e5eef0'; ctx.fill(); ctx.lineWidth = 1.3; ctx.strokeStyle = ghost ? color : '#a7d3de'; ctx.stroke();
    if (!ghost) { ctx.fillStyle = '#2c7d93'; ctx.fillRect(-2, -2, 5, 4); }
    ctx.restore();
    if (ghost) { ctx.font = '8px monospace'; ctx.fillStyle = color; ctx.fillText('WHAT IF', p.x + 14, p.y + 15); return; }
    if ($('show-vectors').checked) {
      const vScale = config.gravity ? .045 : 3.7;
      const vLength = Math.hypot(shown.vx, shown.vy) * vScale;
      const cap = vLength > 105 ? 105 / vLength : 1;
      arrow(p.x, p.y, shown.vx * vScale * cap, -shown.vy * vScale * cap, '#8edfe2', 'v');
      if (config.gravity) { const g = P.gravity(config, shown.x, shown.y); arrow(p.x, p.y, g.x * 35, -g.y * 35, '#8faff4', 'g'); }
      else if (shown.thrust > .01) arrow(p.x, p.y, shown.ax * 14, -shown.ay * 14, '#f98c68', 'a');
    }
    ctx.fillStyle = '#7fabbc'; ctx.font = '7px monospace'; ctx.fillText('OL-01', p.x - 14, p.y + 22);
  }
  function render() {
    if (!ctx) return;
    ctx.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0); ctx.clearRect(0, 0, width, height);
    const gradient = ctx.createRadialGradient(width * .62, height * .4, 0, width * .5, height * .5, width * .7);
    gradient.addColorStop(0, '#102131'); gradient.addColorStop(1, '#080f18'); ctx.fillStyle = gradient; ctx.fillRect(0, 0, width, height);
    stars.forEach(s => { ctx.fillStyle = `rgba(174,201,215,${s.a})`; ctx.fillRect(s.x * width, s.y * height, s.a > .4 ? 1.5 : 1, s.a > .4 ? 1.5 : 1); });
    ctx.lineWidth = .6; ctx.strokeStyle = '#7696ac13';
    for (let x = width % 50 / 2; x < width; x += 50) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke(); }
    for (let y = height % 50 / 2; y < height; y += 50) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke(); }
    calculateView();
    if (config.gravity) drawMoon();
    if (config.target) drawStation();
    const shown = displayState(), time = shown.t;
    pathLine(trace, time, '#81dbe0');
    if (phase === 'complete' && branch.length) { pathLine(branch, time, '#f28b65', true); drawCraft(sampleAt(branch, time), '#f28b65', true); }
    if (!config.gravity) {
      const p = screen(initial.x, initial.y); ctx.strokeStyle = '#819caa60'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(p.x - 5, p.y); ctx.lineTo(p.x + 5, p.y); ctx.moveTo(p.x, p.y - 5); ctx.lineTo(p.x, p.y + 5); ctx.stroke();
      ctx.fillStyle = '#688b9c'; ctx.font = '7px monospace'; ctx.fillText('START', p.x - 10, p.y - 13);
    }
    drawCraft(shown, '#8edfe2');
    if ($('show-vectors').checked) {
      ctx.font = '7px monospace'; ctx.fillStyle = '#9ab9c8';
      ctx.fillText(config.gravity ? 'v  VELOCITY     g  GRAVITY' : 'v  VELOCITY     a  THRUST', 23, 81);
    }
    const scaleDistance = 58 / viewScale;
    text('scale-label', config.gravity ? `${Math.round(scaleDistance / 1000)} km` : `${Math.round(scaleDistance)} m`);
  }
  function frame(now) {
    const elapsed = lastFrame ? Math.min((now - lastFrame) / 1000, .1) : 0; lastFrame = now;
    if (phase === 'running') {
      simAccumulator += elapsed;
      while (simAccumulator >= 1 / 60 && phase === 'running') {
        currentControl = guided ? P.demoControl(config, state) : userControl();
        const dt = Math.min(config.timeScale / 60, config.duration - state.t);
        if (dt <= 1e-8) { finishFlight('completed'); break; }
        state = P.step(config, state, currentControl, dt);
        sampleCounter++;
        if (sampleCounter % 6 === 0) trace.push({ ...state });
        simAccumulator -= 1 / 60;
        if (state.impact) finishFlight('impact');
        else if (P.metrics(config, state).docked) finishFlight('docked');
        else if (state.t >= config.duration - 1e-8) finishFlight('completed');
      }
    }
    if (phase === 'complete' && replayPlaying) {
      // Full trace replay lasts up to 14 real seconds, regardless of orbital time scale.
      replayClock += elapsed * Math.max(1, state.t / 14);
      replayIndex = state.t > 0 ? Math.min(1, replayClock / state.t) : 1;
      $('replay-scrub').value = String(Math.round(replayIndex * 1000));
      if (replayIndex >= 1) { replayPlaying = false; text('replay-toggle', '▶ Replay'); }
    }
    if (visible && (phase === 'running' || replayPlaying || now - lastUiTime > 160)) render();
    if (now - lastUiTime > 100) { updateUI(); lastUiTime = now; }
    requestAnimationFrame(frame);
  }
  if ('ResizeObserver' in window) new ResizeObserver(resize).observe(canvas); else window.addEventListener('resize', resize);
  if ('IntersectionObserver' in window) new IntersectionObserver(entries => { visible = entries[0].isIntersecting; if (visible) render(); }, { threshold: 0 }).observe(canvas);
  moon.addEventListener('load', render);
  const articles = {
    inertia: `<p class="eyebrow">FLIGHT NOTES / NEWTON'S FIRST LAW</p><h2 id="dialog-title">The engine changes motion.<br>It doesn't sustain it.</h2><p>On Earth, a bicycle slows down when you stop pedaling because air resistance and friction exert forces. That everyday experience can make it seem as though motion always needs a continuous push.</p><p>In an ideal force-free region, a spacecraft maintains a constant velocity. A short engine burn changes that velocity. Switching the engine off removes the thrust; it does not erase the velocity already gained.</p><div class="formula">No net force → constant velocity</div><p>In our first mission, gravity and drag are deliberately omitted so you can isolate this idea. In a real orbit, gravity is present even when the thruster is off.</p><p><a href="https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/newtons-laws-of-motion/" target="_blank" rel="noopener noreferrer">Explore Newton's laws with NASA ↗</a></p><button class="button button-orange" data-dialog-mission="coast">Try thrust & coast <svg class="icon"><use href="#i-arrow"/></svg></button>`,
    weightless: `<p class="eyebrow">FLIGHT NOTES / GRAVITY & WEIGHTLESSNESS</p><h2 id="dialog-title">Falling together.<br>Floating relative to each other.</h2><p>Gravity is still acting on an orbiting spacecraft. It continuously bends the path inward. The spacecraft and a freely floating astronaut both follow approximately the same falling trajectory.</p><p>On the ground, a floor pushes up on you. In ideal orbital free fall, that supporting force is absent. This is why you can feel weightless even while gravity accelerates you.</p><div class="note-box"><p><strong>Zero support force does not mean zero gravitational field.</strong> Our third mission displays gravitational acceleration separately from the engine's acceleration.</p></div><p>The lab is a visual simulation. It does not physically remove gravity or reproduce vestibular sensations. A real thruster burn would make a supported occupant feel acceleration again.</p><p><a href="https://www.nasa.gov/learning-resources/for-kids-and-students/what-is-microgravity-grades-5-8/" target="_blank" rel="noopener noreferrer">Read NASA's introduction to microgravity ↗</a></p><button class="button button-orange" data-dialog-mission="orbit">Explore an orbit <svg class="icon"><use href="#i-arrow"/></svg></button>`,
    replay: `<p class="eyebrow">FLIGHT NOTES / COUNTERFACTUAL REPLAY</p><h2 id="dialog-title">A different decision.<br>The same starting point.</h2><p>After a flight, the lab runs a second simulation. It uses the same initial position, velocity, fuel budget, physical model, and elapsed time. Only the control policy changes.</p><ul><li><strong>Thrust & coast:</strong> compare your commands with continuous rightward thrust.</li><li><strong>Rendezvous:</strong> compare your commands with no thrust at all.</li><li><strong>Orbit:</strong> compare your commands with an initial 300-second burn along the direction of motion, then coasting.</li></ul><p>The cyan path is your recorded flight. The dashed orange path is the alternate simulation. Scrub the timeline to compare equal moments in simulated time, or download both traces as JSON.</p><div class="note-box"><p>The feedback follows explicit rules and your selected prediction. It is not an AI diagnosis. Whether this approach improves learning is a research question for a future user study.</p></div><button class="button button-orange" data-dialog-mission="coast">Create your first replay <svg class="icon"><use href="#i-arrow"/></svg></button>`
  };
  function bindDialogMission() {
    dialog.querySelectorAll('[data-dialog-mission]').forEach(button => button.addEventListener('click', () => {
      dialog.close(); selectMission(button.dataset.dialogMission); $('flight-lab').scrollIntoView({ behavior: 'smooth' });
    }));
  }
  document.querySelectorAll('[data-article]').forEach(button => button.addEventListener('click', () => { openDialog(articles[button.dataset.article]); bindDialogMission(); }));
  $('controls-help').addEventListener('click', () => openDialog(`<p class="eyebrow">PILOT HANDBOOK / QUICK START</p><h2 id="dialog-title">A few controls.<br>A universe to explore.</h2><ol><li>Choose one of the three missions.</li><li>Select <strong>Make a prediction</strong> and choose an answer. Or use <strong>Watch a guided flight</strong> to see an example.</li><li>Hold <strong>WASD or the arrow keys</strong> to apply directional thrust. On a phone, hold the on-screen arrows.</li><li>Release to coast. These are direct directional thrusters, not rotation controls. Up is +Y in the displayed inertial frame.</li><li>Press <strong>Space</strong> while the canvas has focus to pause. Use the toolbar to resume, reset, or end a flight.</li><li>At the end, scrub or play the replay. Export both trajectories with <strong>Download flight data</strong>.</li></ol><p>In the orbit mission, time runs at 240×. Vector arrows are illustrative, capped for readability, and use separate scales for velocity and acceleration. The spacecraft and station icons are not drawn to physical scale.</p><p class="dialog-muted">Switching away from this tab pauses the flight. Your session is kept in memory only. Download the JSON before refreshing if you want to keep it.</p>`));
  $('about-project').addEventListener('click', () => openDialog(`<p class="eyebrow">ORBITAL LAB / PROJECT NOTES</p><h2 id="dialog-title">An idea you can fly.</h2><p>This independent capstone prototype explores prediction-driven spaceflight learning and counterfactual replay. It includes three two-dimensional missions, live telemetry, explicit rule-based feedback, and exportable flight traces.</p><h3>The model</h3><p>The first two missions use a gravity-free local inertial frame, with constant spacecraft mass and no drag. The lunar mission uses a spherical Moon and central gravity, integrated with velocity Verlet. It omits third-body gravity, terrain, collisions between craft, navigation errors, and real propulsion dynamics.</p><h3>A three-part capstone</h3><ol><li><strong>Learning & research:</strong> misconception questions, tutor rules, literature review, and study design.</li><li><strong>Simulation & validation:</strong> physics, mission conditions, trace recording, and numerical checks.</li><li><strong>Experience & delivery:</strong> interface, interaction, accessibility, packaging, and demo presentation.</li></ol><p>The shipped site is a working demonstration. Research novelty, real-world flight accuracy, and learning effectiveness have not been established.</p><h3>Image credits</h3><ul><li><a href="https://science.nasa.gov/resource/apollo-8s-iconic-earthrise/" target="_blank" rel="noopener noreferrer">Earthrise — NASA / Bill Anders, Apollo 8</a></li><li><a href="https://www.nasa.gov/image-article/apollo-17-astronauts-capture-iconic-blue-marble-50-years-ago/" target="_blank" rel="noopener noreferrer">Blue Marble — NASA, Apollo 17</a></li><li><a href="https://svs.gsfc.nasa.gov/4720/" target="_blank" rel="noopener noreferrer">Lunar texture — NASA's Scientific Visualization Studio</a>, LROC / LOLA teams</li></ul><p>NASA-inspired editorial design, original Orbital Lab branding. This project is not affiliated with or endorsed by NASA. All application assets are bundled for offline use; source links need an internet connection.</p>`));
  if (!ctx) { text('tutor-message', 'This browser does not support a 2D canvas. Please open the project in a current desktop or mobile browser.'); $('start-flight').disabled = true; $('demo-flight').disabled = true; return; }
  selectMission('coast'); resize(); requestAnimationFrame(frame);
})();
