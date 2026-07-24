import os
from dataclasses import dataclass
from pathlib import Path

ENDPOINT = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"

@dataclass(frozen=True)
class Config:
    endpoint: str = ENDPOINT
    page_size: int = 1000          # Number of records requested per API call
    order: str = ":id"             # Stable ordering for paginated requests
    app_token: str | None = None   # Optional Socrata application token
    db_path: Path = Path("warehouse.db")
    raw_dir: Path = Path("data/raw")
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            app_token=os.environ.get("SOCRATA_APP_TOKEN"),
            db_path=Path(os.environ.get("DB_PATH", "warehouse.db")),
            raw_dir=Path(os.environ.get("RAW_DIR", "data/raw")),
            page_size=int(os.environ.get("PAGE_SIZE", "1000")),
        )