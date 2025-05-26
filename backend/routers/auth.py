from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging
import traceback

from db.session import get_db
from models.user import User
from schemas.user import UserCreate, User as UserSchema, Token
from utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserSchema)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Tentativo di registrazione per l'email: {user_data.email}")
    try:
        # Verifica se l'utente esiste già
        logger.debug("Verifico se l'utente esiste già")
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            logger.warning(f"Tentativo di registrazione con email già esistente: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Crea il nuovo utente
        logger.debug("Creo il nuovo utente")
        hashed_password = get_password_hash(user_data.password)
        logger.debug("Password hashata con successo")
        
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=1
        )
        logger.debug(f"User object created: {db_user.__dict__}")
        
        try:
            db.add(db_user)
            logger.debug("User added to session")
            db.commit()
            logger.debug("Changes committed to database")
            db.refresh(db_user)
            logger.debug(f"User refreshed from database: {db_user.__dict__}")
            logger.info(f"Successfully created user with email: {user_data.email}")
            return db_user
        except Exception as db_error:
            db.rollback()
            logger.error(f"Database error during user creation: {str(db_error)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user in database"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore inaspettato durante la registrazione: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during signup"
        )

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        logger.debug(f"Attempting login for user: {form_data.username}")
        
        # Verifica le credenziali
        user = db.query(User).filter(User.email == form_data.username).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Genera il token di accesso
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        logger.info(f"Successful login for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login"
        ) 