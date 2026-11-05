/* UI-only browser checks. Mock API replies below are fixtures, not model evidence. */
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');

const out = __dirname;
const base = process.argv[2] || 'http://127.0.0.1:8000/';
const port = 9323;
const chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const profile = path.join(out, `chromium-profile-${Date.now()}`);
const child = spawn(chrome, [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--disable-background-networking',
  '--disable-component-update', '--disable-extensions', '--no-first-run',
  '--no-default-browser-check', '--disable-sync', '--hide-scrollbars',
  `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, 'about:blank'
], { windowsHide: true, stdio: 'ignore' });

let socket;
let id = 0;
const pending = new Map();
const failures = [];
const checks = [];
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
function check(name, ok, details = null) {
  checks.push({ name, passed: !!ok, details });
  if (!ok) failures.push(name);
}
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

(async () => {
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
  await wait(400);
  const initial = await evaluate(`({
    title: document.title,
    greeting: document.querySelector('.message-text')?.textContent,
    rows: document.querySelectorAll('.message-row').length,
    logoLoaded: document.querySelector('.brand-logo')?.naturalWidth,
    sidebarWidth: document.querySelector('.sidebar').getBoundingClientRect().width,
    appWidth: document.querySelector('.chat-app').getBoundingClientRect().width,
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: innerWidth,
    status: document.querySelector('#connection-status').hidden ? null : document.querySelector('#connection-status').textContent
  })`);
  check('title_and_greeting_match_report', initial.title === 'Hỗ trợ tâm lý' && initial.greeting === 'Chào bạn! Hôm nay bạn cảm thấy thế nào? Cứ thoải mái chia sẻ với mình nhé.', initial);
  check('initial_page_has_no_fabricated_conversation', initial.rows === 1);
  check('logo_loaded_and_sidebar_is_20_percent', initial.logoLoaded === 45 && Math.abs(initial.sidebarWidth / (initial.appWidth - 2) - .2) < .002);
  check('desktop_has_no_horizontal_overflow', initial.scrollWidth === initial.viewportWidth);
  await screenshot('ui_restored_desktop_initial.png');

  await call('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  const mobile = await evaluate(`({
    scrollWidth: document.documentElement.scrollWidth,
    viewportWidth: innerWidth,
    inputWidth: document.querySelector('#message-input').getBoundingClientRect().width,
    buttonRight: document.querySelector('#send-button').getBoundingClientRect().right,
    composerBottom: document.querySelector('.composer').getBoundingClientRect().bottom,
    height: innerHeight
  })`);
  check('mobile_composer_visible_without_horizontal_overflow', mobile.scrollWidth === mobile.viewportWidth && mobile.inputWidth > 100 && mobile.buttonRight <= mobile.viewportWidth && mobile.composerBottom <= mobile.height, mobile);
  await screenshot('ui_restored_mobile_initial.png');
  await call('Emulation.setDeviceMetricsOverride', { width: 1919, height: 929, deviceScaleFactor: 1, mobile: false });

  // Explicitly labelled local fixtures verify rendering and request/session behavior.
  // No POST reaches /chatbot and no model/provider request is made by these checks.
  await evaluate(`window.__uiRequests = []; window.__uiFixtureStep = 0;
    window.__originalFetch = window.fetch;
    window.fetch = async (url, options) => {
      if (url !== '/chatbot') return window.__originalFetch(url, options);
      window.__uiRequests.push(JSON.parse(options.body));
      await new Promise(resolve => setTimeout(resolve, 100));
      const step = ++window.__uiFixtureStep;
      if (step === 3) throw new Error('UI_FIXTURE_NETWORK_FAILURE');
      if (step === 4) return new Response(JSON.stringify({ status:'error', code:'UPSTREAM_QUOTA', trace_id:'UI-FIXTURE-QUOTA', usage:{} }), {status:429, headers:{'Content-Type':'application/json'}});
      return new Response(JSON.stringify({ response:'UI FIXTURE ' + step + ' <img src=x onerror=alert(1)>', status:'ok', code:'OK', trace_id:'UI-FIXTURE-' + step, model_id:'fixture:ui-only', usage:{}, sources:[{title:'UI fixture source',url:'javascript:alert(1)',quote:'<script>not executable</script>'},{title:'Valid URL fixture',url:'https://example.com/source',retrieved_at:'2026-11-05T00:00:00Z'}] }), {status:200, headers:{'Content-Type':'application/json'}});
    };`);
  await evaluate(`document.querySelector('#message-input').value = 'UI FIXTURE question 1'; document.querySelector('#chat-form').requestSubmit();`);
  const loading = await evaluate(`({ disabled:document.querySelector('#send-button').disabled, pending:document.querySelectorAll('.pending').length })`);
  check('loading_disables_duplicate_send', loading.disabled && loading.pending === 1);
  await wait(250);
  await evaluate(`document.querySelector('#message-input').value = 'UI FIXTURE question 2'; document.querySelector('#message-input').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));`);
  await wait(250);
  const twoTurns = await evaluate(`({
    requests:window.__uiRequests,
    rows:document.querySelectorAll('.message-row').length,
    unsafeLink:!!document.querySelector('a[href^="javascript:"]'),
    sourceLinks:Array.from(document.querySelectorAll('.source-title[href]')).map(a=>({href:a.href,rel:a.rel})),
    executedMarkup:document.querySelectorAll('.bubble img, .bubble script').length,
    evidence:document.querySelectorAll('.response-details').length,
    pending:document.querySelectorAll('.pending').length,
    enabled:!document.querySelector('#send-button').disabled
  })`);
  check('two_turns_keep_same_backend_session', twoTurns.requests.length === 2 && twoTurns.requests[0].session_id === twoTurns.requests[1].session_id && twoTurns.requests[0].user_id === twoTurns.requests[1].user_id && twoTurns.requests.every(r => r.mode === 'auto' && r.use_cache === false));
  check('conversation_shows_both_turns_and_releases_loading', twoTurns.rows === 5 && twoTurns.evidence === 2 && !twoTurns.pending && twoTurns.enabled);
  check('untrusted_response_and_sources_are_not_executable', !twoTurns.unsafeLink && !twoTurns.executedMarkup && twoTurns.sourceLinks.length === 2 && twoTurns.sourceLinks.every(a => a.href === 'https://example.com/source' && a.rel.includes('noopener')), twoTurns);
  await evaluate(`document.querySelector('#message-input').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',shiftKey:true,bubbles:true,cancelable:true}));`);
  check('shift_enter_does_not_submit', await evaluate('window.__uiRequests.length === 2'));
  for (const n of [3, 4]) {
    await evaluate(`document.querySelector('#message-input').value = 'UI FIXTURE question ${n}'; document.querySelector('#chat-form').requestSubmit();`);
    await wait(250);
  }
  check('network_and_http_error_remain_visible_with_retry_enabled', await evaluate(`document.querySelectorAll('.message-row.error').length === 2 && !document.querySelector('#send-button').disabled && document.querySelectorAll('.pending').length === 0`));
  const sessionBeforeReload = await evaluate('window.__uiRequests[0].session_id');
  await call('Page.reload');
  await wait(500);
  check('reload_restores_same_session_and_visible_history', await evaluate(`document.querySelector('#conversation-id').textContent === ${JSON.stringify(sessionBeforeReload)} && document.querySelectorAll('.message-row').length === 9`));

  // Remove test data in this isolated browser and recapture only the real initial UI.
  await evaluate("sessionStorage.removeItem('sgu-chat-report-ui-v1')");
  await call('Page.reload');
  await wait(400);
  const report = { checked_at: new Date().toISOString(), base_url: base, provider_calls: 0, fixture_checks_only: true, screenshots: ['ui_restored_desktop_initial.png', 'ui_restored_mobile_initial.png'], checks, passed: failures.length === 0, failed: failures };
  fs.writeFileSync(path.join(out, 'ui_check_results.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ passed: report.passed, checks: checks.length, failed: failures, provider_calls: 0 }));
  await call('Browser.close');
  socket.close();
  process.exitCode = failures.length ? 1 : 0;
})().catch(error => {
  fs.writeFileSync(path.join(out, 'ui_check_error.txt'), String(error.stack || error));
  console.error(String(error));
  if (socket) socket.close();
  child.kill();
  process.exitCode = 1;
});
