/**
 * Zerith AI — Web UI Client
 * SocketIO chat client with markdown rendering and plan display.
 */

// ── State ───────────────────────────────────────────────
const socket = io();
let isThinking = false;
let isRecording = false;
let isSpeaking = false;
let recognition = null;
let lastAssistantMessage = "";

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
const micBtn = document.getElementById("micBtn");
const speakerBtn = document.getElementById("speakerBtn");
const captureBtn = document.getElementById("captureBtn");
const uploadBtn = document.getElementById("uploadBtn");
const imageInput = document.getElementById("imageInput");

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
    lastAssistantMessage = "";
});

// ── Voice Events from Backend ────────────────────────────
socket.on("tts_ready", (data) => {
    // Use browser's speech synthesis for TTS
    speakText(data.text);
});

socket.on("image_result", (data) => {
    addMessage("assistant", data.result, data.error);
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
});

socket.on("voice_recognized", (data) => {
    // Send the recognized voice text as a chat message
    const text = data.text.trim();
    if (text) {
        messageInput.value = text;
        sendMessage();
    }
});

// ── Self-Coding Socket Events ────────────────────────────
socket.on("file_modified", (data) => {
    if (data.success) {
        addMessage("assistant", `✅ File modified: ${data.path}\n${data.result}`);
        // Check if refresh is needed
        if (data.refresh) {
            addMessage("assistant", "💡 Please refresh your browser to see the changes.");
        }
    } else {
        addMessage("assistant", `❌ File modification failed: ${data.error}`, true);
    }
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
});

socket.on("file_content", (data) => {
    if (data.success) {
        // Show file content in a collapsible format
        const contentPreview = data.content.substring(0, 500) + (data.content.length > 500 ? "..." : "");
        addMessage("assistant", `📄 **File: ${data.path}**\n\n\`\`\`\n${contentPreview}\n\`\`\``);
    } else {
        addMessage("assistant", `❌ Could not read file: ${data.error}`, true);
    }
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
});

socket.on("ui_changed", (data) => {
    if (data.success) {
        addMessage("assistant", `✅ ${data.message}`);
        if (data.refresh) {
            addMessage("assistant", "💡 Please refresh your browser to see the changes.");
        }
    } else {
        addMessage("assistant", `❌ UI change failed: ${data.error}`, true);
    }
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
});

// ── Memory Socket Events ────────────────────────────
socket.on("memory_results", (data) => {
    if (data.error) {
        addMessage("assistant", `❌ Memory search failed: ${data.results}`, true);
    } else {
        addMessage("assistant", `🔍 **Memory Search Results:**\n\n${data.results}`);
    }
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
});

socket.on("memory_stats_result", (data) => {
    if (data.error) {
        addMessage("assistant", `❌ Memory stats error: ${data.stats}`, true);
    } else {
        addMessage("assistant", `📊 **Memory Statistics:**\n\n${data.stats}`);
    }
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
});

socket.on("memory_cleared", (data) => {
    if (data.error) {
        addMessage("assistant", `❌ Clear memory failed: ${data.result}`, true);
    } else {
        addMessage("assistant", `🗑️ ${data.result}`);
    }
    isThinking = false;
    thinkingIndicator.classList.remove("active");
    sendBtn.classList.remove("disabled");
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

    // Check for memory commands
    for (const [cmd, handler] of Object.entries(memoryCommands)) {
        if (text.toLowerCase().startsWith(cmd)) {
            if (handler(text)) {
                messageInput.value = "";
                return;
            }
        }
    }

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

    // Store last assistant message for TTS
    if (role === "assistant") {
        lastAssistantMessage = text;
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

// ── Voice Input (Microphone) ───────────────────────────
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("Speech recognition not supported");
        micBtn.disabled = true;
        micBtn.title = "Speech recognition not supported";
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add("recording");
        micBtn.title = "Recording... Click to stop";
    };

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join("");

        if (event.results[0].isFinal) {
            messageInput.value = transcript;
            messageInput.style.height = "auto";
            messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
        }
    };

    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        stopRecording();
    };

    recognition.onend = () => {
        stopRecording();
    };
}

