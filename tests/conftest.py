import os

# Defaults so tests run without a local .env file.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-that-is-at-least-32-chars")
os.environ.setdefault("LLM_MODEL", "test-model")
