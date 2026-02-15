#!/usr/bin/env node
/**
 * Test backend: login, fetch runs and report detail, validate data shape and content.
 * Usage:
 *   LOGIN_USER=youruser LOGIN_PASSWORD=yourpass node scripts/test-backend-data.mjs
 *   API_URL=http://localhost:8080 LOGIN_USER=u LOGIN_PASSWORD=p node scripts/test-backend-data.mjs
 */
const API_URL = process.env.API_URL || 'http://localhost:8080';

function log(msg) {
  console.log(msg);
}

async function request(method, path, body = null, token = null) {
  const url = `${API_URL.replace(/\/$/, '')}${path}`;
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (token) opts.headers.Authorization = `Bearer ${token}`;
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    throw new Error(`Invalid JSON: ${text.slice(0, 200)}`);
  }
  if (!res.ok) {
    const msg = data?.detail || data?.message || res.statusText;
    throw new Error(`HTTP ${res.status}: ${typeof msg === 'string' ? msg : JSON.stringify(msg)}`);
  }
  return data;
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function main() {
  const user = process.env.LOGIN_USER || process.env.TEST_USER;
  const pass = process.env.LOGIN_PASSWORD || process.env.TEST_PASSWORD;

  log('Backend data test');
  log(`API_URL=${API_URL}`);

  if (!user || !pass) {
    log('\nNo credentials. Set LOGIN_USER and LOGIN_PASSWORD (or TEST_USER, TEST_PASSWORD) to test with your account.');
    log('Example: LOGIN_USER=myuser LOGIN_PASSWORD=mypass node scripts/test-backend-data.mjs');
    process.exit(1);
  }

  let token;
  try {
    const loginRes = await request('POST', '/api/auth/login', { user_id: user, password: pass });
    assert(loginRes.token, 'Login response must include token');
    token = loginRes.token;
    log('Login: OK');
  } catch (e) {
    log(`Login failed: ${e.message}`);
    process.exit(1);
  }

  let runsRes;
  try {
    runsRes = await request('GET', '/api/runs?limit=5&offset=0', null, token);
    assert(Array.isArray(runsRes.runs), 'Response must have runs array');
    log(`Runs list: OK (total=${runsRes.total ?? '?'}, count=${runsRes.runs.length})`);
  } catch (e) {
    log(`Runs list failed: ${e.message}`);
    process.exit(1);
  }

  if (runsRes.runs.length === 0) {
    log('\nNo runs found. Create a report (New Report) then run this script again to validate report data.');
    process.exit(0);
  }

  const runId = runsRes.runs[0].run_id;
  if (!runId) {
    log('First run missing run_id');
    process.exit(1);
  }

  let detailRes;
  try {
    detailRes = await request('GET', `/api/runs/${encodeURIComponent(runId)}`, null, token);
    log(`Run detail (${runId}): OK`);
  } catch (e) {
    log(`Run detail failed: ${e.message}`);
    process.exit(1);
  }

  // Validate run detail shape
  assert(detailRes.run != null, 'Response must have run');
  assert(detailRes.run.run_id === runId, 'run.run_id must match');
  assert(typeof detailRes.run.user_id === 'string', 'run.user_id must be string');
  assert(Array.isArray(detailRes.dawairx_report), 'dawairx_report must be array');
  assert(Array.isArray(detailRes.dawairx_columns), 'dawairx_columns must be array');
  assert(typeof detailRes.dawairx_row_count === 'number', 'dawairx_row_count must be number');
  assert(typeof detailRes.is_no_data === 'boolean', 'is_no_data must be boolean');

  if (detailRes.dawairx_report.length > 0) {
    const first = detailRes.dawairx_report[0];
    const keys = Object.keys(first);
    const hasReportColumn = keys.some((k) => /NDC|DRUG NAME|medicine_key|TOTAL ORDERED|TOTAL BILLED/i.test(k));
    assert(hasReportColumn, 'First row should have at least one report column (NDC, DRUG NAME, medicine_key, TOTAL ORDERED-O, etc.)');
    assert(detailRes.dawairx_columns.length > 0, 'dawairx_columns should not be empty when report has rows');
    assert(detailRes.dawairx_row_count === detailRes.dawairx_report.length, 'dawairx_row_count should match report length');
    log(`Report data: OK (rows=${detailRes.dawairx_report.length}, columns=${detailRes.dawairx_columns.length})`);
    log(`Sample columns: ${detailRes.dawairx_columns.slice(0, 6).join(', ')}${detailRes.dawairx_columns.length > 6 ? '...' : ''}`);
  } else {
    log(`Report data: no rows (is_no_data=${detailRes.is_no_data}, dawairx_error=${detailRes.dawairx_error || 'none'})`);
  }

  log('\nAll checks passed. Backend data shape and content are correct.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
