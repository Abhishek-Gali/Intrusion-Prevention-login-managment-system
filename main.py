from fastapi import FastAPI, Form, UploadFile, File, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
import bcrypt
import mysql.connector
import shutil
import os
import subprocess
import logging
from pydantic import BaseModel
import secrets
from datetime import datetime, timedelta
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount templates directory
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token configuration
TOKEN_SECRET = "your-secret-key"  # Hardcoded since .env is not used
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Path to the virtual environment's Python executable
PYTHON_EXECUTABLE = "./venv/Scripts/python.exe"

# Database connection
def get_db():
    try:
        db = mysql.connector.connect(
            host="localhost",  # Updated as per your requirement
            port=3306,
            user="root",
            password="root",
            database="intrusion_prevention_system"
        )
        logger.info("Database connection successful!")
        return db
    except mysql.connector.Error as err:
        logger.error(f"Database connection failed: {err}")
        raise

# Token functions
def create_token(username: str):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE users SET token = %s, token_expires_at = %s WHERE username = %s",
            (token, expires_at, username)
        )
        db.commit()
        cursor.close()
        db.close()
        return token
    except mysql.connector.Error as err:
        logger.error(f"Database error storing token: {err}")
        raise HTTPException(status_code=500, detail="Database error")

from fastapi import Request

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT username FROM users WHERE token = %s AND token_expires_at > %s",
            (token, datetime.utcnow())
        )
        user = cursor.fetchone()
        cursor.close()
        db.close()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user["username"]
    except mysql.connector.Error as err:
        logger.error(f"Database error verifying token: {err}")
        raise HTTPException(status_code=500, detail="Database error")


# Validate username
def is_safe_username(username: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9_-]{3,50}$', username))

