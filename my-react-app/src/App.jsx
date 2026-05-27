import { useState, useRef, useEffect } from "react";
import "./index.css";

function App() {

  /* =========================
     USERS
  ========================= */

  const [users, setUsers] = useState([
    {
      username: "admin",
      password: "Bring123!",
      role: "admin"
    }
  ]);

  /* =========================
     PAGE STATE
  ========================= */

  const [page, setPage] = useState(() => {
    const savedLoggedIn = localStorage.getItem("loggedIn");
    return savedLoggedIn === "true" ? "chat" : "login";
  });

  /* =========================
     LOGIN STATE
  ========================= */

  const [loggedIn, setLoggedIn] = useState(() => {
    const savedLoggedIn = localStorage.getItem("loggedIn");
    return savedLoggedIn === "true";
  });

  const [username, setUsername] = useState(() => {
    return localStorage.getItem("username") || "";
  });

  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  /* =========================
     ADMIN PANEL STATE
  ========================= */

  const [signupUsername, setSignupUsername] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [signupError, setSignupError] = useState("");

  /* =========================
     CHAT STATE
  ========================= */

  const [text, setText] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSelectedOption, setHasSelectedOption] = useState(false);

  const chatBodyRef = useRef(null);
  const hasStarted = useRef(false);

  /* =========================
     BACKEND
  ========================= */

  const BACKEND_BASE = "http://127.0.0.1:8000";
  const CHAT_URL = `${BACKEND_BASE}/chat`;
  const REQUEST_TIMEOUT_MS = 180000;

  /* =========================
     AUTO SCROLL
  ========================= */

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop =
        chatBodyRef.current.scrollHeight;
    }
  }, [messages, loading]);

  /* =========================
     WELCOME MESSAGE
  ========================= */

  useEffect(() => {

    if (!loggedIn) return;
    if (hasStarted.current) return;

    hasStarted.current = true;

    setLoading(true);

    setTimeout(() => {

      setLoading(false);

      addBot(
        `Hallo ${username}! 👋\n\nKies een optie om te beginnen.`
      );

    }, 1200);

  }, [loggedIn]);

  /* =========================
     LOGOUT
  ========================= */

  function handleLogout() {

    localStorage.removeItem("loggedIn");
    localStorage.removeItem("username");
    localStorage.removeItem("role");

    setLoggedIn(false);

    setUsername("");
    setPassword("");

    setMessages([]);

    setHasSelectedOption(false);

    hasStarted.current = false;

    setPage("login");
  }

  /* =========================
     HELPERS
  ========================= */

  function cleanBotAnswer(answer) {

    const text = (answer || "").trim();

    return text || "Geen antwoord ontvangen.";
  }

  function addBot(t) {

    setMessages((prev) => [
      ...prev,
      {
        sender: "bot",
        text: t
      }
    ]);
  }

  function addUser(t) {

    setMessages((prev) => [
      ...prev,
      {
        sender: "user",
        text: t
      }
    ]);
  }

  /* =========================
     BACKEND REQUEST
  ========================= */

  async function sendToBackend(question) {

    const controller = new AbortController();

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
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            message: question,
            session_id: username
          }),

          signal: controller.signal,
        }
      );

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error("Backend fout");
      }

      return cleanBotAnswer(data.answer);

    } catch (err) {

      if (err?.name === "AbortError") {
        return "Backend duurde te lang.";
      }

      return "Er ging iets mis.";

    } finally {

      clearTimeout(timeout);
    }
  }

  /* =========================
     SEND MESSAGE
  ========================= */

  async function handleUserSend(input) {

    if (loading) return;

    const msg = (input || "").trim();

    if (!msg) return;

    if (
      input === "Algemene vraag" ||
      input === "Track & Trace" ||
      input === "Interne Vraag"
    ) {
      setHasSelectedOption(true);
    }

    addUser(msg);

    setText("");

    setLoading(true);

    try {

      const answer = await sendToBackend(msg);

      addBot(answer);

    } catch {

      addBot("Er ging iets mis.");

    } finally {

      setLoading(false);
    }
  }

  function sendMessage(e) {

    e.preventDefault();

    handleUserSend(text);
  }

  /* =========================
     LOGIN PAGE
  ========================= */

  if (page === "login") {

    return (
      <div className="login-page">

        <div className="login-box">

          <h1>Bring ChatBot</h1>

          <input
            type="text"
            placeholder="Gebruikersnaam"
            value={username}
            onChange={(e) =>
              setUsername(e.target.value)
            }
          />

          <input
            type="password"
            placeholder="Wachtwoord"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
          />

          {error && (
            <p className="login-error">
              {error}
            </p>
          )}

          <button
            onClick={() => {

              const foundUser = users.find(
                (u) =>
                  u.username === username &&
                  u.password === password
              );

              if (foundUser) {

                localStorage.setItem(
                  "loggedIn",
                  "true"
                );

                localStorage.setItem(
                  "username",
                  foundUser.username
                );

                localStorage.setItem(
                  "role",
                  foundUser.role
                );

                setLoggedIn(true);

                setError("");

                setPage("chat");

              } else {

                setError(
                  "Onjuiste login gegevens"
                );
              }
            }}
          >
            Sign In
          </button>

          <button
            className="switch-button"
            onClick={() => {

              const currentUser = users.find(
                (u) =>
                  u.username === username
              );

              if (!currentUser) {

                setError(
                  "Voer eerst je gebruikersnaam in"
                );

                return;
              }

              const newPassword =
                prompt("Nieuw wachtwoord:");

              if (!newPassword) return;

              setUsers((prev) =>
                prev.map((u) =>
                  u.username === username
                    ? {
                        ...u,
                        password: newPassword
                      }
                    : u
                )
              );

              alert(
                "Wachtwoord aangepast!"
              );
            }}
          >
            Wachtwoord wijzigen
          </button>

        </div>

      </div>
    );
  }

  /* =========================
     ADMIN PANEL
  ========================= */

  if (page === "admin") {

    if (username !== "admin") {

      return (
        <div className="login-page">

          <div className="login-box">

            <h1>Geen toegang</h1>

            <button
              onClick={() => setPage("chat")}
            >
              Terug
            </button>

          </div>

        </div>
      );
    }

    return (
      <div className="login-page">

        <div className="login-box">

          <h1>Admin Panel</h1>

          <input
            type="text"
            placeholder="Gebruikersnaam"
            value={signupUsername}
            onChange={(e) =>
              setSignupUsername(e.target.value)
            }
          />

          <input
            type="password"
            placeholder="Wachtwoord"
            value={signupPassword}
            onChange={(e) =>
              setSignupPassword(e.target.value)
            }
          />

          {signupError && (
            <p className="login-error">
              {signupError}
            </p>
          )}

          <button
            onClick={() => {

              if (
                !signupUsername ||
                !signupPassword
              ) {

                setSignupError(
                  "Vul alle velden in"
                );

                return;
              }

              const exists = users.find(
                (u) =>
                  u.username === signupUsername
              );

              if (exists) {

                setSignupError(
                  "Gebruiker bestaat al"
                );

                return;
              }

              setUsers((prev) => [
                ...prev,
                {
                  username: signupUsername,
                  password: signupPassword,
                  role: "user"
                }
              ]);

              setSignupUsername("");
              setSignupPassword("");
              setSignupError("");
            }}
          >
            Gebruiker toevoegen
          </button>

          <div
            style={{
              marginTop: "25px",
              display: "flex",
              flexDirection: "column",
              gap: "12px"
            }}
          >

            {users.map((user, index) => (

              <div
                key={index}
                style={{
                  padding: "14px",
                  borderRadius: "12px",
                  background:
                    "rgba(255,255,255,0.05)",
                  border:
                    "1px solid rgba(255,255,255,0.1)"
                }}
              >

                <strong>
                  {user.username}
                </strong>

                <p
                  style={{
                    marginTop: "6px",
                    opacity: 0.7
                  }}
                >
                  Rol: {user.role}
                </p>

                {user.username !== "admin" && (

                  <button
                    style={{
                      marginTop: "10px"
                    }}
                    onClick={() => {

                      setUsers(
                        users.filter(
                          (u) =>
                            u.username !==
                            user.username
                        )
                      );
                    }}
                  >
                    Verwijderen
                  </button>

                )}

              </div>
            ))}

          </div>

          <button
            className="switch-button"
            onClick={() => setPage("chat")}
          >
            Terug naar chat
          </button>

        </div>

      </div>
    );
  }

  /* =========================
     CHAT PAGE
  ========================= */

  return (
    <div className="container">

      <div className="chatbot-popup">

        {/* HEADER */}

        <div
          className="chat-header"
          style={{
            justifyContent: "space-between",
            padding: "18px 25px"
          }}
        >

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "2px"
            }}
          >

            <h2>Bring ChatBot</h2>

            <p
              className="logged-user"
              style={{
                color:
                  "rgba(255,255,255,0.6)",
                fontSize: "13px"
              }}
            >
              Ingelogd als:
              <strong> {username}</strong>
            </p>

          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px"
            }}
          >

            {username === "admin" && (

              <button
                onClick={() =>
                  setPage("admin")
                }
                style={{
                  padding: "8px 16px",
                  background:
                    "rgba(82,255,47,0.15)",
                  border:
                    "1px solid rgba(82,255,47,0.4)",
                  borderRadius: "10px",
                  color: "#b7ffb0",
                  cursor: "pointer"
                }}
              >
                Admin Panel
              </button>

            )}

            <button
              onClick={handleLogout}
              style={{
                padding: "8px 16px",
                background:
                  "rgba(255,255,255,0.08)",
                border:
                  "1px solid rgba(255,255,255,0.15)",
                borderRadius: "10px",
                color: "#ffb0b0",
                cursor: "pointer"
              }}
            >
              Uitloggen
            </button>

          </div>

        </div>

        {/* CHAT BODY */}

        <div
          className="chat-body"
          ref={chatBodyRef}
        >

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

          {messages.map((msg, index) => {

            const isBot =
              msg.sender === "bot";

            return (
              <div
                key={index}
                className={
                  isBot
                    ? "message-bot-message"
                    : "message-user-message"
                }
              >

                {isBot && (
                  <div className="bot-icon">
                    🤖
                  </div>
                )}

                <div className="message-text">
                  {msg.text}
                </div>

              </div>
            );
          })}

          {loading && (

            <div className="message-bot-message">

              <div className="bot-icon">
                🤖
              </div>

              <div className="message-text typing">
                <span></span>
                <span></span>
                <span></span>
              </div>

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
              disabled={
                loading ||
                !hasSelectedOption
              }
              type="submit"
            >
              ↑
            </button>

          </form>

        </div>

      </div>

    </div>
  );
}

export default App;
