// src/components/SignUp.js
import React from 'react';
import awsCognitoConfig from '../cognitoConfig';

function SignUp() {
  const handleSignUp = () => {
    const {
      domain,
      clientId,
      redirectSignIn,
      scopes,
      responseType,
    } = awsCognitoConfig;

    // URL do Hosted UI para registro
    const signupUrl = `https://${domain}/signup?response_type=${responseType}&client_id=${clientId}&redirect_uri=${redirectSignIn}&scope=${scopes.join(' ')}`;

    window.location.href = signupUrl;
  };

  return (
    <div>
      <h2>Registrar</h2>
      <button onClick={handleSignUp}>Registrar com Hosted UI</button>
    </div>
  );
}

export default SignUp;