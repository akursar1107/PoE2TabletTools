from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    poe_session_id: str
    database_path: str = "data/poe2_tablets.db"
    snapshot_interval_minutes: int = 60
    price_min_divine_rare: float = 1.0
    price_min_divine_magic: float = 0.0
    price_min_divine_normal: float = 0.0
    current_league_auto: bool = True
    archive_on_league_reset: bool = True
    log_level: str = "INFO"
    league_name: str = ""

    chaos_per_divine: float = 200.0
    exalt_per_divine: float = 0.05
    regal_cost_divine: float = 0.02

    buy_signal_min_profit_div: float = 1.0
    buy_signal_max_junk_rate: float = 0.30
    buy_signal_min_confidence: float = 0.60

    api_host: str = "0.0.0.0"
    api_port: int = 8001
    enable_api: bool = True

    trade_base_url: str = "https://www.pathofexile.com"
    leagues_api_url: str = "https://api.pathofexile.com/leagues"

    # CORS and frontend settings
    cors_origins: str = "*"
    api_base_url: str = ""

    @model_validator(mode="before")
    @classmethod
    def _legacy_env_aliases(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        for legacy_key in ("PRICE_MIN_DIVINE", "price_min_divine"):
            if legacy_key in data and "price_min_divine_rare" not in data:
                data["price_min_divine_rare"] = data[legacy_key]
        return data

    @property
    def request_headers(self) -> dict[str, str]:
        return {
            "Cookie": f"POESESSID={self.poe_session_id}",
            "User-Agent": "poe-tablet-tool/0.2.0 (contact: personal-tool)",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


settings = Settings()
