from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Stable, user-facing error with an API error code."""

    def __init__(
        self,
        code: str,
        status: int,
        title: str,
        detail: str = "",
        *,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail or title)
        self.code = code
        self.status = status
        self.title = title
        self.detail = detail or title
        self.extra = extra or {}

    def problem(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "type": "about:blank",
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "code": self.code,
        }
        body.update(self.extra)
        return body


class QlooError(AppError):
    pass


class QlooAuthError(QlooError):
    def __init__(self, detail: str = "Qloo rejected the API key") -> None:
        super().__init__("qloo_auth", 502, "Qloo authentication failed", detail)


class QlooRateLimited(QlooError):
    def __init__(self, detail: str = "Qloo rate limit exceeded") -> None:
        super().__init__("qloo_rate_limited", 429, "Qloo rate limited the request", detail)


class QlooUnavailable(QlooError):
    def __init__(self, detail: str = "Qloo is unavailable") -> None:
        super().__init__("qloo_unavailable", 502, "Qloo unavailable", detail)


class QlooBadRequest(QlooError):
    def __init__(self, detail: str) -> None:
        super().__init__("qloo_bad_request", 502, "Qloo rejected the request", detail)


class QlooBudgetExceeded(QlooError):
    def __init__(self, detail: str) -> None:
        super().__init__("qloo_budget_exceeded", 429, "Qloo call budget reached", detail)


class QlooContractViolation(QlooError):
    def __init__(self, detail: str) -> None:
        super().__init__("qloo_contract_violation", 502, "Qloo contract violation", detail)


class QlooUnconfigured(QlooError):
    def __init__(self) -> None:
        super().__init__(
            "qloo_unconfigured",
            503,
            "Qloo is not configured",
            "Set QLOO_API_KEY. TasteBound fails closed rather than guessing taste.",
        )


class LLMError(AppError):
    pass


class LLMAuthError(LLMError):
    def __init__(self, detail: str = "LLM provider rejected the API key") -> None:
        super().__init__("llm_auth", 502, "LLM authentication failed", detail)


class LLMRateLimitError(LLMError):
    def __init__(self, detail: str = "LLM rate limited") -> None:
        super().__init__("llm_rate_limited", 429, "LLM rate limited", detail)


class LLMTimeoutError(LLMError):
    def __init__(self, detail: str = "LLM timed out") -> None:
        super().__init__("llm_timeout", 504, "LLM timed out", detail)


class LLMBadResponseError(LLMError):
    def __init__(self, detail: str = "LLM returned an invalid response") -> None:
        super().__init__("llm_bad_response", 502, "LLM returned an invalid response", detail)


class LLMUnavailable(LLMError):
    def __init__(self, detail: str = "LLM is not configured") -> None:
        super().__init__("llm_unavailable", 503, "LLM unavailable", detail)


class NotFound(AppError):
    def __init__(self, what: str = "resource") -> None:
        super().__init__("not_found", 404, "Not found", f"The {what} was not found.")


class InvalidWorkspace(AppError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_workspace", 401, "Invalid workspace", "A valid workspace token is required."
        )


class ValidationProblem(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__("validation_error", 422, "Validation failed", detail)


class RateLimited(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__("rate_limited", 429, "Rate limited", detail)


class ProfileTooThin(AppError):
    def __init__(self) -> None:
        super().__init__(
            "profile_too_thin",
            422,
            "Taste profile too thin",
            "Qloo resolved fewer than 3 signature items. Add better-known items and try again.",
        )


class NoMarketData(AppError):
    def __init__(self) -> None:
        super().__init__(
            "no_market_data",
            502,
            "No market data",
            "Qloo returned no usable data for the selected markets.",
        )


class ArrivalsInvalid(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__("arrivals_invalid", 422, "Arrivals file invalid", detail)


class DestinationNotFound(AppError):
    def __init__(self, name: str) -> None:
        super().__init__(
            "destination_not_found",
            422,
            "Destination not found",
            f"Qloo could not resolve '{name}' as a destination. "
            "Check the spelling or add a nearby major city.",
        )


class AssistantError(AppError):
    pass


class AssistantUnavailable(AssistantError):
    def __init__(
        self, detail: str = "The results assistant needs a configured model provider."
    ) -> None:
        super().__init__("assistant_unavailable", 503, "Assistant unavailable", detail)


class AssistantTimeout(AssistantError):
    def __init__(self, detail: str = "The model took too long to answer.") -> None:
        super().__init__("assistant_timeout", 504, "Assistant timed out", detail)


class AssistantRateLimited(AssistantError):
    def __init__(self, detail: str = "Too many assistant messages. Try again later.") -> None:
        super().__init__("assistant_rate_limited", 429, "Assistant rate limited", detail)


class AssistantBadResponse(AssistantError):
    def __init__(self, detail: str = "The model returned an unusable answer.") -> None:
        super().__init__("assistant_bad_response", 502, "Assistant returned a bad response", detail)


class AssistantUngrounded(AssistantError):
    def __init__(
        self, detail: str = "The answer could not be verified against this run's data."
    ) -> None:
        super().__init__("assistant_ungrounded", 502, "Assistant answer not grounded", detail)


class AssistantBusy(AssistantError):
    def __init__(self, detail: str = "This conversation is already waiting for an answer.") -> None:
        super().__init__("assistant_busy", 409, "Assistant is busy", detail)


class ConversationNotFound(AssistantError):
    def __init__(self) -> None:
        super().__init__(
            "conversation_not_found",
            404,
            "Conversation not found",
            "This conversation expired or belongs to another run. Start a new one.",
        )


class AssistantNotReady(AssistantError):
    def __init__(self) -> None:
        super().__init__(
            "assistant_not_ready",
            409,
            "Assistant is not ready",
            "Market results are not available for this run yet.",
        )
