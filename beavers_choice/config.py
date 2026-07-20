from pathlib import Path
import os

from sqlalchemy import create_engine

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # Streamlit Cloud can inject secrets without python-dotenv installed.
    pass

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
DATA_DIR = REPO_ROOT / "data"
INPUT_DATA_DIR = DATA_DIR / "input"
RUNTIME_DIR = DATA_DIR / "runtime"
OUTPUT_DIR = REPO_ROOT / "outputs"
DATABASE_PATH = RUNTIME_DIR / "munder_difflin.db"
DB_ENGINE = create_engine(f"sqlite:///{DATABASE_PATH}")

MODEL_ID = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("UDACITY_OPENAI_API_KEY")
if _api_key and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = _api_key

# Vocareum keys need the Vocareum base URL; standard OpenAI keys use the default API.
API_BASE = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE") or (
    "https://openai.vocareum.com/v1"
    if (_api_key or "").startswith("voc-")
    else "https://api.openai.com/v1"
)
ENV_VAR_NAME = "OPENAI_API_KEY"

REQUEST_CONTEXT = {"as_of_date": "2025-01-01", "customer_deadline": ""}


def set_request_context(as_of_date: str, customer_deadline: str = "") -> None:
    REQUEST_CONTEXT["as_of_date"] = as_of_date.split("T")[0]
    REQUEST_CONTEXT["customer_deadline"] = customer_deadline


def resolve_data_path(filename: str) -> Path:
    for base_dir in (INPUT_DATA_DIR, DATA_DIR, REPO_ROOT):
        candidate = base_dir / filename
        if candidate.exists():
            return candidate
    return INPUT_DATA_DIR / filename


def resolve_output_path(filename: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR / filename
