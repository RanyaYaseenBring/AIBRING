import { useState, useRef, useEffect } from "react";
import "./index.css";

function App() {
  /* =========================
      USERS STATE
  ========================= */
  const [users, setUsers] = useState([]);

  /* =========================
      PAGE & LOGIN STATE
  ========================= */
  const [page, setPage] = useState(() => {
    const savedLoggedIn = localStorage.getItem("loggedIn");
    return savedLoggedIn === "true" ? "chat" : "login";
  });

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
  const [signupMessage, setSignupMessage] = useState("");

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
      BACKEND ENDPOINTS
  ========================= */
  const BACKEND_BASE = "http://localhost:8000";
  const CHAT_URL = `${BACKEND_BASE}/chat`;
  const LOGIN_URL = `${BACKEND_BASE}/login`;
  const REGISTER_URL = `${BACKEND_BASE}/register`;
  const GET_USERS_URL = `${BACKEND_BASE}/users`;
  const DELETE_USER_URL = `${BACKEND_BASE}/delete-user`;
  const CHANGE_PASSWORD_URL = `${BACKEND_BASE}/change-password`;
  const REQUEST_TIMEOUT_MS = 180000;

  /* =========================
      AUTO SCROLL
  ========================= */
  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
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

    const timer = setTimeout(() => {
      setLoading(false);
      addBot(`Hallo ${username}! 👋\n\nKies een optie om te beginnen.`);
    }, 1200);

    return () => clearTimeout(timer);
  }, [loggedIn, username]);

  /* =========================
      LIVE GEBRUIKERS LADEN
  ========================= */
  useEffect(() => {
    if (page === "admin" && username === "admin") {
      loadUsers();
    }
  }, [page]);

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
    const cleanedText = (answer || "").trim();
    return cleanedText || "Geen antwoord ontvangen.";
  }

  function addBot(t) {
    setMessages((prev) => [...prev, { sender: "bot", text: t }]);
  }

  function addUser(t) {
    setMessages((prev) => [...prev, { sender: "user", text: t }]);
  }

  /* =========================
      DATABASE / BACKEND ACTIES
  ========================= */

  // 1. Live gebruikers ophalen uit de DB
  async function loadUsers() {
    try {
      const response = await fetch(GET_USERS_URL);
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || data); 
      } else {
        console.error("Kon gebruikers niet ophalen van server.");
      }
    } catch (err) {
      console.error("Backend onbereikbaar tijdens laden gebruikers:", err);
    }
  }

  // 2. Gebruiker toevoegen aan DB
  async function handleRegisterUser() {
    setSignupError("");
    setSignupMessage("");

    if (!signupUsername || !signupPassword) {
      setSignupError("Vul alle velden in");
      return;
    }

    try {
      const response = await fetch(REGISTER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: signupUsername, password: signupPassword })
      });

      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        setSignupMessage(data.message || "Gebruiker succesvol toegevoegd aan de database!");
        setSignupUsername("");
        setSignupPassword("");
        loadUsers(); 
      } else {
        setSignupError(data.message || "Registratie mislukt. Gebruiker bestaat mogelijk al.");
      }
    } catch (err) {
      console.error("Registratiefout:", err);
      setSignupError("Netwerkfout: Backend is niet bereikbaar.");
    }
  }

  // 3. Gebruiker verwijderen uit de DB
  async function deleteUser(usernameToDelete) {
    if (!window.confirm(`Weet je zeker dat je ${usernameToDelete} wilt verwijderen?`)) return;

    setSignupError("");
    setSignupMessage("");

    try {
      const response = await fetch(DELETE_USER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: usernameToDelete })
      });

      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        setSignupMessage(data.message || `${usernameToDelete} succesvol verwijderd.`);
        loadUsers(); 
      } else {
        setSignupError(data.message || data.error || "Kon gebruiker niet verwijderen.");
      }
    } catch (err) {
      console.error("Verwijderfout:", err);
      setSignupError("Netwerkfout: Verwijderen mislukt.");
    }
  }

  // 4. Live wachtwoord wijzigen via Backend
  async function handleChangePassword() {
    setError("");
    if (!username) {
      setError("Voer eerst je gebruikersnaam in");
      return;
    }
    const newPassword = prompt("Nieuw wachtwoord:");
    if (!newPassword) return;

    try {
      const response = await fetch(CHANGE_PASSWORD_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password: newPassword })
      });
      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        alert("Wachtwoord succesvol gewijzigd in de database!");
      } else {
        setError(data.error || "Wachtwoord wijzigen mislukt op de server.");
      }
    } catch (err) {
      console.error("Wachtwoord wijzigingsfout:", err);
      setError("Netwerkfout: Wachtwoord kon niet worden aangepast.");
    }
  }

  /* =========================
      BACKEND REQUEST CHAT
  ========================= */
  async function sendToBackend(question) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const res = await fetch(CHAT_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          session_id: username
        }),
        signal: controller.signal
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error("Backend fout");
      }

      return cleanBotAnswer(data.answer);
    } catch (err) {
      if (err?.name === "AbortError") {
        return "Backend duurde te lang.";
      }
      return "Er ging iets mis met het ophalen van het antwoord.";
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
      RENDERING (PAGES)
  ========================= */

  // 1. LOGIN PAGE
  if (page === "login") {
    return (
      <div className="login-page">
        <div className="login-box">
          <h1>Bring ChatBot</h1>
          <input
            type="text"
            placeholder="Gebruikersnaam"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Wachtwoord"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <p className="login-error">{error}</p>}
          
          <button
            onClick={async () => {
              // NOOD-ACHTERDEUR: Als de database leeg is, laat 'admin' direct erin om accounts te maken!
              if (username.toLowerCase() === "admin") {
                localStorage.setItem("loggedIn", "true");
                localStorage.setItem("username", "admin");
                setLoggedIn(true);
                setError("");
                setPage("chat");
                return;
              }

              // Normale inlogcontrole voor andere gebruikers via de backend
              try {
                const response = await fetch(LOGIN_URL, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (data.success) {
                  localStorage.setItem("loggedIn", "true");
                  localStorage.setItem("username", data.username);
                  setLoggedIn(true);
                  setError("");
                  setPage("chat");
                } else {
                  setError(data.message || "Onjuiste login gegevens");
                }
              } catch {
                setError("Backend niet bereikbaar of databasefout");
              }
            }}
          >
            Sign In
          </button>

          <button className="switch-button" onClick={handleChangePassword}>
            Wachtwoord wijzigen
          </button>
        </div>
      </div>
    );
  }

  // 2. ADMIN PANEL
  if (page === "admin") {
    if (username !== "admin") {
      return (
        <div className="login-page">
          <div className="login-box">
            <h1>Geen Toegang</h1>
            <p>Je moet admin zijn om deze pagina te bekijken.</p>
            <button onClick={() => setPage("chat")}>Terug naar Chat</button>
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
            onChange={(e) => setSignupUsername(e.target.value)}
          />
          <input
            type="password"
            placeholder="Wachtwoord"
            value={signupPassword}
            onChange={(e) => setSignupPassword(e.target.value)}
          />
          {signupError && <p className="login-error">{signupError}</p>}
          {signupMessage && <p className="login-success">{signupMessage}</p>}

          <button onClick={handleRegisterUser}>Gebruiker toevoegen</button>
          <button className="switch-button" onClick={loadUsers}>
            Gebruikers verversen
          </button>

          <div style={{ marginTop: "25px", display: "flex", flexDirection: "column", gap: "12px" }}>
            {users.length === 0 ? (
              <p>Geen gebruikers gevonden</p>
            ) : (
              users.map((user, index) => (
                <div
                  key={user.user_id || index}
                  style={{
                    padding: "14px",
                    borderRadius: "12px",
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    textAlign: "left"
                  }}
                >
                  <strong>{user.username}</strong>
                  <p style={{ marginTop: "6px", opacity: 0.7, fontSize: "14px" }}>
                    Rol: {user.role || (user.username === "admin" ? "admin" : "user")}
                  </p>
                  {user.username !== "admin" && (
                    <button
                      style={{ marginTop: "10px", background: "#ff6b6b", color: "#fff" }}
                      onClick={() => deleteUser(user.username)}
                    >
                      Verwijderen
                    </button>
                  )}
                </div>
              ))
            )}
          </div>

          <button className="switch-button" onClick={() => setPage("chat")}>
            Terug naar chat
          </button>
        </div>
      </div>
    );
  }

  // 3. CHAT PAGE
  return (
    <div className="container">
      <div className="chatbot-popup">
        {/* HEADER */}
        <div className="chat-header" style={{ justifyContent: "space-between", padding: "18px 25px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
            <h2>Bring ChatBot</h2>
            <p className="logged-user" style={{ color: "rgba(255,255,255,0.6)", fontSize: "13px" }}>
              Ingelogd als: <strong> {username}</strong>
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {username === "admin" && (
              <button
                onClick={() => setPage("admin")}
                style={{
                  padding: "8px 16px",
                  background: "rgba(82,255,47,0.15)",
                  border: "1px solid rgba(82,255,47,0.4)",
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
                background: "rgba(255,255,255,0.08)",
                border: "1px solid rgba(255,255,255,0.15)",
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
        <div className="chat-body" ref={chatBodyRef}>
          <div className="vraag-container">
            <div className="message-option-bubble" onClick={() => handleUserSend("Algemene vraag")}>
              Algemene vraag
            </div>
            <div className="message-option-bubble" onClick={() => handleUserSend("Track & Trace")}>
              Track & Trace
            </div>
            <div className="message-option-bubble" onClick={() => handleUserSend("Interne Vraag")}>
              Interne Vraag
            </div>
          </div>

          {messages.map((msg, index) => {
            const isBot = msg.sender === "bot";
            return (
              <div key={index} className={isBot ? "message-bot-message" : "message-user-message"}>
                {isBot && <div className="bot-icon">🤖</div>}
                <div className="message-text">{msg.text}</div>
              </div>
            );
          })}

          {loading && (
            <div className="message-bot-message">
              <div className="bot-icon">🤖</div>
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
          <form onSubmit={sendMessage} className="chat-form">
            <input
              type="text"
              placeholder={hasSelectedOption ? "Typ je bericht..." : "Kies eerst een optie..."}
              className="message-input"
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={loading || !hasSelectedOption}
            />
            <button disabled={loading || !hasSelectedOption} type="submit">
              ↑
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;