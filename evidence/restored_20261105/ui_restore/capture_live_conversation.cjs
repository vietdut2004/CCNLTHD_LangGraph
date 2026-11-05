/* Three real UI requests. Run only after the final backend has been selected. */
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { spawn } = require('node:child_process');

if (!process.argv.includes('--run-live')) {
  console.error('This script calls the real configured API three times. Use --run-live after selecting the final backend.');
  process.exit(2);
}

const base = process.argv.find(arg => /^https?:\/\//.test(arg)) || 'http://127.0.0.1:8000/';
const delayMs = Number((process.argv.find(arg => arg.startsWith('--delay-ms=')) || '--delay-ms=0').split('=')[1]);
const out = path.join(__dirname, `live_conversation_${new Date().toISOString().replace(/[:.]/g, '-')}`);
fs.mkdirSync(out, { recursive: true });
const port = 9324;
const chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const child = spawn(chrome, [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--disable-background-networking',
  '--disable-component-update', '--disable-extensions', '--no-first-run',
  '--no-default-browser-check', '--disable-sync',
  `--remote-debugging-port=${port}`, `--user-data-dir=${path.join(out, 'chromium-profile')}`, 'about:blank'
], { windowsHide: true, stdio: 'ignore' });

let socket;
let id = 0;
const pending = new Map();
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const requestId = ++id;
    pending.set(requestId, { resolve, reject });
    socket.send(JSON.stringify({ id: requestId, method, params }));
  });
}
async function evaluate(expression) {
  const result = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function screenshot(name) {
  const result = await call('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(out, name), Buffer.from(result.data, 'base64'));
}
function writeRecords(records) {
  fs.writeFileSync(path.join(out, 'requests_responses.json'), JSON.stringify(records, null, 2));
  const fields = ['question','started_at_utc','finished_at_utc','http_status','status','code','route','trace_id','graph_id','model_id','latency_ms_browser','input_tokens','output_tokens','total_tokens','usage_complete','source_count','response'];
  const csvCell = value => value == null ? '' : '"' + String(value).replaceAll('"', '""') + '"';
  const lines = [fields.join(',')];
  for (const row of records) {
    const result = row.response || {};
    const tokens = result.usage?.usage_complete === true ? (result.usage.observed_tokens || {}) : {};
    const values = {
      question:row.request.question, started_at_utc:row.started_at, finished_at_utc:row.finished_at,
      http_status:row.http_status, status:result.status, code:result.code, route:result.route,
      trace_id:result.trace_id, graph_id:result.graph_id, model_id:result.model_id,
      latency_ms_browser:row.latency_ms_browser, input_tokens:tokens.input_tokens,
      output_tokens:tokens.output_tokens, total_tokens:tokens.total_tokens,
      usage_complete:result.usage?.usage_complete,
      source_count:Array.isArray(result.sources) ? result.sources.length : 0, response:result.response
    };
    lines.push(fields.map(field => csvCell(values[field])).join(','));
  }
  fs.writeFileSync(path.join(out, 'LIVE_RESULTS.csv'), '\ufeff' + lines.join('\r\n') + '\r\n');
}
const questions = [
  'bạn cho mình biết ý nghĩa của hít thở sâu là gì',
  'bạn có khỏe kh',
  'bạn gợi ý cho tôi vài bộ phim truyền động lực sống được kh'
];

(async () => {
  const healthResponse = await fetch(new URL('/health', base));
  const health = await healthResponse.json();
  fs.writeFileSync(path.join(out, 'health_before.json'), JSON.stringify(health, null, 2));
  if (!healthResponse.ok || !health.configured || health.fixture) throw new Error('Real configured API required; fixture/unconfigured API will not be used.');
  const frontendHashes = [];
  for (const asset of ['/', '/frontend/style.css', '/frontend/app.js', '/frontend/assets/sgu-report.png']) {
    const response = await fetch(new URL(asset, base));
    const bytes = Buffer.from(await response.arrayBuffer());
    frontendHashes.push({ path:asset, http_status:response.status, bytes:bytes.length, sha256:createHash('sha256').update(bytes).digest('hex') });
  }
  fs.writeFileSync(path.join(out, 'frontend_http_hashes.json'), JSON.stringify(frontendHashes, null, 2));
  for (let n = 0; n < 80; n++) {
    try { await fetch(`http://127.0.0.1:${port}/json/version`); break; } catch { await wait(100); }
  }
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  socket.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) reject(new Error(JSON.stringify(message.error)));
      else resolve(message.result);
    }
  });
  await new Promise(resolve => socket.addEventListener('open', resolve, { once: true }));
  await call('Page.enable');
  await call('Runtime.enable');
  await call('Emulation.setDeviceMetricsOverride', { width: 1919, height: 929, deviceScaleFactor: 1, mobile: false });
  await call('Page.navigate', { url: base });
  for (let n = 0; n < 50; n++) {
    if (await evaluate("!!document.querySelector('#conversation-id')?.textContent")) break;
    await wait(100);
  }
  // Observe and clone actual HTTP requests/responses; forward them unchanged.
  // This wrapper contains no fixture response and no reference answer.
  await evaluate(`window.__liveRecords = [];
    window.__realFetch = window.fetch;
    window.fetch = async (url, options) => {
      if (url !== '/chatbot') return window.__realFetch(url, options);
      const startedAt = new Date().toISOString();
      const started = performance.now();
      const record = {started_at:startedAt,request:JSON.parse(options.body),fixture:false};
      try {
        const response = await window.__realFetch(url, options);
        record.http_status = response.status;
        record.headers = { 'content-type':response.headers.get('Content-Type'), 'x-trace-id':response.headers.get('X-Trace-ID') };
        record.response_body = await response.clone().text();
        try { record.response = JSON.parse(record.response_body); } catch {}
        record.latency_ms_browser = Math.round(performance.now()-started);
        record.finished_at = new Date().toISOString();
        window.__liveRecords.push(record);
        return response;
      } catch (error) {
        record.network_error = String(error);
        record.latency_ms_browser = Math.round(performance.now()-started);
        record.finished_at = new Date().toISOString();
        window.__liveRecords.push(record);
        throw error;
      }
    };`);

  for (let index = 0; index < questions.length; index++) {
    if (index && delayMs > 0) await wait(delayMs);
    await evaluate(`document.querySelector('#message-input').value = ${JSON.stringify(questions[index])}; document.querySelector('#chat-form').requestSubmit();`);
    let completed = false;
    for (let n = 0; n < 900; n++) {
      if (await evaluate(`window.__liveRecords.length >= ${index + 1} && !document.querySelector('#send-button').disabled`)) { completed = true; break; }
      await wait(100);
    }
    const records = await evaluate('window.__liveRecords');
    writeRecords(records);
    if (!completed) throw new Error(`UI request ${index + 1} did not finish within 90 seconds.`);
    await screenshot(`turn_${index + 1}_actual.png`);
    const r = records[index];
    console.log(JSON.stringify({ turn:index + 1, http_status:r.http_status, status:r.response?.status, route:r.response?.route, trace_id:r.response?.trace_id, model_id:r.response?.model_id, latency_ms_browser:r.latency_ms_browser }));
    if ([401, 403, 429].includes(r.http_status) || ['UPSTREAM_AUTH', 'UPSTREAM_QUOTA', 'CONFIG_GROQ_MISSING'].includes(r.response?.code)) {
      fs.writeFileSync(path.join(out, 'STOPPED_LIVE.json'), JSON.stringify({ stopped_at:new Date().toISOString(), reason:'Authentication or quota error; no retry and no further provider requests.', failed_turn:index + 1, result:r }, null, 2));
      throw new Error(`Stopped after authentication/quota failure on turn ${index + 1}; raw response retained.`);
    }
  }

  await screenshot('conversation_actual.png');
  // One uncropped screenshot of every visible bubble, keeping real response text.
  // Increase only the viewport height; do not inject or replace conversation content.
  const fullHeight = await evaluate('document.querySelector("#messages").scrollHeight + 230');
  await call('Emulation.setDeviceMetricsOverride', { width: 1919, height: Math.max(929, Math.min(fullHeight, 12000)), deviceScaleFactor: 1, mobile: false });
  await evaluate('document.querySelector("#messages").scrollTop = 0');
  await wait(200);
  await screenshot('conversation_actual_full.png');
  const records = await evaluate('window.__liveRecords');
  const summary = {
    captured_at:new Date().toISOString(), base_url:base, fixture:false,
    note:'Three questions copied from the historical report screenshot. Answers are new actual API responses. HTTP success is not a content-quality score.',
    health_before:health,
    questions,
    turns:records.length,
    results:records.map((r,i)=>({question:questions[i],http_status:r.http_status,status:r.response?.status,code:r.response?.code,route:r.response?.route,trace_id:r.response?.trace_id,model_id:r.response?.model_id,graph_id:r.response?.graph_id,latency_ms_browser:r.latency_ms_browser,usage:r.response?.usage ?? null,sources:r.response?.sources ?? [],network_error:r.network_error ?? null}))
  };
  fs.writeFileSync(path.join(out, 'LIVE_CAPTURE_REPORT.json'), JSON.stringify(summary, null, 2));
  console.log(`Evidence: ${out}`);
  await call('Browser.close');
  socket.close();
})().catch(error => {
  fs.writeFileSync(path.join(out, 'CAPTURE_ERROR.txt'), String(error.stack || error));
  console.error(String(error));
  if (socket) socket.close();
  child.kill();
  process.exitCode = 1;
});
