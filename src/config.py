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
        pass
