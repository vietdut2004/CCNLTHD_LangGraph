'use strict';

(() => {
  const STORAGE_KEY = 'sgu-chat-report-ui-v1';
  const greeting = 'Chào bạn! Hôm nay bạn cảm thấy thế nào? Cứ thoải mái chia sẻ với mình nhé.';
  const messages = document.getElementById('messages');
  const input = document.getElementById('message-input');
  const sendButton = document.getElementById('send-button');
  const connectionStatus = document.getElementById('connection-status');
  let sending = false;

  function randomId() {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  }

  function readConversation() {
    try {
      const stored = JSON.parse(sessionStorage.getItem(STORAGE_KEY));
      if (stored && typeof stored.userId === 'string' && typeof stored.sessionId === 'string' && Array.isArray(stored.turns)) {
        return stored;
      }
    } catch { /* A blocked or full browser store must not prevent chatting. */ }
    return { userId: `browser-${randomId()}`, sessionId: randomId(), turns: [] };
  }

  const conversation = readConversation();
  document.getElementById('conversation-id').textContent = conversation.sessionId;

  function saveConversation() {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(conversation)); }
    catch { /* Keep the current in-memory conversation when browser storage is unavailable. */ }
  }

  function scrollToLatest() { messages.scrollTop = messages.scrollHeight; }

  function safeUrl(value) {
    if (typeof value !== 'string') return null;
    try {
      const url = new URL(value);
      return ['https:', 'http:'].includes(url.protocol) ? url.href : null;
    } catch { return null; }
  }

  function showEvidence(bubble, result, httpStatus, elapsedMs) {
    const sources = Array.isArray(result.sources) ? result.sources : [];
    if (!sources.length && !result.trace_id && !result.code) return;
    const details = document.createElement('details');
    details.className = 'response-details';
    const summary = document.createElement('summary');
    summary.textContent = sources.length ? `Nguồn tham khảo (${sources.length}) · Chi tiết` : 'Chi tiết phản hồi';
    details.append(summary);

    if (sources.length) {
      const list = document.createElement('ol');
      list.className = 'source-list';
      for (const source of sources) {
        if (!source || typeof source !== 'object') continue;
        const item = document.createElement('li');
        const title = [source.title || source.id || 'Nguồn', source.page ? `trang ${source.page}` : null].filter(Boolean).join(' · ');
        const url = safeUrl(source.url);
        const label = document.createElement(url ? 'a' : 'span');
        label.className = 'source-title';
        label.textContent = title;
        if (url) {
          label.href = url;
          label.target = '_blank';
          label.rel = 'noopener noreferrer';
        }
        item.append(label);
        if (typeof source.quote === 'string' && source.quote) {
          const quote = document.createElement('blockquote');
          quote.className = 'source-quote';
          quote.textContent = source.quote;
          item.append(quote);
        }
        if (typeof source.retrieved_at === 'string' && source.retrieved_at) {
          const time = document.createElement('div');
          time.className = 'source-time';
          time.textContent = `Truy xuất: ${source.retrieved_at}`;
          item.append(time);
        }
        list.append(item);
      }
      details.append(list);
    }

    const trace = document.createElement('pre');
    trace.className = 'trace-data';
    trace.textContent = JSON.stringify({
      http_status: httpStatus,
      status: result.status ?? null,
      code: result.code ?? null,
      trace_id: result.trace_id ?? null,
      route: result.route ?? null,
      model_id: result.model_id ?? null,
      graph_id: result.graph_id ?? null,
      latency_ms_browser: elapsedMs,
      usage: result.usage ?? null
    }, null, 2);
    details.append(trace);
    bubble.append(details);
  }

  function appendMessage(turn) {
    const row = document.createElement('div');
    row.className = `message-row ${turn.role === 'user' ? 'user' : 'assistant'}${turn.error ? ' error' : ''}${turn.pending ? ' pending' : ''}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    const text = document.createElement('p');
    text.className = 'message-text';
    text.textContent = turn.text;
    bubble.append(text);
    if (turn.result) showEvidence(bubble, turn.result, turn.httpStatus, turn.elapsedMs);
    row.append(bubble);
    messages.append(row);
    scrollToLatest();
    return row;
  }

  function errorText(code) {
    const descriptions = {
      CONFIG_GROQ_MISSING: 'Chưa cấu hình khóa API cho chatbot. Bạn hãy kiểm tra cấu hình trên máy chạy rồi thử lại.',
      CONFIG_TAVILY_MISSING: 'Chưa cấu hình tìm kiếm web. Bạn hãy kiểm tra khóa Tavily trên máy chạy rồi thử lại.',
      UPSTREAM_AUTH: 'Dịch vụ tạo câu trả lời chưa xác thực được. Bạn hãy kiểm tra khóa API trên máy chạy.',
      UPSTREAM_QUOTA: 'Dịch vụ đang giới hạn lượt sử dụng. Bạn đợi một lát rồi gửi lại nhé.',
      UPSTREAM_TIMEOUT: 'Chatbot mất nhiều thời gian hơn dự kiến. Bạn có thể thử gửi lại câu hỏi.',
      RAG_SOURCE_MISSING: 'Chưa tìm thấy tài liệu trên máy chạy. Bạn hãy kiểm tra lại tệp PDF.',
      INVALID_REQUEST: 'Câu hỏi chưa hợp lệ. Bạn kiểm tra lại nội dung rồi gửi lại nhé.',
      SESSION_LIMIT: 'Máy chạy đang có nhiều phiên trò chuyện. Bạn hãy khởi động lại ứng dụng rồi thử lại.'
    };
    return descriptions[code] || 'Mình chưa nhận được câu trả lời từ dịch vụ. Bạn thử lại sau nhé.';
  }

  appendMessage({ role: 'assistant', text: greeting });
  for (const turn of conversation.turns) {
    if (turn && ['user', 'assistant'].includes(turn.role) && typeof turn.text === 'string') appendMessage(turn);
  }
  saveConversation();

  fetch('/health').then(async response => {
    if (!response.ok) throw new Error('health');
    const health = await response.json();
    if (health.fixture) {
      connectionStatus.textContent = 'Đang chạy chế độ kiểm thử giả lập; phản hồi không phải kết quả model thật.';
      connectionStatus.hidden = false;
    } else if (!health.configured) {
      connectionStatus.textContent = 'Máy chạy chưa có khóa API. Bạn cần cấu hình trước khi trò chuyện.';
      connectionStatus.hidden = false;
    }
  }).catch(() => {
    connectionStatus.textContent = 'Chưa kết nối được máy chạy chatbot. Bạn kiểm tra lại chương trình nhé.';
    connectionStatus.hidden = false;
  });

  function resizeInput() {
    input.style.height = '46px';
    input.style.height = `${Math.min(Math.max(input.scrollHeight, 46), 160)}px`;
  }
  input.addEventListener('input', resizeInput);
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      if (!sending) document.getElementById('chat-form').requestSubmit();
    }
  });

  document.getElementById('chat-form').addEventListener('submit', async event => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question || sending) return;
    sending = true;
    sendButton.disabled = true;
    input.readOnly = true;
    const userTurn = { role: 'user', text: question };
    appendMessage(userTurn);
    conversation.turns.push(userTurn);
    saveConversation();
    input.value = '';
    resizeInput();
    const waiting = appendMessage({ role: 'assistant', text: 'Đang trả lời…', pending: true });
    const started = performance.now();
    let assistantTurn;
    try {
      const response = await fetch('/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          mode: 'auto',
          user_id: conversation.userId,
          session_id: conversation.sessionId,
          use_cache: false
        })
      });
      const result = await response.json();
      const failed = !response.ok || result.status === 'error';
      assistantTurn = {
        role: 'assistant',
        text: failed ? errorText(result.code) : (typeof result.response === 'string' && result.response.trim() ? result.response : 'Dịch vụ trả về phản hồi trống. Bạn thử lại nhé.'),
        error: failed,
        result,
        httpStatus: response.status,
        elapsedMs: Math.round(performance.now() - started)
      };
    } catch {
      assistantTurn = { role: 'assistant', text: 'Không kết nối được chatbot. Bạn kiểm tra chương trình đang chạy rồi thử lại nhé.', error: true };
    } finally {
      waiting.remove();
      appendMessage(assistantTurn);
      conversation.turns.push(assistantTurn);
      saveConversation();
      sending = false;
      sendButton.disabled = false;
      input.readOnly = false;
      input.focus();
    }
  });
})();
