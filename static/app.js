/**
 * Zerith AI — Web UI Client
 * SocketIO chat client with markdown rendering and plan display.
 */

// ── State ───────────────────────────────────────────────
const socket = io();
let isThinking = false;

// ── DOM Elements ────────────────────────────────────────
const chatArea = document.getElementById("chatArea");
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const thinkingIndicator = document.getElementById("thinkingIndicator");
const topbarStatus = document.getElementById("topbarStatus");
const toolList = document.getElementById("toolList");
const sidebar = document.getElementById("sidebar");
const openSidebarBtn = document.getElementById("openSidebar");
const closeSidebarBtn = document.getElementById("closeSidebar");
const clearBtn = document.getElementById("clearBtn");
const newChatBtn = document.getElementById("newChatBtn");

// ── SocketIO Events ─────────────────────────────────────

socket.on("connect", () => {
    topbarStatus.textContent = "Connected";
    topbarStatus.classList.remove("disconnected");
    document.getElementById("statusDot").classList.add("connected");
    loadTools();
});

socket.on("disconnect", () => {
    topbarStatus.textContent = "Disconnected";
    topbarStatus.classList.add("disconnected");
    document.getElementById("statusDot").classList.remove("connected");
});

socket.on("thinking", (data) => {
    isThinking = data.status;
    if (data.status) {
        thinkingIndicator.classList.add("active");
        scrollToBottom();
    } else {
        thinkingIndicator.classList.remove("active");
    }
});

socket.on("chat_response", (data) => {
    addMessage("assistant", data.message, data.error);
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
});

socket.on("plan", (data) => {
    addPlanMessage(data);
});

socket.on("executing", () => {
    updateThinkingText("Executing plan...");
});

socket.on("plan_result", (data) => {
    addResultMessage(data);
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
});

socket.on("history_cleared", () => {
    messages.innerHTML = "";
    welcome.classList.remove("hidden");
});

// ── Tool Icon Map ───────────────────────────────────────
const toolIcons = {
    keyboard: "⌨️",
    mouse: "🖱️",
    system: "💻",
    vision: "👁️",
    web: "🌐",
    memory: "🧠",
    preferences: "⚙️",
    file: "📁",
    automation: "🤖",
};

// ── Functions ───────────────────────────────────────────

function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isThinking) return;

    // Hide welcome
    welcome.classList.add("hidden");

    // Show user message
    addMessage("user", text);

    // Send to server
    socket.emit("chat_message", { message: text });

    // Reset input
    messageInput.value = "";
    messageInput.style.height = "auto";
    sendBtn.classList.add("disabled");
    isThinking = true;
}

function addMessage(role, text, isError = false) {
    const msgEl = document.createElement("div");
    msgEl.className = `message ${role}${isError ? " error" : ""}`;

    const avatar = role === "user" ? "👤" : "⚡";
    const sender = role === "user" ? "You" : "Zerith";

    let rendered = text;
    try {
        rendered = marked.parse(text);
    } catch (e) {
        rendered = escapeHtml(text);
    }

    msgEl.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-sender">${sender}</div>
            <div class="message-body">${rendered}</div>
        </div>
    `;

    messages.appendChild(msgEl);
    scrollToBottom();
}

function addPlanMessage(data) {
    const msgEl = document.createElement("div");
    msgEl.className = "message assistant";

    let stepsHtml = "";
    for (const step of data.steps) {
        stepsHtml += `
            <div class="plan-step" id="step-${step.step}">
                <div class="step-number">${step.step}</div>
                <span class="step-tool">${step.tool}</span>
                <span class="step-action">${step.action}</span>
                <span class="step-status">⏳</span>
            </div>
        `;
    }

    let responseHtml = "";
    try {
        responseHtml = marked.parse(data.response || "");
    } catch (e) {
        responseHtml = escapeHtml(data.response || "");
    }

    msgEl.innerHTML = `
        <div class="message-avatar">⚡</div>
        <div class="message-content">
            <div class="message-sender">Zerith</div>
            <div class="message-body">${responseHtml}</div>
            <div class="plan-card">
                <div class="plan-header">📋 Execution Plan — ${data.steps.length} step(s)</div>
                <div class="plan-steps">${stepsHtml}</div>
            </div>
        </div>
    `;

    messages.appendChild(msgEl);
    scrollToBottom();
}

function addResultMessage(data) {
    // Update step statuses in existing plan card
    for (const result of data.results) {
        const stepEl = document.getElementById(`step-${result.step}`);
        if (stepEl) {
            const statusEl = stepEl.querySelector(".step-status");
            statusEl.textContent = result.status === "success" ? "✅" : "❌";

            // Add result detail
            if (result.result) {
                const resultEl = document.createElement("div");
                resultEl.className = "step-result";
                resultEl.textContent = result.result.substring(0, 500);
                stepEl.parentNode.insertBefore(resultEl, stepEl.nextSibling);
            }
        }
    }

    // Add summary
    const summary = data.summary;
    const isSuccess = summary.failed === 0;
    const summaryEl = document.createElement("div");
    summaryEl.className = `result-summary ${isSuccess ? "success" : "failure"}`;
    summaryEl.innerHTML = `
        ${isSuccess ? "✅" : "⚠️"}
        <span>${summary.success} succeeded, ${summary.failed} failed out of ${summary.total} steps</span>
    `;
    messages.appendChild(summaryEl);
    scrollToBottom();
}

function updateThinkingText(text) {
    const thinkingText = document.querySelector(".thinking-text");
    if (thinkingText) thinkingText.textContent = text;
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function loadTools() {
    fetch("/api/tools")
        .then((r) => r.json())
        .then((tools) => {
            toolList.innerHTML = "";
            for (const [name, actions] of Object.entries(tools).sort()) {
                const icon = toolIcons[name] || "🔧";
                const item = document.createElement("div");
                item.className = "tool-item";
                item.innerHTML = `
                    <span class="tool-icon">${icon}</span>
                    <span class="tool-name">${name}</span>
                    <span class="tool-count">${actions.length}</span>
                `;
                item.title = actions.join(", ");
                toolList.appendChild(item);
            }
        })
        .catch(() => {
            toolList.innerHTML = '<div class="tool-item loading">Failed to load tools</div>';
        });
}

// ── Auto-resize textarea ────────────────────────────────
messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
});

// ── Event Listeners ─────────────────────────────────────
sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Hint cards
document.querySelectorAll(".hint-card").forEach((card) => {
    card.addEventListener("click", () => {
        messageInput.value = card.dataset.message;
        sendMessage();
    });
});

// Sidebar toggle
openSidebarBtn.addEventListener("click", () => {
    sidebar.classList.remove("collapsed");
});

closeSidebarBtn.addEventListener("click", () => {
    sidebar.classList.add("collapsed");
});

// Clear conversation
clearBtn.addEventListener("click", () => {
    socket.emit("clear_history");
});

// New chat
newChatBtn.addEventListener("click", () => {
    socket.emit("clear_history");
});
