from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from tastebound_api.db.tables import Base, Market
from tastebound_api.settings import API_ROOT, Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _make_engine(settings: Settings) -> AsyncEngine:
    dsn = settings.database_dsn
    if dsn.startswith("sqlite"):
        settings.resolved_sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        engine = create_async_engine(dsn, future=True)
        if dsn.endswith(".db") or ":memory:" in dsn:

            @event.listens_for(engine.sync_engine, "connect")
            def _fk_pragma(dbapi_connection: Any, _record: Any) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=10000")
                cursor.close()

        return engine
    return create_async_engine(
        dsn,
        future=True,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        connect_args={"statement_cache_size": 0},
    )


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _make_engine(get_settings())
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def init_db(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_markets(settings)


async def seed_markets(settings: Settings | None = None) -> None:
    path = API_ROOT / "src/tastebound_api/data/markets.json"
    if not path.exists():
        return
    payload = json.loads(path.read_text())
    async with get_session_factory()() as session:
        existing = (await session.execute(select(Market.id))).scalars().all()
        existing_ids = set(existing)
        for row in payload["markets"]:
            if row["id"] in existing_ids:
                db_market = await session.get(Market, row["id"])
                if db_market is not None:
                    db_market.city = row["city"]
                    db_market.country_code = row["country_code"]
                    db_market.country_name = row["country_name"]
                    db_market.region = row["region"]
                    db_market.lat = row["lat"]
                    db_market.lon = row["lon"]
                    db_market.radius_km = row.get("radius_km", 40)
                    db_market.population_band = row["population_band"]
                    db_market.active = row.get("active", True)
                    db_market.presets = row.get("presets", [])
                continue
            session.add(
                Market(
                    id=row["id"],
                    city=row["city"],
                    country_code=row["country_code"],
                    country_name=row["country_name"],
                    region=row["region"],
                    lat=row["lat"],
                    lon=row["lon"],
                    radius_km=row.get("radius_km", 40),
                    population_band=row["population_band"],
                    active=row.get("active", True),
                    presets=row.get("presets", []),
                )
            )
        await session.commit()


async def dispose_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def utcnow() -> datetime:
    return datetime.now(UTC)


def data_dir() -> Path:
    path = API_ROOT / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path
