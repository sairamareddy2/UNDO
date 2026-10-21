import os
import sys
import tempfile
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Configure database for serverless writable temp directory
if not os.environ.get("DATABASE_URL") or "./undo.db" in os.environ.get("DATABASE_URL", ""):
    temp_db_path = Path(tempfile.gettempdir()) / "undo.db"
    # Format sqlite URL with forward slashes
    os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path.as_posix()}"

os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("DEBUG", "False")

from app.database import init_db
init_db()

from app.main import app
