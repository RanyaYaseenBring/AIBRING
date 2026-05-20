import { useState } from "react";

import {
  BrowserRouter,
  Routes,
  Route,
  useNavigate
} from "react-router-dom";

import "./index.css";

/* =========================
   LOGIN PAGE
========================= */

function LoginPage() {

  const navigate =
    useNavigate();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  async function handleLogin() {

    try {

      const res = await fetch(

        "http://127.0.0.1:8000/login",

        {

          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({

            email,
            password

          })

        }

      );

      const data =
        await res.json();

      if (data.success) {

        navigate("/chat");

      } else {

        setError(
          "Onjuiste login gegevens"
        );
      }

    } catch {

      setError(
        "Kan geen verbinding maken met backend"
      );
    }
  }

  return (

    <div className="login-page">

      <div className="login-box">

        <h1>
          Bring ChatBot
        </h1>

        <input
          type="email"
          placeholder="Email"

          value={email}

          onChange={(e) =>
            setEmail(
              e.target.value
            )
          }
        />

        <input
          type="password"
          placeholder="Wachtwoord"

          value={password}

          onChange={(e) =>
            setPassword(
              e.target.value
            )
          }
        />

        {error && (

          <p className="login-error">
            {error}
          </p>

        )}

        <button
          onClick={handleLogin}
        >
          Sign In
        </button>

        {/* CREATE ACCOUNT */}

        <button
          className="switch-button"

          onClick={() =>
            navigate("/signup")
          }
        >
          Create Account
        </button>

      </div>

    </div>
  );
}

/* =========================
   SIGNUP PAGE
========================= */

function SignupPage() {

  const navigate =
    useNavigate();

  const [username, setUsername] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [error, setError] =
    useState("");

  async function handleSignup() {

    try {

      const res = await fetch(

        "http://127.0.0.1:8000/signup",

        {

          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({

            username,
            email,
            password

          })

        }

      );

      const data =
        await res.json();

      if (data.success) {

        navigate("/");

      } else {

        setError(
          data.message ||
          "Signup mislukt"
        );
      }

    } catch {

      setError(
        "Kan geen verbinding maken met backend"
      );
    }
  }

  return (

    <div className="login-page">

      <div className="login-box">

        <h1>
          Create Account
        </h1>

        {/* USERNAME */}

        <input
          type="text"
          placeholder="Username"

          value={username}

          onChange={(e) =>
            setUsername(
              e.target.value
            )
          }
        />

        {/* EMAIL */}

        <input
          type="email"
          placeholder="Email"

          value={email}

          onChange={(e) =>
            setEmail(
              e.target.value
            )
          }
        />

        {/* PASSWORD */}

        <input
          type="password"
          placeholder="Wachtwoord"

          value={password}

          onChange={(e) =>
            setPassword(
              e.target.value
            )
          }
        />

        {error && (

          <p className="login-error">
            {error}
          </p>

        )}

        <button
          onClick={handleSignup}
        >
          Sign Up
        </button>

        <button
          className="switch-button"

          onClick={() =>
            navigate("/")
          }
        >
          Already have an account? Login
        </button>

      </div>

    </div>
  );
}

/* =========================
   CHAT PAGE
========================= */

function ChatPage() {

  return (

    <div className="chat-page">

      <h1>
        Bring ChatBot
      </h1>

    </div>
  );
}

/* =========================
   APP
========================= */

function App() {

  return (

    <BrowserRouter>

      <Routes>

        {/* LOGIN */}

        <Route
          path="/"
          element={<LoginPage />}
        />

        {/* SIGNUP */}

        <Route
          path="/signup"
          element={<SignupPage />}
        />

        {/* CHAT */}

        <Route
          path="/chat"
          element={<ChatPage />}
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;