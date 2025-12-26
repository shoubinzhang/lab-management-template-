"""
Configuration module to avoid circular imports
"""
import os
from datetime import timedelta

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lab.db")

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# CORS Configuration
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://172.30.81.103:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://172.30.81.103:8080",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://172.30.81.103:8001",
    "http://localhost:8002",
    "http://127.0.0.1:8002",
    "http://172.30.81.103:8002",
]