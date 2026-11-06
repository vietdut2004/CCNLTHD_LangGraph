"use strict";

const messages = document.getElementById("messages");
const form = document.getElementById("chat-form");
const question = document.getElementById("question");
const send = document.getElementById("send");
const newChat = document.getElementById("new-chat");
const errorBox = document.getElementById("error");
const connection = document.getElementById("connection");
const activity = document.getElementById("activity");
const conversation = document.getElementById("conversation");
const STORAGE_KEY = "support-chat-thread";
const GREETING = "Chào bạn! Hôm nay bạn cảm thấy thế nào? Cứ thoải mái chia sẻ với mình nhé.";
let threadId = null;
let busy = false;

// Only the thread ID is stored in this tab. Message history belongs to LangGraph.
function savedThread() {
  try { return sessionStorage.getItem(STORAGE_KEY); } catch { return null; }
}
function saveThread(id) {
  try {
    if (id) sessionStorage.setItem(STORAGE_KEY, id);
    else sessionStorage.removeItem(STORAGE_KEY);
  } catch { /* The chat still works when browser storage is unavailable. */ }
}

function runErrorMessage(error) {
  // Agent Server reports the exception class separately from its raw message.
  // Never show the raw provider message: it can contain credentials or input.
  const type = error && typeof error === "object" ? error.error : null;
  switch (type) {
    case "APIConnectionError":
      return "Máy chủ không kết nối được dịch vụ AI. Hãy kiểm tra kết nối Internet của máy đang chạy chatbot rồi thử lại.";
    case "APITimeoutError":
    case "TimeoutError":
      return "Dịch vụ AI phản hồi quá thời gian chờ. Vui lòng thử lại sau.";
    case "AuthenticationError":
    case "PermissionDeniedError":
      return "Chưa xác thực được quyền truy cập dịch vụ AI. Hãy kiểm tra GROQ_API_KEY và quyền truy cập mô hình trong file .env.";
    case "RateLimitError":
      return "Dịch vụ AI đã chạm giới hạn sử dụng. Vui lòng đợi hạn mức được khôi phục hoặc kiểm tra hạn mức tài khoản Groq.";
    default:
      return "Trợ lý chưa thể trả lời. Hãy kiểm tra cấu hình dịch vụ hoặc thử lại sau.";
  }
}

async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const error = new Error(response.status === 404
      ? "Cuộc trò chuyện không còn tồn tại. Hãy tạo cuộc trò chuyện mới."
      : "Chưa thể xử lý yêu cầu. Vui lòng thử lại sau.");
    error.status = response.status;
    throw error;
  }
  const data = await response.json();
  if (data.__error__) throw new Error(runErrorMessage(data.__error__));
  return data;
}

function contentText(content) {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";
  return content.filter(block => block.type === "text").map(block => block.text || "").join("\n");
}

function addMessage(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `message ${role}`;
  // Text nodes prevent model output or user input from becoming executable HTML.
  const urlPattern = /https?:\/\/[^\s<>]+/g;
  let offset = 0;
  for (const match of text.matchAll(urlPattern)) {
    const url = match[0].replace(/[.,;:!?)\]]+$/, "");
    bubble.append(document.createTextNode(text.slice(offset, match.index)));
    const link = document.createElement("a");
    link.href = url;
    link.textContent = url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    bubble.append(link);
    offset = match.index + url.length;
  }
  bubble.append(document.createTextNode(text.slice(offset)));
  messages.append(bubble);
  messages.scrollTop = messages.scrollHeight;
  return bubble;
}

function renderHistory(history = []) {
  messages.replaceChildren();
  addMessage("assistant", GREETING);
  for (const message of history) {
    const role = message.type || message.role;
    if (!["human", "user", "ai", "assistant"].includes(role)) continue;
    if (message.tool_calls?.length) continue;
    const text = contentText(message.content);
    if (text) addMessage(["human", "user"].includes(role) ? "user" : "assistant", text);
  }
}

function setBusy(value, label = "") {
  busy = value;
  send.disabled = value;
  newChat.disabled = value;
  question.readOnly = value;
  activity.textContent = label;
  form.setAttribute("aria-busy", String(value));
}

function showError(error) {
  errorBox.textContent = error instanceof TypeError
    ? "Không kết nối được máy chủ. Hãy kiểm tra chương trình đang chạy và thử lại."
    : error.message;
  errorBox.hidden = false;
}

async function initialize(fresh = false) {
  setBusy(true, "Đang mở cuộc trò chuyện…");
  errorBox.hidden = true;
  try {
    threadId = fresh ? null : savedThread();
    let history = [];
    if (threadId) {
      try {
        const state = await api(`/threads/${encodeURIComponent(threadId)}/state`);
        history = state.values?.messages || [];
      } catch (error) {
        if (error.status !== 404) throw error;
        threadId = null;
      }
    }
    if (!threadId) {
      const thread = await api("/threads", {});
      threadId = thread.thread_id;
    }
    saveThread(threadId);
    renderHistory(history);
    conversation.textContent = `Conversation ID: ${threadId}`;
    connection.textContent = "Sẵn sàng";
    connection.classList.add("ready");
  } catch (error) {
    threadId = null;
    connection.textContent = "Chưa kết nối";
    connection.classList.remove("ready");
    showError(error);
  } finally {
    setBusy(false);
    question.focus();
  }
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  if (busy) return;
  const text = question.value.trim();
  if (!text) return;
  if (!threadId) await initialize();
  if (!threadId) return;
  errorBox.hidden = true;
  setBusy(true, "Trợ lý đang trả lời…");
  addMessage("user", text);
  question.value = "";
  question.style.height = "auto";
  const pending = addMessage("assistant", "");
  pending.classList.add("pending");
  pending.setAttribute("aria-label", "Trợ lý đang trả lời");
  for (let i = 0; i < 3; i++) pending.append(document.createElement("i"));
  try {
    // Native stateful run: LangGraph loads and checkpoints the entire conversation.
    const result = await api(`/threads/${encodeURIComponent(threadId)}/runs/wait`, {
      assistant_id: "chatbot",
      input: { messages: [{ type: "human", content: text }] },
      config: { recursion_limit: 16 },
      multitask_strategy: "reject",
    });
    const last = result.messages?.at(-1);
    if (!last || !["ai", "assistant"].includes(last.type || last.role)
        || last.tool_calls?.length || !contentText(last.content)) {
      throw new Error("Trợ lý chưa tạo được câu trả lời. Vui lòng thử lại.");
    }
    renderHistory(result.messages);
  } catch (error) {
    showError(error);
    // Restore committed state after an interrupted response; don't retry a run automatically.
    try {
      const state = await api(`/threads/${encodeURIComponent(threadId)}/state`);
      renderHistory(state.values?.messages || []);
    } catch { /* Keep visible messages if the server is unreachable. */ }
  } finally {
    pending.remove();
    setBusy(false);
    question.focus();
  }
});

question.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!busy) form.requestSubmit();
  }
});
question.addEventListener("input", () => {
  question.style.height = "auto";
  question.style.height = `${Math.min(question.scrollHeight, 120)}px`;
});
newChat.addEventListener("click", () => { if (!busy) initialize(true); });
renderHistory();
initialize();
