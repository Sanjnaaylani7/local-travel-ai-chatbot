"""Global test configuration.

Sets environment variables *before* the application package is imported so
that cached settings pick up test-friendly values (temporary DB, existing
vector store, lower relevance threshold).
"""
import os
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent

# Isolated temporary SQLite database for the test run.
_tmp_db = Path(tempfile.gettempdir()) / "travel_chatbot_test.db"
if _tmp_db.exists():
    _tmp_db.unlink()

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_db.as_posix()}")
os.environ.setdefault(
    "VECTOR_STORE_DIR",
    str(_ROOT / "data_pipeline" / "output" / "vector_store"),
)
os.environ.setdefault("SIMILARITY_THRESHOLD", "0.2")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")  # disable limiter in tests
os.environ.setdefault("ENABLE_METRICS", "false")
