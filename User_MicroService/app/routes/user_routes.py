from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import UserResponse, UserBase
from app.database import get_db
import app.models.models as models
from app.models.updateUser import UpdateProfileSchema
from app.services.auth_service import get_current_user
import logging
router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("user_service_user_routes")

@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserBase, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"User created: {db_user}")
    return db_user

@router.get("/user/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_profile(current_user: models.User = Depends(get_current_user)):
    """
    Fetch the current authenticated user's profile using their Cognito ID.
    """
    logger.info(f"Current user: {current_user}")
    return current_user  # Return the user profile directly from the DB (as fetched by get_current_user)

@router.put("/user/profile/update", response_model=UserResponse)
async def update_user_profile(
    profile_data: UpdateProfileSchema, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current authenticated user's profile.
    """
    # Update the current user's profile in the database
    current_user.name = profile_data.name
    current_user.email = profile_data.email
    current_user.role = profile_data.role

    # db.add(current_user)
    current_user = db.merge(current_user)
    db.commit()
    db.refresh(current_user)

    logger.info(f"User profile updated: {current_user}")
    return current_user  # Return the updated user profile