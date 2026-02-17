from fastapi import FastAPI, APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import bcrypt
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT config
JWT_SECRET = os.environ.get('JWT_SECRET', 'bala-lab-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"

# Upload directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# ---- Models ----

class UserRegister(BaseModel):
    email: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: str

class ReportResponse(BaseModel):
    id: str
    file_name: str
    original_name: str
    file_type: str
    file_size: int
    user_email: str
    uploaded_by: str
    created_at: str

class TokenResponse(BaseModel):
    token: str
    user: UserResponse

# ---- Auth Helpers ----

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ---- Auth Endpoints ----

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(data: UserRegister):
    existing = await db.users.find_one({"email": data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    user_doc = {
        "id": user_id,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "role": data.role if data.role in ["admin", "user"] else "user",
        "created_at": now,
    }
    await db.users.insert_one(user_doc)

    token = create_token(user_id, data.email, user_doc["role"])
    return TokenResponse(
        token=token,
        user=UserResponse(id=user_id, email=data.email, role=user_doc["role"], created_at=now)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["id"], user["email"], user["role"])
    return TokenResponse(
        token=token,
        user=UserResponse(id=user["id"], email=user["email"], role=user["role"], created_at=user["created_at"])
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user=Depends(get_current_user)):
    return UserResponse(id=user["id"], email=user["email"], role=user["role"], created_at=user["created_at"])

# ---- Report Endpoints ----

@api_router.post("/reports/upload", response_model=ReportResponse)
async def upload_report(
    file: UploadFile = File(...),
    user_email: str = Form(...),
    admin=Depends(require_admin),
):
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}")

    # Read file and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")

    # Check if target user exists
    target_user = await db.users.find_one({"email": user_email}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User with this email not found")

    # Generate unique filename
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_name

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine file type
    file_type = "pdf" if ext == ".pdf" else "image"

    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    report_doc = {
        "id": report_id,
        "file_name": unique_name,
        "original_name": file.filename,
        "file_type": file_type,
        "file_size": len(content),
        "file_path": str(file_path),
        "user_email": user_email,
        "user_id": target_user["id"],
        "uploaded_by": admin["id"],
        "created_at": now,
    }
    await db.reports.insert_one(report_doc)

    return ReportResponse(
        id=report_id,
        file_name=unique_name,
        original_name=file.filename,
        file_type=file_type,
        file_size=len(content),
        user_email=user_email,
        uploaded_by=admin["email"],
        created_at=now,
    )

@api_router.get("/reports", response_model=List[ReportResponse])
async def list_reports(user=Depends(get_current_user)):
    if user["role"] == "admin":
        reports = await db.reports.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    else:
        reports = await db.reports.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(1000)

    result = []
    for r in reports:
        # Get uploader email
        uploader = await db.users.find_one({"id": r.get("uploaded_by", "")}, {"_id": 0})
        uploader_email = uploader["email"] if uploader else "unknown"
        result.append(ReportResponse(
            id=r["id"],
            file_name=r["file_name"],
            original_name=r["original_name"],
            file_type=r["file_type"],
            file_size=r["file_size"],
            user_email=r["user_email"],
            uploaded_by=uploader_email,
            created_at=r["created_at"],
        ))
    return result

@api_router.get("/reports/{report_id}/download")
async def download_report(report_id: str, user=Depends(get_current_user)):
    report = await db.reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Security: users can only download their own reports
    if user["role"] != "admin" and report["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    file_path = Path(report["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=str(file_path),
        filename=report["original_name"],
        media_type="application/octet-stream",
    )

@api_router.get("/reports/{report_id}/preview")
async def preview_report(report_id: str, user=Depends(get_current_user)):
    report = await db.reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if user["role"] != "admin" and report["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    file_path = Path(report["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    # Determine content type
    ext = Path(report["file_name"]).suffix.lower()
    content_types = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
    }
    media_type = content_types.get(ext, "application/octet-stream")

    return FileResponse(path=str(file_path), media_type=media_type)

@api_router.delete("/reports/{report_id}")
async def delete_report(report_id: str, admin=Depends(require_admin)):
    report = await db.reports.find_one({"id": report_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Delete file
    file_path = Path(report["file_path"])
    if file_path.exists():
        file_path.unlink()

    await db.reports.delete_one({"id": report_id})
    return {"message": "Report deleted successfully"}

@api_router.get("/users", response_model=List[UserResponse])
async def list_users(admin=Depends(require_admin)):
    users = await db.users.find({"role": "user"}, {"_id": 0}).to_list(1000)
    return [
        UserResponse(id=u["id"], email=u["email"], role=u["role"], created_at=u["created_at"])
        for u in users
    ]

@api_router.get("/")
async def root():
    return {"message": "Bala Lab API is running"}

# ---- Middleware ----

cors_origins = [o.strip() for o in os.environ.get('CORS_ORIGINS', '*').split(',') if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False if cors_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "online", "message": "Bala Lab Server is running"}

# Include router
app.include_router(api_router)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
