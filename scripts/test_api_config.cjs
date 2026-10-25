const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../tasks/api-config.js'), 'utf8');
for (const [protocol, hostname, expected] of [
  ['https:', 'russ.emiit.ru', 'https://russ.emiit.ru'],
  ['https:', 'localhost', 'https://russ.emiit.ru'],
  ['http:', '127.0.0.1', 'http://127.0.0.1:8888'],
  ['http:', 'example.com', 'http://127.0.0.1:8888'],
  ['file:', '', 'http://127.0.0.1:8888'],
]) {
  const window = { location: { protocol, hostname } };
  vm.runInNewContext(script, { window });
  assert.equal(window.ANALYZER_CONFIG.apiBaseUrl, expected);
}
console.log('API routing: 5 protocol/host scenarios passed.');
