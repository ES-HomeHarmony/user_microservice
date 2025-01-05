from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal
from app.models.models import Base, User
from app.routes import user_routes, auth_routes
from app.services.auth_service import decode_jwt
from kafka import KafkaConsumer, KafkaProducer
import threading
import json
import os
import uuid

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

# New Kafka consumer for user creation
user_creation_consumer = KafkaConsumer(
    'user-creation-request',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    auto_offset_reset='earliest',
    group_id='user_creation_group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# Kafka consumer to tenant data
tenant_consumer = KafkaConsumer(
    'tenant_info_request',
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    auto_offset_reset='earliest',
    group_id='tenant_group',
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

def handle_user_creation():
    for message in user_creation_consumer:
        request_data = message.value
        if request_data.get("action") == "create_user":
            user_data = request_data.get("user_data")
            print(f"Creating user: {user_data}")

            #se o user já estiver cirado devolve o cognitoid
            db = SessionLocal()
            user = db.query(User).filter(User.email == user_data["email"]).first()

            if user:
                print(f"User already exists with cognito_id: {user.cognito_id}")
                #change the user role to tenant
                user.role = "tenant"
                db.commit()
                db.refresh(user)
                producer.send('user-creation-response', {"cognito_id": user.cognito_id})
                db.close()
            else:

                new_cognito_id = str(uuid.uuid4())

                db_user = User(
                    cognito_id = new_cognito_id, # Replace with actual ID from user creation logic
                    name=user_data["name"],
                    email=user_data["email"],
                    role="tenant"
                )

                db = SessionLocal()
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
                db.close()

                try:
                    cognito_id = db_user.cognito_id 

                    print(f"User created with cognito_id: {cognito_id}")
                    # Send confirmation response back to Kafka
                    producer.send('user-creation-response', {"cognito_id": cognito_id})
                except Exception as e:
                    print(f"Error creating user: {e}")

def handle_tenant_data():
    for message in tenant_consumer:
        request_data = message.value

        print(f"Received tenant data request: {request_data}")

        if request_data.get("action") == "get_tenants_data":
            
            tenant_data = {}
            
            tenants_ids = request_data.get("tenant_ids")


            db = SessionLocal()
            for tenant_id in tenants_ids:
                tenant = db.query(User).filter(User.cognito_id == tenant_id).first()
                print(f"Tenant: {tenant}")
                tenant_data2 = []
                tenant_data2.append(tenant.name)
                tenant_data2.append(tenant.email)

                tenant_data[tenant_id] = tenant_data2
            db.close()

            producer.send('tenant_info_response', tenant_data)

# Start Kafka consumer in a background thread when the FastAPI app starts
@app.on_event("startup")
def startup_event():
    try:
        # Start thread for process_validation_request
        validation_thread = threading.Thread(target=process_validation_request, daemon=True)
        validation_thread.start()
        print("Kafka validation consumer thread started")

        # Start thread for user creation processing
        user_creation_thread = threading.Thread(target=handle_user_creation, daemon=True)
        user_creation_thread.start()
        print("Kafka user creation consumer thread started")

        tenant_consumer_thread = threading.Thread(target=handle_tenant_data, daemon=True)
        tenant_consumer_thread.start()
        print("Kafka tenant data consumer thread started")
        
    except Exception as e:
        print(f"Error starting Kafka consumer threads: {e}")
