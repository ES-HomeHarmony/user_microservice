// src/components/Home.js
import React, { useEffect } from 'react';
import axios from 'axios';
import awsCognitoConfig from '../cognitoConfig';

function Home() {
  useEffect(() => {
    const getCodeFromURL = () => {
      const params = new URLSearchParams(window.location.search);
      return params.get('code'); // Obtém o código de autorização da URL
    };

    const exchangeCodeForToken = async (code) => {
      const {
        domain,
        clientId,
        redirectSignIn,
      } = awsCognitoConfig;
    
      const params = new URLSearchParams();
      params.append('grant_type', 'authorization_code');
      params.append('client_id', clientId);
      params.append('redirect_uri', redirectSignIn);
      params.append('code', code);
    
      try {
        const response = await axios.post(`https://${domain}/oauth2/token`, params, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });
        return response.data.id_token;
      } catch (error) {
        console.error('Erro ao trocar código pelo token:', error);
        if (error.response) {
          console.error('Detalhes do erro:', error.response.data);
        }
      }
    };

    const decodeJWT = (token) => {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function (c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(jsonPayload);
    };

    const createUserInDB = async (userData) => {
      try {
        await axios.post('http://localhost:8000/users/', userData);
        console.log('Usuário salvo com sucesso!');
      } catch (error) {
        console.error('Erro ao criar usuário na base de dados:', error);
      }
    };

    const handleSignUp = async () => {
      const code = getCodeFromURL();
      if (code) {
        const idToken = await exchangeCodeForToken(code);
        if (idToken) {
          const userData = decodeJWT(idToken);
          const newUser = {
            cognito_id: userData.sub,
            email: userData.email,
            name: userData.name,
          };
          alert(userData);
          await createUserInDB(newUser);
        }
      }
    };

    handleSignUp();
  }, []);

  return (
    <div>
      <h1>Bem-vindo ao HomeHarmony!</h1>
      <p>Esta é a página principal.</p>
    </div>
  );
}

export default Home;