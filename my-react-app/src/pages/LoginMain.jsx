import React from "react";
import "./login.css";

const LoginSignup = () => {

    return (

        <div className="login-container">

            <h1>Login</h1>

            <input
                type="text"
                placeholder="Username"
            />

            <input
                type="password"
                placeholder="Password"
            />

            <button>
                Login
            </button>

        </div>
    );
};

export default LoginSignup;