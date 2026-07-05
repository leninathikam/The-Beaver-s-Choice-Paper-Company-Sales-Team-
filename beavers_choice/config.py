from pathlib import Path

import dotenv
from sqlalchemy import create_engine

dotenv.load_dotenv()

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
DATA_DIR = REPO_ROOT / "data"
INPUT_DATA_DIR = DATA_DIR / "input"
RUNTIME_DIR = DATA_DIR / "runtime"
OUTPUT_DIR = REPO_ROOT / "outputs"
DATABASE_PATH = RUNTIME_DIR / "munder_difflin.db"
DB_ENGINE = create_engine(f"sqlite:///{DATABASE_PATH}")

MODEL_ID = "gpt-4o-mini"
API_BASE = "https://openai.vocareum.com/v1"
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