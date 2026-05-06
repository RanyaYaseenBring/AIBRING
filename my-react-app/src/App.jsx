import { useState, useRef, useEffect } from "react";
import ChatbotIcon from "./components/ChatbotIcon";

const BACKEND_BASE = "http://127.0.0.1:8000";
const CHAT_URL = `${BACKEND_BASE}/chat`;
const REQUEST_TIMEOUT_MS = 180000;
function cleanBotAnswer(answer) {
  const text = (answer || "").trim();
  return text || "Geen antwoord ontvangen.";
}

function App() {
  const [text, setText] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const chatBodyRef = useRef(null);
  const hasStarted = useRef(false); 

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    setMessages([
      {
        sender: "bot",
        text:
          "Hallo! 👋\n\nWaarmee kan ik je helpen?\n\nHeb je een vraag over track & trace of een andere interne vraag?",
      },
    ]);
  }, []);

  function addBot(t) {
    setMessages((prev) => [...prev, { sender: "bot", text: t }]);
  }

  function addUser(t) {
    setMessages((prev) => [...prev, { sender: "user", text: t }]);
  }

  async function sendToBackend(question) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const res = await fetch(CHAT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
        signal: controller.signal,
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error("Backend fout");

      return cleanBotAnswer(data?.answer);
    } catch (err) {
      if (err?.name === "AbortError") {
        return "Backend duurde te lang (timeout).";
      }
      return "Er ging iets mis.";
    } finally {
      clearTimeout(timeout);
    }
  }

  async function handleUserSend(input) {
    if (loading) return;
    const msg = (input || "").trim();
    if (!msg) return;

    setLoading(true);
    addUser(msg);
    setText("");

    try {
      const answer = await sendToBackend(msg);
      addBot(answer);
    } finally {
      setLoading(false);
    }
  }

  function sendMessage(e) {
    e.preventDefault();
    handleUserSend(text);
  }

  return (
    <div className="container">
      <div className="chatbot-popup">
        <div className="chat-header">
          <div className="header-info">
            <ChatbotIcon />
            <h2 className="logo-text">ChatBot</h2>
          </div>
        </div>

        <div className="chat-body" ref={chatBodyRef}>
          {messages.map((msg, index) => (
            <div
              key={index}
              className={
                msg.sender === "user"
                  ? "message-user-message"
                  : "message-bot-message"
              }
            >
              {msg.sender === "bot" && <ChatbotIcon />}
              <p className="message-text" style={{ whiteSpace: "pre-wrap" }}>
                {msg.text}
              </p>
            </div>
          ))}

          {loading && (
            <div className="message-bot-message">
              <ChatbotIcon />
              <p className="message-text typing">
                <span></span>
                <span></span>
                <span></span>
              </p>
            </div>
          )}
        </div>

        <div className="chat-footer">
          <form onSubmit={sendMessage} className="chat-form">
            <input
              type="text"
              placeholder="Typ je bericht..."
              className="message-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={loading}
            />
            <button
              className="material-symbols-rounded"
              disabled={loading}
              type="submit"
              title="Verstuur"
            >
              keyboard_arrow_up
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;