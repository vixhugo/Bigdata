import sys
import os

# Ensure backend directory is in sys.path for Vercel Serverless Function runtime
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import FastAPI app at top level for Vercel Python AST analysis
from app.main import app  # type: ignore # pyright: ignore # noqa: E402

handler = app
