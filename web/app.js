const state = {
  userId: null,
  sessionId: null,
};

const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chatForm");
const inputEl = document.getElementById("promptInput");
const metaEl = document.getElementById("sessionMeta");
const templateEl = document.getElementById("messageTemplate");

function addMessage(role, text) {
  const node = templateEl.content.firstElementChild.cloneNode(true);
  node.classList.add(role);
  node.querySelector(".who").textContent = role === "user" ? "YOU" : "AGENT";
  node.querySelector(".bubble").textContent = text;
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setMeta() {
  if (!state.sessionId) {
    metaEl.textContent = "Disconnected";
    return;
  }
  metaEl.textContent = `User: ${state.userId} | Session: ${state.sessionId}`;
}

async function initSession() {
  const response = await fetch("/api/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userId: "web-user" }),
  });

  if (!response.ok) {
    throw new Error("Could not create session.");
  }

  const data = await response.json();
  state.userId = data.userId;
  state.sessionId = data.sessionId;
  setMeta();
}

async function sendMessage(prompt) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: prompt,
      userId: state.userId,
      sessionId: state.sessionId,
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }

  return data.reply;
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = inputEl.value.trim();
  if (!prompt) {
    return;
  }

  addMessage("user", prompt);
  inputEl.value = "";

  const loadingText = "Thinking...";
  addMessage("assistant", loadingText);
  const loadingBubble = messagesEl.lastElementChild.querySelector(".bubble");

  try {
    const reply = await sendMessage(prompt);
    loadingBubble.textContent = reply;
  } catch (error) {
    loadingBubble.textContent = `Error: ${error.message}`;
  }
});

(async () => {
  try {
    await initSession();
    addMessage("assistant", "Session is ready. Ask me the current time in a city.");
  } catch (error) {
    addMessage("assistant", `Startup error: ${error.message}`);
    setMeta();
  }
})();
