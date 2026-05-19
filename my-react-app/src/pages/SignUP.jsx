import React from "react";
import './LoginSignup.css'

import user from 'pages/assets/user.png'
import password from 'pages/assets/password.png'
import mail from 'pages/assets/mail.png'

const LoginSignup = () => {
    return (
        <div>
            <div className="container">
                <div className="header">
                    <div className="text">Sign Up</div>
                    <div className="underline"></div>
                </div>
                </div>
                <div className="inputs">
                    <div className="input">
                        <img src={user} alt=""/>
                        <input type="text"></input>
                    </div>
                      <div className="input">
                        <img src={mail} alt=""/>
                        <input type="email"></input>
                    </div>
                      <div className="input">
                        <img src={password} alt=""/>
                        <input type="password"></input>
                    </div>
                    
                    </div>
                    </div>
    )
}

export default LoginSignup