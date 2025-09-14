from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel, Field, Session, create_engine, select
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import uuid
import os
import shutil

# ---------- MODELS ----------
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Photo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    filename: str
    caption: str | None = None
    tags: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------- SCHEMAS ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: int
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str

class UserRegisterResponse(BaseModel):
    id: int
    email: str
    is_verified: bool
    verify_token: str | None = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# ---------- CONFIG ----------
SECRET_KEY = "your-super-secret-key-change-this-in-production-123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Database setup
DATABASE_URL = "sqlite:///./photobooth.db"  # Using SQLite for simplicity
engine = create_engine(DATABASE_URL, echo=True)

# Create upload directory
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- APP SETUP ----------
app = FastAPI(title="Photobooth API", version="1.0.0")

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ---------- DATABASE ----------
def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    print("Initializing database...")
    init_db()
    print("Database initialized!")

# ---------- HELPER FUNCTIONS ----------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_user_by_email(session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    user = get_user_by_email(session, email)
    if user is None:
        raise credentials_exception
    
    return user

# ---------- ROUTES ----------

# Health check
@app.get("/")
def read_root():
    return {"message": "Photobooth API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Auth routes
@app.post("/register", response_model=UserRegisterResponse)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    print(f"Registration attempt for: {user_data.email}")
    
    # Check if user already exists
    existing_user = get_user_by_email(session, user_data.email)
    if existing_user:
        print(f"User {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_verified=False
    )
    
    try:
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"User {user_data.email} created successfully with ID: {user.id}")
    except Exception as e:
        print(f"Error creating user: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Create verification token
    verify_token = create_access_token(
        data={"sub": user.email, "type": "email_verification"},
        expires_delta=timedelta(hours=24)
    )
    
    return UserRegisterResponse(
        id=user.id,
        email=user.email,
        is_verified=user.is_verified,
        verify_token=verify_token
    )

@app.post("/login", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    print(f"Login attempt for: {form_data.username}")
    
    user = get_user_by_email(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        print("Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        print("Account deactivated")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    print(f"Login successful for: {user.email}")
    return TokenOut(access_token=access_token, token_type="bearer")

@app.post("/login-json", response_model=TokenOut)
def login_json(user_data: UserLogin, session: Session = Depends(get_session)):
    print(f"JSON Login attempt for: {user_data.email}")
    
    user = get_user_by_email(session, user_data.email)
    if not user or not verify_password(user_data.password, user.hashed_password):
        print("Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        print("Account deactivated")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    print(f"JSON Login successful for: {user.email}")
    return TokenOut(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserRead)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )

@app.post("/verify-email")
def verify_email(token: str = Form(...), session: Session = Depends(get_session)):
    payload = decode_token(token)
    if not payload or payload.get("type") != "email_verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    session.add(user)
    session.commit()
    
    return {"message": "Email verified successfully"}

@app.post("/reset-password/request")
def request_password_reset(reset_data: PasswordResetRequest, session: Session = Depends(get_session)):
    user = get_user_by_email(session, reset_data.email)
    if not user:
        return {"message": "If the email exists, a reset link will be sent"}
    
    reset_token = create_access_token(
        data={"sub": user.email, "type": "password_reset"},
        expires_delta=timedelta(hours=1)
    )
    
    return {
        "message": "Password reset token generated",
        "reset_token": reset_token
    }

@app.post("/reset-password/confirm")
def confirm_password_reset(reset_data: PasswordResetConfirm, session: Session = Depends(get_session)):
    payload = decode_token(reset_data.token)
    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    session.add(user)
    session.commit()
    
    return {"message": "Password reset successfully"}

# Photo routes
@app.post("/photos/upload")
def upload_photo(
    file: UploadFile = File(...), 
    caption: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed"
        )
    
    file_extension = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    photo = Photo(
        user_id=current_user.id,
        filename=filename,
        caption=caption
    )
    session.add(photo)
    session.commit()
    session.refresh(photo)
    
    return {
        "id": photo.id,
        "filename": photo.filename,
        "url": f"/uploads/{photo.filename}",
        "caption": photo.caption,
        "created_at": photo.created_at.isoformat()
    }

@app.get("/photos")
def list_photos(
    skip: int = 0, 
    limit: int = 20, 
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(Photo).where(Photo.user_id == current_user.id).offset(skip).limit(limit)
    photos = session.exec(statement).all()
    
    return [
        {
            "id": photo.id,
            "url": f"/uploads/{photo.filename}",
            "caption": photo.caption,
            "created_at": photo.created_at.isoformat()
        }
        for photo in photos
    ]

@app.delete("/photos/{photo_id}")
def delete_photo(
    photo_id: int, 
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    photo = session.exec(
        select(Photo).where(Photo.id == photo_id, Photo.user_id == current_user.id)
    ).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Delete file from filesystem
    file_path = os.path.join(UPLOAD_DIR, photo.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    session.delete(photo)
    session.commit()
    
    return {"message": "Photo deleted successfully"}

# ---------- STATIC FILES ----------
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")