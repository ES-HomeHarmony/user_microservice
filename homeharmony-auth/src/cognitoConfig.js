// src/cognitoConfig.js
const awsCognitoConfig = {
  region: 'eu-north-1',  // Exemplo: 'us-east-1'
  userPoolId: 'eu-north-1_BZVwENxbX',
  clientId: '1ks0163ckccdfje0a1h7h78ffl',
  redirectSignIn: 'http://localhost:3000',
  redirectSignOut: 'http://localhost:3000',
  domain: 'homeharmony.auth.eu-north-1.amazoncognito.com',
  scopes: ['openid', 'email', 'phone', 'profile'],
  responseType: 'code' // ou 'token' dependendo do que você precisar
};

export default awsCognitoConfig;