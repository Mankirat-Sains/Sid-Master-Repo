import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"


@dataclass
class AppConfig:
    openai_api_key: Optional[str]
    vector_db_path: Path
    metadata_db_path: Path
    embedding_model: str
    qdrant_collection: str
    use_local_embeddings: bool
    embedding_dim: Optional[int]
    log_level: str
    use_csv_vector_store: bool = False
    csv_vector_store_path: Path = DATA_DIR / "vector_store.csv"


def load_config() -> AppConfig:
    """
    Load application configuration from environment variables with sane defaults.
    """
    load_dotenv()
    vector_db_path = _coerce_path(os.getenv("VECTOR_DB_PATH", DATA_DIR / "vector_db"))
    metadata_db_path = _coerce_path(os.getenv("METADATA_DB_PATH", DATA_DIR / "metadata.db"))

    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        vector_db_path=vector_db_path,
        metadata_db_path=metadata_db_path,
        embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "documents"),
        use_local_embeddings=_as_bool(os.getenv("USE_LOCAL_EMBEDDINGS", "false")),
        embedding_dim=_parse_optional_int(os.getenv("EMBEDDING_DIM")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        use_csv_vector_store=_as_bool(os.getenv("USE_CSV_VECTOR_STORE", "false")),
        csv_vector_store_path=_coerce_path(os.getenv("CSV_VECTOR_STORE_PATH", DATA_DIR / "vector_store.csv")),
    )


def ensure_data_dirs() -> None:
    """
    Create local data directories when they are missing.
    """
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "sample_docs").mkdir(parents=True, exist_ok=True)


def _coerce_path(path_value: os.PathLike | str) -> Path:
    return Path(path_value).expanduser().resolve()


def _parse_optional_int(value: Optional[str]) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _as_bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "y"}