# Signup endpoint
@app.post("/signup")
async def signup(
    firstName: str = Form(...),
    lastName: str = Form(...),
    username: str = Form(...),
    dob: str = Form(...),
    phoneNumber: str = Form(...),
    gmail: str = Form(...),
    password: str = Form(...),
    photo1: UploadFile = File(None),
    photo2: UploadFile = File(None),
    photo3: UploadFile = File(None),
    photo4: UploadFile = File(None),
    photo5: UploadFile = File(None),
    photo6: UploadFile = File(None),
    photo7: UploadFile = File(None),
    photo8: UploadFile = File(None),
    photo9: UploadFile = File(None),
    photo10: UploadFile = File(None),
    photo11: UploadFile = File(None),
    photo12: UploadFile = File(None),
    photo13: UploadFile = File(None),
    photo14: UploadFile = File(None),
    photo15: UploadFile = File(None),
    photo16: UploadFile = File(None),
    photo17: UploadFile = File(None),
    photo18: UploadFile = File(None),
    photo19: UploadFile = File(None),
    photo20: UploadFile = File(None),
    photo21: UploadFile = File(None),
    photo22: UploadFile = File(None),
    photo23: UploadFile = File(None),
    photo24: UploadFile = File(None),
    photo25: UploadFile = File(None),
    photo26: UploadFile = File(None),
    photo27: UploadFile = File(None),
    photo28: UploadFile = File(None),
    photo29: UploadFile = File(None),
    photo30: UploadFile = File(None)
):
    logger.info(f"Attempting to register user: {username}")
    if not is_safe_username(username):
        return JSONResponse(status_code=400, content={"error": "Invalid username. Use 3-50 alphanumeric characters, underscores, or hyphens."})

    # Check for existing username
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            cursor.close()
            db.close()
            return JSONResponse(status_code=400, content={"error": "Username already exists, choose another."})
        if os.path.exists(f"dataset/{username}"):
            cursor.close()
            db.close()
            return JSONResponse(status_code=400, content={"error": "Username already exists in dataset, choose another."})
    except mysql.connector.Error as err:
        logger.error(f"MySQL Error: {err}")
        return JSONResponse(status_code=500, content={"error": "Database error"})

    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Validate and save photos
    user_folder = f"dataset/{username}"
    os.makedirs(user_folder, exist_ok=True)
    photos = [
        photo1, photo2, photo3, photo4, photo5, photo6, photo7, photo8, photo9, photo10,
        photo11, photo12, photo13, photo14, photo15, photo16, photo17, photo18, photo19, photo20,
        photo21, photo22, photo23, photo24, photo25, photo26, photo27, photo28, photo29, photo30
    ]
    for idx, photo in enumerate(photos, start=1):
        if photo:
            file_extension = os.path.splitext(photo.filename)[1].lower()
            if file_extension not in [".jpg", ".jpeg", ".png"]:
                return JSONResponse(status_code=400, content={"error": f"Photo {idx} must be JPEG or PNG"})
            if photo.size > 5 * 1024 * 1024:
                return JSONResponse(status_code=400, content={"error": f"Photo {idx} exceeds 5MB"})
            file_location = f"{user_folder}/{idx}.jpg"
            with open(file_location, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)

    # Insert user into database
    try:
        cursor.execute('''
            INSERT INTO users (first_name, last_name, username, dob, phone_number, gmail, password, failed_attempts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (firstName, lastName, username, dob, phoneNumber, gmail, hashed_password, 0))
        db.commit()
        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        logger.error(f"MySQL Error during signup: {err}")
        return JSONResponse(status_code=500, content={"error": f"Database error: {err}"})

    # Trigger asynchronous model retraining
    try:
        subprocess.Popen([PYTHON_EXECUTABLE, "train model.py"])
        logger.info("Started model retraining")
    except Exception as e:
        logger.error(f"Model training initiation failed: {str(e)}")
        return JSONResponse(status_code=500, content={"error": f"Model training initiation failed: {str(e)}"})

    return JSONResponse(status_code=200, content={"message": "User registered successfully!"})

# Login endpoint
class LoginRequest(BaseModel):
    username: str
    password: str

from fastapi.responses import Response

@app.post("/login")
async def login(request: LoginRequest):
    logger.info(f"Attempting to login user: {request.username}")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE username = %s', (request.username,))
    user = cursor.fetchone()

    if user is None:
        cursor.close()
        db.close()
        return JSONResponse(status_code=401, content={"error": "Username does not exist"})

    if bcrypt.checkpw(request.password.encode('utf-8'), user['password']):
        cursor.execute('UPDATE users SET failed_attempts = 0 WHERE username = %s', (request.username,))
        db.commit()
        token = create_token(request.username)
        cursor.close()
        db.close()

        # Set token in secure cookie
        response = JSONResponse(content={"message": "Credentials are correct!"})
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True if using HTTPS
            samesite="Lax",
            max_age=3600
        )
        return response
    else:
        cursor.execute('UPDATE users SET failed_attempts = failed_attempts + 1 WHERE username = %s', (request.username,))
        db.commit()
        cursor.execute('SELECT failed_attempts FROM users WHERE username = %s', (request.username,))
        failed_attempts = cursor.fetchone()['failed_attempts']
        cursor.close()
        db.close()
        if failed_attempts >= 3:
            return JSONResponse(status_code=401, content={"error": "Password is incorrect", "face_recognition_required": True})
        return JSONResponse(status_code=401, content={"error": "Password is incorrect"})


# Pre-login face recognition
@app.post("/pre-login-face")
async def pre_login_face():
    try:
        process = subprocess.Popen([PYTHON_EXECUTABLE, "recognize face.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=11)  # Match 10-second recognition with 1-second buffer
        if process.returncode != 0:
            logger.error(f"Face recognition failed: {stderr.decode()}")
            return JSONResponse(status_code=500, content={"error": "Face recognition failed"})
        if not os.path.exists("recognition_result.txt"):
            return JSONResponse(status_code=404, content={"error": "No user recognized", "signup_required": True})
        with open("recognition_result.txt", "r") as f:
            username = f.read().strip()
        if username == "Unknown":
            return JSONResponse(status_code=404, content={"error": "No user recognized", "signup_required": True})
        return JSONResponse(status_code=200, content={"username": username})
    except subprocess.TimeoutExpired:
        logger.error("Face recognition timed out")
        # Ensure a default result
        with open("recognition_result.txt", "w") as f:
            f.write("Unknown")
        return JSONResponse(status_code=404, content={"error": "No user recognized (timeout)", "signup_required": True})
    except Exception as e:
        logger.error(f"Error in pre-login face recognition: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# Capture photo endpoint
@app.post("/capture-photo")
async def capture_photo():
    try:
        process = subprocess.Popen([PYTHON_EXECUTABLE, "recognize face.py", "--capture"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate(timeout=20)  # Increased to 20 seconds to match 10-second recognition + buffer
        if process.returncode != 0:
            logger.error(f"Photo capture failed: {stderr.decode()}")
            return JSONResponse(status_code=500, content={"error": "Photo capture failed"})
        if os.path.exists("temp.jpg"):
            return JSONResponse(status_code=200, content={"message": "Photo captured"})
        return JSONResponse(status_code=500, content={"error": "Failed to capture photo"})
    except subprocess.TimeoutExpired:
        logger.error("Photo capture timed out")
        return JSONResponse(status_code=500, content={"error": "Photo capture timed out"})
    except Exception as e:
        logger.error(f"Error capturing photo: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# Move photo to user's folder after recognition
@app.post("/move-photo")
async def move_photo(username: str = Form(...)):
    if not is_safe_username(username):
        return JSONResponse(status_code=400, content={"error": "Invalid username"})
    user_folder = f"dataset/{username}"
    if not os.path.exists(user_folder):
        return JSONResponse(status_code=404, content={"error": "User not found"})
    
    # Find next photo index
    existing_photos = [int(f.split('.')[0]) for f in os.listdir(user_folder) if f.endswith('.jpg')]
    next_index = max(existing_photos, default=0) + 1
    file_location = f"{user_folder}/{next_index}.jpg"
    
    try:
        if os.path.exists("temp.jpg"):
            shutil.move("temp.jpg", file_location)
            return JSONResponse(status_code=200, content={"message": "Photo moved to user's folder"})
        return JSONResponse(status_code=500, content={"error": "Temporary photo not found"})
    except Exception as e:
        logger.error(f"Error moving photo: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# Liveness check
@app.post("/liveness-check")
async def liveness_check():
    try:
        process = subprocess.Popen([PYTHON_EXECUTABLE, "recognize face.py", "--liveness"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logger.error(f"Liveness check failed: {stderr.decode()}")
            return JSONResponse(status_code=401, content={"error": "Liveness check failed"})
        with open("liveness_result.txt", "r") as f:
            result = f.read().strip()
        if result != "LivenessPassed":
            return JSONResponse(status_code=401, content={"error": "Liveness check failed"})
        return JSONResponse(status_code=200, content={"message": "Liveness verified"})
    except Exception as e:
        logger.error(f"Error in liveness check: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# Serve protected dashboard
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(username: str = Depends(get_current_user)):
    with open("templates/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)