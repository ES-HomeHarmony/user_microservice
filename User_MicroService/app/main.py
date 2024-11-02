from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal
from app.models.models import Base
from app.routes import user_routes, auth_routes
from app.services.auth_service import decode_jwt
from kafka import KafkaConsumer, KafkaProducer
import threading
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Inclui as rotas de usuários
app.include_router(user_routes.router)
app.include_router(auth_routes.router)

# Kafka consumer setup
consumer = KafkaConsumer(
    'user-validation-request',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    auto_offset_reset='earliest',
    group_id='user_group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

print("Connected to Kafka")

def process_validation_request():
    try:
        for message in consumer:
            request_data = message.value
            if request_data.get("action") == "validate_token":
                access_token = request_data.get("access_token")
                
                user = decode_jwt(access_token, access_token)

                # Replace with your actual token validation logic
                validated_user = {
                    "cognito_id": user.get("sub"),
                }

                producer.send('user-validation-response', validated_user)
                
    except Exception as e:
        print(f"Error in Kafka consumer loop: {e}")

# Start Kafka consumer in a background thread when the FastAPI app starts
@app.on_event("startup")
def startup_event():
    try:
        thread = threading.Thread(target=process_validation_request, daemon=True)
        thread.start()
        print("Kafka consumer thread started")
    except Exception as e:
        print(f"Error starting Kafka consumer thread: {e}")
