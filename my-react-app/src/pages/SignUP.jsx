import React, { useState } from "react";
import "./LoginSignup.css";

import user from "pages/assets/user.png";
import passwordImg from "pages/assets/password.png";

const LoginSignup = () => {


const [username, setUsername] = useState("");
const [password, setPassword] = useState("");

const register = async () => {
    try {

        const response = await fetch(
            "http://localhost:8000/register",
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

        if (data.success) {
            alert("Gebruiker aangemaakt");
        } else {
            alert(data.error || "Registratie mislukt");
        }

    } catch (error) {
        console.error(error);
        alert("Backend niet bereikbaar");
    }
};

const login = async () => {
    try {

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

        if (data.success) {
            alert("Login succesvol");
        } else {
            alert(data.message);
        }

    } catch (error) {
        console.error(error);
        alert("Backend niet bereikbaar");
    }
};

return (
    <div className="container">

        <div className="header">
            <div className="text">Sign Up / Login</div>
            <div className="underline"></div>
        </div>

        <div className="inputs">

            <div className="input">
                <img src={user} alt="" />
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />
            </div>

            <div className="input">
                <img src={passwordImg} alt="" />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
            </div>

        </div>

        <div className="submit-container">

            <div className="submit" onClick={register}>
                Sign Up
            </div>

            <div className="submit" onClick={login}>
                Login
            </div>

        </div>

    </div>
);


};

export default LoginSignup;
