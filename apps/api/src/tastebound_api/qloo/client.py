from __future__ import annotations

import asyncio
import hashlib
import json
import random
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tastebound_api.db.tables import QlooCall
from tastebound_api.errors import (
    QlooAuthError,
    QlooBadRequest,
    QlooBudgetExceeded,
    QlooContractViolation,
    QlooRateLimited,
    QlooUnavailable,
    QlooUnconfigured,
)
from tastebound_api.settings import Settings, get_settings

Adapter = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass
class QlooResult:
    data: dict[str, Any]
    call_id: str
    cache_hit: bool
    warnings: list[Any]


class QlooClient:
    """Rate-limited, cached, budgeted, traced Qloo client. Fails closed."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        event_sink: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.session_factory = session_factory
        self._client = httpx.AsyncClient(
            base_url=self.settings.qloo_base_url.rstrip("/"),
            timeout=self.settings.qloo_timeout_seconds,
            headers={"X-Api-Key": self.settings.qloo_api_key},
            transport=transport,
        )
        self._lock = asyncio.Lock()
        self._last_call_at = 0.0
        self._run_live_counts: dict[str, int] = {}
        self.event_sink = event_sink

    @property
    def configured(self) -> bool:
        return bool(self.settings.qloo_api_key)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(
        self,
        path: str,
        params: dict[str, Any],
        *,
        run_id: str | None,
        step: str,
        cache_ttl_hours: int | None = None,
    ) -> QlooResult:
        if not self.configured:
            raise QlooUnconfigured()
        clean_params = {k: v for k, v in params.items() if v is not None}
        cache_key = self.cache_key(path, clean_params)
        ttl = timedelta(hours=cache_ttl_hours or self.settings.qloo_cache_ttl_hours)

        cached = await self._lookup_cache(cache_key)
        if cached is not None:
            warnings = cached.get("warnings", [])
            call_id = await self._trace(
                run_id=run_id,
                step=step,
                endpoint=path,
                params=clean_params,
                cache_key=cache_key,
                cache_hit=True,
                status=200,
                duration_ms=0,
                response=cached,
                warnings=warnings if isinstance(warnings, list) else [],
                expires_at=None,
                result_count=self._result_count(cached),
            )
            await self._emit(
                "qloo_call",
                {
                    "call_id": call_id,
                    "endpoint": path,
                    "step": step,
                    "cache_hit": True,
                    "status": 200,
                    "duration_ms": 0,
                    "result_count": self._result_count(cached),
                },
            )
            return QlooResult(cached, call_id, True, warnings if isinstance(warnings, list) else [])

        await self._budget_guard(run_id)
        started = time.monotonic()
        status: int | None = None
        response: dict[str, Any] | None = None
        last_error: Exception | None = None
        for attempt in range(3):
            await self._wait_for_slot()
            try:
                resp = await self._client.get(path, params=clean_params)
                status = resp.status_code
                if resp.status_code == 401:
                    raise QlooAuthError(
                        "Qloo rejected QLOO_API_KEY. Check the hackathon key and base URL."
                    )
                if resp.status_code == 403:
                    raise QlooAuthError("Qloo denied access to this entity type or resource.")
                if resp.status_code == 400:
                    raise QlooBadRequest(resp.text[:500])
                if resp.status_code == 429:
                    raise QlooRateLimited(resp.text[:300])
                if resp.status_code >= 500:
                    raise QlooUnavailable(f"Qloo returned HTTP {resp.status_code}")
                if resp.status_code >= 400:
                    raise QlooBadRequest(
                        f"Qloo returned HTTP {resp.status_code}: {resp.text[:300]}"
                    )
                try:
                    parsed = resp.json()
                except ValueError as exc:
                    raise QlooContractViolation("Qloo returned non-JSON content") from exc
                if not isinstance(parsed, dict):
                    raise QlooContractViolation("Qloo returned an unexpected JSON shape")
                response = parsed
                break
            except (QlooBadRequest, QlooAuthError):
                raise
            except (QlooRateLimited, QlooUnavailable, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.5 * (2**attempt) + random.uniform(0, 0.2))
                    continue
                if isinstance(exc, QlooRateLimited):
                    raise QlooRateLimited(str(exc)) from exc
                raise QlooUnavailable(str(exc)) from exc

        if response is None:
            raise QlooUnavailable(str(last_error or "Qloo request failed"))

        duration_ms = int((time.monotonic() - started) * 1000)
        run_key = run_id or "global"
        self._run_live_counts[run_key] = self._run_live_counts.get(run_key, 0) + 1
        expires_at = datetime.now(UTC) + ttl
        warnings = response.get("warnings", [])
        result_count = self._result_count(response)
        call_id = await self._trace(
            run_id=run_id,
            step=step,
            endpoint=path,
            params=clean_params,
            cache_key=cache_key,
            cache_hit=False,
            status=status,
            duration_ms=duration_ms,
            response=response,
            warnings=warnings if isinstance(warnings, list) else [],
            expires_at=expires_at,
            result_count=result_count,
        )
        await self._emit(
            "qloo_call",
            {
                "call_id": call_id,
                "endpoint": path,
                "step": step,
                "cache_hit": False,
                "status": status,
                "duration_ms": duration_ms,
                "result_count": result_count,
            },
        )
        return QlooResult(response, call_id, False, warnings if isinstance(warnings, list) else [])

    async def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self.event_sink is None:
            return
        await self.event_sink(event_type, payload)

    @staticmethod
    def cache_key(path: str, params: dict[str, Any]) -> str:
        payload = json.dumps(
            {"method": "GET", "path": path, "params": params},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _result_count(response: dict[str, Any]) -> int | None:
        results = response.get("results")
        if isinstance(results, list):
            return len(results)
        if isinstance(results, dict):
            for key in ("entities", "demographics"):
                value = results.get(key)
                if isinstance(value, list):
                    return len(value)
        return None

    async def _lookup_cache(self, cache_key: str) -> dict[str, Any] | None:
        now = datetime.now(UTC)
        async with self.session_factory() as session:
            stmt = (
                select(QlooCall)
                .where(
                    QlooCall.cache_key == cache_key,
                    QlooCall.status == 200,
                    QlooCall.response.is_not(None),
                    QlooCall.expires_at > now,
                )
                .order_by(QlooCall.created_at.desc())
                .limit(1)
            )
            row = (await session.execute(stmt)).scalars().first()
            if row is None or row.response is None:
                return None
            return dict(row.response)

    async def _budget_guard(self, run_id: str | None) -> None:
        run_live = self._run_live_counts.get(run_id or "global", 0)
        if run_live >= self.settings.qloo_max_calls_per_run:
            raise QlooBudgetExceeded(
                f"Per-run Qloo cap of {self.settings.qloo_max_calls_per_run} live calls reached. "
                "Partial results are kept."
            )
        async with self.session_factory() as session:
            since = datetime.now(UTC) - timedelta(days=30)
            count = await session.scalar(
                select(func.count(QlooCall.id)).where(
                    QlooCall.cache_hit.is_(False),
                    QlooCall.created_at >= since,
                )
            )
        monthly = int(count or 0)
        guard = int(self.settings.qloo_monthly_call_limit * 0.8)
        if monthly >= guard:
            raise QlooBudgetExceeded(
                f"Monthly Qloo guard reached ({monthly}/{self.settings.qloo_monthly_call_limit}). "
                "Use the stored sample run."
            )

    async def _wait_for_slot(self) -> None:
        async with self._lock:
            min_interval = 1.0 / max(self.settings.qloo_rps, 0.1)
            now = time.monotonic()
            wait = min_interval - (now - self._last_call_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call_at = time.monotonic()

    async def _trace(
        self,
        *,
        run_id: str | None,
        step: str,
        endpoint: str,
        params: dict[str, Any],
        cache_key: str,
        cache_hit: bool,
        status: int | None,
        duration_ms: int | None,
        response: dict[str, Any] | None,
        warnings: list[Any],
        expires_at: datetime | None,
        result_count: int | None = None,
    ) -> str:
        call_id = str(uuid.uuid4())
        async with self.session_factory() as session:
            session.add(
                QlooCall(
                    id=call_id,
                    run_id=run_id,
                    step=step,
                    endpoint=endpoint,
                    params=params,
                    cache_key=cache_key,
                    cache_hit=cache_hit,
                    status=status,
                    duration_ms=duration_ms,
                    result_count=result_count,
                    warnings=warnings,
                    response=response,
                    expires_at=expires_at,
                )
            )
            await session.commit()
        return call_id
