import React, { useState } from "react";

const LoginSignup = () => {

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const login = async () => {

        const response = await fetch(
            "http://localhost:8000/login",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username,
                    password
                })
            }
        );

        const data = await response.json();

        console.log(data);
    };

    return (
        <div className="login-container">

            <h1>Login</h1>

            <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
            />

            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />

            <button onClick={login}>
                Login
            </button>

        </div>
    );
};

export default LoginSignup;