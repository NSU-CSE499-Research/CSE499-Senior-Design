const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(root, 'styles.css'), 'utf8');
const js = fs.readFileSync(path.join(root, 'js/app.js'), 'utf8');
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
test('Document IDs are unique and section anchors and SVG references resolve', () => {
  assert.equal(new Set(ids).size, ids.length);
  for (const match of html.matchAll(/href="#([^"]+)"/g)) assert.ok(ids.includes(match[1]), `Missing target ${match[1]}`);
});
test('Every static script, style, and image is bundled locally', () => {
  for (const match of html.matchAll(/(?:src|href)="([^"#]+)"/g)) {
    if (/^(?:https?:|mailto:)/.test(match[1])) continue;
    assert.ok(fs.existsSync(path.join(root, match[1])), `Missing local file ${match[1]}`);
  }
  for (const match of css.matchAll(/url\((?:"([^"]*)"|'([^']*)'|([^)\s]+))\)/g)) {
    const asset = match[1] || match[2] || match[3];
    if (asset.startsWith('data:')) continue;
    assert.ok(fs.existsSync(path.join(root, asset)), `Missing CSS image ${asset}`);
  }
});
test('Static UI element lookups resolve to HTML or an explicitly created dialog element', () => {
  for (const match of js.matchAll(/\$\('([^']+)'\)/g)) assert.ok(ids.includes(match[1]) || match[1] === 'prediction-form', `Unresolved UI ID ${match[1]}`);
});
test('The application does not require external scripts, styles, fonts, or API requests', () => {
  assert.ok(!/<script[^>]+src="https?:/.test(html)); assert.ok(!/<link[^>]+href="https?:/.test(html));
  assert.ok(!/\bfetch\(|\bXMLHttpRequest|\bWebSocket/.test(js)); assert.ok(!/@import\s/.test(css));
});
