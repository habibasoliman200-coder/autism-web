import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'calmband.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # CHANGE THIS in production (environment variable). Used to sign login tokens.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    JWT_EXPIRES_HOURS = 24 * 7
    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "ml" / "model.joblib"))
    USE_AI = os.getenv("USE_AI", "1") == "1"   # set USE_AI=0 to force the rule-based logic

    # --- decision settings (same meaning as your original file) ---
    BASELINE_WINDOW = 300
    MIN_BASELINE_READINGS = 30
    RATIO_EARLY = 1.15
    RATIO_DISTRESS = 1.30
    MOTION_HIGH = 0.7
    MIN_ALERT_LENGTH = 3
    SMOOTHING = 3            # same decision N times in a row before the UI state changes
    AI_EARLY_RATIO = 0.6     # AI: risk >= threshold*0.6 -> early, >= threshold -> distress