function toggleRecording() {
    if (!recognition) {
        initSpeechRecognition();
        if (!recognition) return;
    }

    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

function stopRecording() {
    isRecording = false;
    micBtn.classList.remove("recording");
    micBtn.title = "Voice input (speech recognition)";
}

micBtn.addEventListener("click", toggleRecording);

// ── Voice Output (TTS) ─────────────────────────────────
function speakText(text) {
    if (!("speechSynthesis" in window)) {
        console.warn("Speech synthesis not supported");
        return;
    }

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
        isSpeaking = true;
        speakerBtn.classList.add("speaking");
        speakerBtn.title = "Speaking... Click to stop";
    };

    utterance.onend = () => {
        isSpeaking = false;
        speakerBtn.classList.remove("speaking");
        speakerBtn.title = "Voice output (text-to-speech)";
    };

    utterance.onerror = (event) => {
        console.error("TTS error:", event.error);
        isSpeaking = false;
        speakerBtn.classList.remove("speaking");
        speakerBtn.title = "Voice output (text-to-speech)";
    };

    window.speechSynthesis.speak(utterance);
}

function toggleSpeaking() {
    if (isSpeaking) {
        window.speechSynthesis.cancel();
    } else if (lastAssistantMessage) {
        speakText(lastAssistantMessage);
    } else {
        // Get the last assistant message from the DOM
        const lastMsg = messages.querySelector(".message.assistant:last-child .message-body");
        if (lastMsg) {
            // Strip HTML tags
            const tempDiv = document.createElement("div");
            tempDiv.innerHTML = lastMsg.innerHTML;
            const text = tempDiv.textContent || tempDiv.innerText || "";
            speakText(text);
        }
    }
}

speakerBtn.addEventListener("click", toggleSpeaking);

// ── Image Capture (Screen) ───────────────────────────
captureBtn.addEventListener("click", async () => {
    captureBtn.disabled = true;
    captureBtn.title = "Capturing...";

    try {
        // Add message that we're capturing screen
        addMessage("user", "[Capturing screen...]");
        welcome.classList.add("hidden");

        // Request screen capture
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: { displaySurface: "monitor" }
        });

        // Create video element to capture frame
        const video = document.createElement("video");
        video.srcObject = stream;
        await video.play();

        // Create canvas and capture frame
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0);

        // Stop the stream
        stream.getTracks().forEach(track => track.stop());

        // Get image as data URL
        const imageDataUrl = canvas.toDataURL("image/png");

        // Send to backend for analysis
        socket.emit("image_analyze", { image: imageDataUrl });

        // Show thinking
        isThinking = true;
        thinkingIndicator.classList.add("active");
        sendBtn.classList.add("disabled");

    } catch (error) {
        console.error("Screen capture error:", error);
        addMessage("assistant", "Could not capture screen: " + error.message, true);
    }

    captureBtn.disabled = false;
    captureBtn.title = "Capture screen";
});

// ── Image Upload ───────────────────────────────────────
imageInput.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const imageDataUrl = e.target.result;

        // Show user the uploaded image
        addMessage("user", `[Uploading image: ${file.name}]`);
        welcome.classList.add("hidden");

        // Send to backend for analysis
        socket.emit("image_analyze", { image: imageDataUrl });

        // Show thinking
        isThinking = true;
        thinkingIndicator.classList.add("active");
        sendBtn.classList.add("disabled");
    };
    reader.readAsDataURL(file);

    // Reset input
    imageInput.value = "";
});

// ── Memory Functions ────────────────────────────────
function searchMemory(query) {
    if (!query || isThinking) return;
    
    isThinking = true;
    thinkingIndicator.classList.add("active");
    sendBtn.classList.add("disabled");
    
    socket.emit("memory_search", { query: query });
}

function getMemoryStats() {
    if (isThinking) return;
    
    isThinking = true;
    thinkingIndicator.classList.add("active");
    sendBtn.classList.add("disabled");
    
    socket.emit("memory_stats");
}

function clearMemory() {
    if (isThinking) return;
    
    if (!confirm("Are you sure you want to clear all conversation memories? This cannot be undone.")) {
        return;
    }
    
    isThinking = true;
    thinkingIndicator.classList.add("active");
    sendBtn.classList.add("disabled");
    
    socket.emit("clear_memory");
}

// Memory commands that can be typed in chat
const memoryCommands = {
    "search memory": (query) => {
        const match = query.match(/search memory\s+(.+)/i);
        if (match) {
            searchMemory(match[1]);
            return true;
        }
        return false;
    },
    "memory stats": () => {
        getMemoryStats();
        return true;
    },
    "clear memory": () => {
        clearMemory();
        return true;
    }
};
