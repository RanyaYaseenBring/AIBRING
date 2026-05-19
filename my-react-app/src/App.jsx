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

  const [hasSelectedOption, setHasSelectedOption] =
    useState(false);

  const chatBodyRef = useRef(null);

  const hasStarted = useRef(false);

  useEffect(() => {

    if (chatBodyRef.current) {

      chatBodyRef.current.scrollTop =
        chatBodyRef.current.scrollHeight;
    }

  }, [messages, loading]);

  useEffect(() => {

    if (hasStarted.current) return;

    hasStarted.current = true;

    setLoading(true);

    setTimeout(() => {

      setLoading(false);

      addBot(
        "Hallo! Ik ben uw Bring ChatBot 👋\n\nKies een optie om te beginnen."
      );

    }, 2000);

  }, []);

  function addBot(t) {

    setMessages((prev) => [

      ...prev,

      {
        sender: "bot",
        text: t
      },

    ]);
  }

  function addUser(t) {

    setMessages((prev) => [

      ...prev,

      {
        sender: "user",
        text: t
      },

    ]);
  }

  async function sendToBackend(question) {

    const controller =
      new AbortController();

    const timeout = setTimeout(

      () => controller.abort(),

      REQUEST_TIMEOUT_MS
    );

    try {

      const res = await fetch(
        CHAT_URL,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            message: question,
          }),

          signal: controller.signal,
        }
      );

      const data =
        await res.json().catch(() => ({}));

      if (!res.ok) {

        throw new Error(
          "Backend fout"
        );
      }

      return cleanBotAnswer(
        data?.answer
      );

    } catch (err) {

      if (
        err?.name === "AbortError"
      ) {

        return
          "Backend duurde te lang (timeout).";
      }

      return "Er ging iets mis.";

    } finally {

      clearTimeout(timeout);
    }
  }

  async function handleUserSend(input) {

    if (loading) return;

    const msg =
      (input || "").trim();

    if (!msg) return;

    if (
      input === "Algemene vraag" ||
      input === "Track & Trace" ||
      input === "Interne Vraag"
    ) {

      setHasSelectedOption(true);
    }

    setLoading(true);

    addUser(msg);

    setText("");

    try {

      const answer =
        await sendToBackend(msg);

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

        {/* HEADER */}

        <div className="chat-header">

          <h2>
            Bring ChatBot
          </h2>

        </div>

        {/* CHAT BODY */}

        <div
          className="chat-body"
          ref={chatBodyRef}
        >

          {/* QUICK OPTIONS */}

          <div className="vraag-container">

            <div
              className="message-option-bubble"
              onClick={() =>
                handleUserSend(
                  "Algemene vraag"
                )
              }
            >
              Algemene vraag
            </div>

            <div
              className="message-option-bubble"
              onClick={() =>
                handleUserSend(
                  "Track & Trace"
                )
              }
            >
              Track & Trace
            </div>

            <div
              className="message-option-bubble"
              onClick={() =>
                handleUserSend(
                  "Interne Vraag"
                )
              }
            >
              Interne Vraag
            </div>

          </div>

          {/* CHAT MESSAGES */}

          {messages.map((msg, index) => (

            <div
              key={index}

              className={
                msg.sender === "user"

                  ? "message-user-message"

                  : "message-bot-message"
              }
            >

              {msg.sender === "bot" && (
                <ChatbotIcon />
              )}

              <p
                className="message-text"

                style={{
                  whiteSpace: "pre-wrap",
                }}
              >
                {msg.text}
              </p>

            </div>
          ))}

          {/* LOADING DOTS */}

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

        {/* FOOTER */}

        <div className="chat-footer">

          <form
            onSubmit={sendMessage}
            className="chat-form"
          >

            <input
              type="text"

              placeholder={
                hasSelectedOption

                  ? "Typ je bericht..."

                  : "Kies eerst een optie..."
              }

              className="message-input"

              value={text}

              onChange={(e) =>
                setText(e.target.value)
              }

              disabled={
                loading ||
                !hasSelectedOption
              }
            />

            <button
              className="material-symbols-rounded"

              disabled={
                loading ||
                !hasSelectedOption
              }

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