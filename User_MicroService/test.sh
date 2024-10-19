#!/bin/bash

# Configurar a variável de ambiente para testes
export TESTING=1

source .env/bin/activate
pip install -r requirements.txt

docker compose -f docker-compose.test.yml up -d
sleep 7

# Rodar os testes com pytest
pytest --disable-warnings

# Verificar o status de saída do pytest
if [ $? -eq 0 ]; then
  echo "All tests have passed!"
else
  echo "Some test have failed!"
fi