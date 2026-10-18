"""Observable preflight estimates; never a claim of exact model tokenization."""

from dataclasses import dataclass

from pactlens.arena.models import integer


@dataclass(frozen=True)
class TokenBudget:
    limit: int
    utf8_bytes: int
    estimated_tokens: int
    exact_tokens: int | None
    method: str
    fits: bool

    def __post_init__(self):
        integer(self.limit, 1, 4096)
        integer(self.utf8_bytes, 0, 100_000_000)
        integer(self.estimated_tokens, 0, 100_000_000)
        if self.exact_tokens is not None:
            integer(self.exact_tokens, 0, 1_000_000)
        expected_method = (
            "TRUSTED_TOKEN_COUNTER"
            if self.exact_tokens is not None
            else "UTF8_HALF_PLUS_CHAT_MARGIN_V1_ESTIMATE"
        )
        if (
            self.method != expected_method
            or type(self.fits) is not bool
            or self.fits
            != (
                (self.estimated_tokens if self.exact_tokens is None else self.exact_tokens)
                <= self.limit
            )
        ):
            raise ValueError("TOKEN_BUDGET_CONSISTENCY")


class BudgetExceeded(ValueError):
    def __init__(self, report):
        super().__init__("INPUT_BUDGET_EXCEEDED")
        self.report = report


def token_preflight(turns, *, limit, token_counter=None):
    integer(limit, 1, 4096)
    size = sum(len(t.role.encode("utf-8")) + len(t.content.encode("utf-8")) for t in turns)
    # Deliberately conservative English-oriented heuristic, with chat overhead.
    # Tokenizer/template dependent; even a passing estimate is NOT a guarantee.
    estimate = (size + 1) // 2 + 32 * len(turns) + 128
    exact = None if token_counter is None else token_counter(turns)
    if exact is not None:
        integer(exact, 0, 1_000_000)
    report = TokenBudget(
        limit,
        size,
        estimate,
        exact,
        "TRUSTED_TOKEN_COUNTER" if exact is not None else "UTF8_HALF_PLUS_CHAT_MARGIN_V1_ESTIMATE",
        (estimate if exact is None else exact) <= limit,
    )
    return report


def require_budget(turns, *, limit, token_counter=None):
    report = token_preflight(turns, limit=limit, token_counter=token_counter)
    if not report.fits:
        raise BudgetExceeded(report)
    return report
