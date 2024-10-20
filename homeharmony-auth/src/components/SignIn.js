// src/components/SignIn.js
import React from 'react';
import awsCognitoConfig from '../cognitoConfig';

function SignIn() {
  const handleSignIn = () => {
    const {
      domain,
      clientId,
      redirectSignIn,
      scopes,
      responseType,
    } = awsCognitoConfig;

    const loginUrl = `https://${domain}/oauth2/authorize?identity_provider=COGNITO&redirect_uri=${encodeURIComponent(redirectSignIn)}&response_type=${responseType}&client_id=${clientId}&scope=${scopes.join(' ')}`;

    window.location.href = loginUrl;
  };

  return (
    <div>
      <h2>Login</h2>
      <button onClick={handleSignIn}>Login com Hosted UI</button>
    </div>
  );
}

export default SignIn;