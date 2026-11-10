from __future__ import annotations

import json
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    contract_account: str = ""
    agent_account: str = ""
    near_network: str = "testnet"
    near_rpc: str = "https://rpc.testnet.fastnear.com"
    outlayer_api: str = "https://testnet-api.outlayer.ai"

    database_url: str = "sqlite:///./backend/data/sealquery.db"
    redis_url: str = "redis://127.0.0.1:6379/0"
    api_key: str = Field(default="", validation_alias=AliasChoices("SEALQUERY_API_KEY", "API_KEY"))
    rate_limit_per_minute: int = Field(
        default=5,
        validation_alias=AliasChoices(
            "SEALQUERY_RATE_LIMIT_PER_MINUTE", "RATE_LIMIT_PER_MINUTE"
        ),
    )
    idempotency_ttl_seconds: int = Field(
        default=86_400,
        validation_alias=AliasChoices(
            "SEALQUERY_IDEMPOTENCY_TTL_SECONDS", "IDEMPOTENCY_TTL_SECONDS"
        ),
    )
    state_ttl_seconds: float = Field(
        default=5.0,
        validation_alias=AliasChoices(
            "SEALQUERY_STATE_TTL_SECONDS", "STATE_TTL_SECONDS"
        ),
    )
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    indexer_interval_seconds: int = 15
    indexer_on_startup: bool = False
    neardata_api: str = "https://testnet.neardata.xyz"
    neardata_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("NEARDATA_API_KEY", "FASTNEAR_API_KEY"),
    )
    event_start_block: int | None = Field(
        default=None, validation_alias=AliasChoices("EVENT_START_BLOCK", "SEALQUERY_EVENT_START_BLOCK")
    )
    event_blocks_per_sync: int = Field(
        default=5, validation_alias=AliasChoices("EVENT_BLOCKS_PER_SYNC", "SEALQUERY_EVENT_BLOCKS_PER_SYNC")
    )
    worker_poll_seconds: float = Field(
        default=2.0,
        validation_alias=AliasChoices("WORKER_POLL_SECONDS", "SEALQUERY_WORKER_POLL_SECONDS"),
    )
    job_timeout_seconds: int = Field(
        default=300,
        validation_alias=AliasChoices("JOB_TIMEOUT_SECONDS", "SEALQUERY_JOB_TIMEOUT_SECONDS"),
    )
    proof_dir: str = "data/proofs"
    legacy_tx_file: str = "data/query_tx.json"
    demo_datasets: str = '[["retail_v1","spend_growth_v1"],["retail_alt","spend_growth_alt"]]'

    @property
    def datasets(self) -> list[tuple[str, str]]:
        return [tuple(item) for item in json.loads(self.demo_datasets)]

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
