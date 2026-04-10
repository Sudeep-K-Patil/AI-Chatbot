import os
import json
from urllib import error, request as urlrequest
from typing import List, Dict

from flask import Flask, jsonify, render_template_string, request, session

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-in-production")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
PORT = int(os.getenv("PORT", "5000"))
OLLAMA_FALLBACK_HOST = "http://host.docker.internal:11434"


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Chatbot</title>
    <style>
        :root {
            --bg: #f4efe7;
            --panel: #fffdf8;
            --text: #1d1d1d;
            --muted: #6b6b6b;
            --accent: #0d6e6e;
            --accent-dark: #084f4f;
            --border: #ded6ca;
            --user: #dff5f2;
            --assistant: #f4f0e8;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: Georgia, "Times New Roman", serif;
            background:
                radial-gradient(circle at top left, #fff5e8 0%, transparent 30%),
                linear-gradient(135deg, #f3eadf 0%, #efe7db 45%, #e6efe9 100%);
            color: var(--text);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }

        .app-shell {
            width: min(900px, 100%);
            background: rgba(255, 253, 248, 0.94);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(222, 214, 202, 0.9);
            border-radius: 24px;
            overflow: hidden;
            box-shadow: 0 18px 50px rgba(38, 45, 40, 0.12);
        }

        .hero {
            padding: 28px 28px 16px;
            border-bottom: 1px solid var(--border);
            background: linear-gradient(180deg, rgba(255,255,255,0.55), rgba(255,255,255,0));
        }

        .hero h1 {
            margin: 0 0 8px;
            font-size: clamp(28px, 4vw, 42px);
            line-height: 1;
        }

        .hero p {
            margin: 0;
            color: var(--muted);
            font-size: 16px;
        }

        .chat-box {
            height: 460px;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .message {
            max-width: 82%;
            padding: 14px 16px;
            border-radius: 18px;
            line-height: 1.5;
            white-space: pre-wrap;
            border: 1px solid rgba(0, 0, 0, 0.05);
            animation: slideUp 180ms ease-out;
        }

        .user {
            align-self: flex-end;
            background: var(--user);
        }

        .assistant {
            align-self: flex-start;
            background: var(--assistant);
        }

        .composer {
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 12px;
            padding: 18px 24px 24px;
            border-top: 1px solid var(--border);
            background: rgba(255, 255, 255, 0.55);
        }

        textarea {
            width: 100%;
            min-height: 58px;
            max-height: 160px;
            resize: vertical;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 14px;
            font: inherit;
            color: var(--text);
            background: white;
        }

        button {
            border: none;
            border-radius: 16px;
            padding: 0 18px;
            font: inherit;
            cursor: pointer;
            transition: transform 120ms ease, opacity 120ms ease, background 120ms ease;
        }

        button:hover {
            transform: translateY(-1px);
        }

        button:disabled {
            opacity: 0.6;
            cursor: wait;
            transform: none;
        }

        .send-btn {
            background: var(--accent);
            color: white;
        }

        .clear-btn {
            background: #efe8de;
            color: var(--text);
        }

        .status {
            padding: 0 24px 18px;
            color: var(--muted);
            font-size: 14px;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 700px) {
            body {
                padding: 12px;
            }

            .chat-box {
                height: 58vh;
                padding: 16px;
            }

            .message {
                max-width: 92%;
            }

            .composer {
                grid-template-columns: 1fr;
            }

            button {
                height: 48px;
            }
        }
    </style>
</head>
<body>
    <main class="app-shell">
        <section class="hero">
            <h1>AI Chatbot</h1>
            <p>Ask a question, brainstorm ideas, or get help writing and planning.</p>
        </section>

        <section id="chatBox" class="chat-box">
            <div class="message assistant">Hi, I'm your AI chatbot. What would you like help with?</div>
        </section>

        <form id="chatForm" class="composer">
            <textarea id="messageInput" placeholder="Type your message here..." required></textarea>
            <button class="send-btn" type="submit">Send</button>
            <button class="clear-btn" type="button" id="clearBtn">Clear</button>
        </form>

        <div id="status" class="status">Ready</div>
    </main>

    <script>
        const chatBox = document.getElementById("chatBox");
        const chatForm = document.getElementById("chatForm");
        const messageInput = document.getElementById("messageInput");
        const clearBtn = document.getElementById("clearBtn");
        const statusEl = document.getElementById("status");

        function addMessage(content, role) {
            const message = document.createElement("div");
            message.className = `message ${role}`;
            message.textContent = content;
            chatBox.appendChild(message);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        async function sendMessage(message) {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message })
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: "Something went wrong." }));
                throw new Error(error.error || "Request failed.");
            }

            return response.json();
        }

        chatForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage(message, "user");
            messageInput.value = "";
            statusEl.textContent = "Thinking...";

            const submitButton = chatForm.querySelector(".send-btn");
            submitButton.disabled = true;

            try {
                const data = await sendMessage(message);
                addMessage(data.reply, "assistant");
                statusEl.textContent = "Ready";
            } catch (error) {
                addMessage(error.message, "assistant");
                statusEl.textContent = "There was a problem answering that message.";
            } finally {
                submitButton.disabled = false;
                messageInput.focus();
            }
        });

        clearBtn.addEventListener("click", async () => {
            try {
                await fetch("/reset", { method: "POST" });
                chatBox.innerHTML = '<div class="message assistant">Hi, I\\'m your AI chatbot. What would you like help with?</div>';
                statusEl.textContent = "Conversation cleared";
            } catch {
                statusEl.textContent = "Unable to clear the conversation";
            }
        });
    </script>
</body>
</html>
"""


def get_conversation() -> List[Dict[str, str]]:
    return session.setdefault(
        "messages",
        [
            {
                "role": "system",
                "content": (
                    "You are a helpful, concise, friendly AI chatbot. "
                    "Answer clearly and keep responses practical."
                ),
            }
        ],
    )


def generate_reply(messages: List[Dict[str, str]]) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "messages": messages,
            "stream": False,
        }
    )

    hosts = [OLLAMA_HOST]
    if OLLAMA_FALLBACK_HOST not in hosts:
        hosts.append(OLLAMA_FALLBACK_HOST)

    last_error = None
    for host in hosts:
        req = urlrequest.Request(
            f"{host}/api/chat",
            data=payload.encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlrequest.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except error.URLError as exc:
            last_error = exc
    else:
        raise RuntimeError(
            "Cannot reach Ollama. Make sure Ollama is installed and running. Tried: "
            f"{', '.join(hosts)}."
        ) from last_error

    message = data.get("message", {})
    content = (message.get("content") or "").strip()
    if not content:
        raise RuntimeError("Ollama returned an empty response.")
    return content


@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL}), 200


@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    messages = get_conversation()
    messages.append({"role": "user", "content": user_message})

    try:
        reply = generate_reply(messages)
    except Exception as exc:
        return jsonify({"error": f"Ollama request failed: {exc}"}), 500

    messages.append({"role": "assistant", "content": reply})
    session["messages"] = messages

    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    session.pop("messages", None)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=PORT, use_reloader=False)
