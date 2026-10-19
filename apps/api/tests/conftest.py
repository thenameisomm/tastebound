from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SESSION_SECRET", "test-secret-not-for-production")
os.environ.setdefault("QLOO_API_KEY", "")
os.environ.setdefault("OLLAMA_API_KEY", "")
