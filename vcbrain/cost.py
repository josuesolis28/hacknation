"""Presupuesto de costo por corrida de búsqueda.

El tool "web_search" de OpenAI resultó ser caro: una sola llamada puede
inyectar >15k tokens de contexto (páginas encontradas) además de la tarifa
fija por llamada de la tool. Con las ~44 queries que antes disparaba la
tesis DACH completa, una corrida se acercaba o superaba los $2 USD.

Este módulo estima el costo en tiempo real (tokens + fee de la tool) y
permite cortar una corrida antes de que se pase del límite configurado
(`Settings.max_search_cost_usd`, default $2). Es una estimación best-effort
con los precios públicos de OpenAI — ajustables por env si cambian.
"""

import threading

# USD por 1M tokens (input, output). Aproximado a precios públicos de OpenAI.
_MODEL_PRICES_PER_1M: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-5.4-mini": (0.75, 4.50),
}
_DEFAULT_PRICE = (2.50, 10.00)

# Tarifa aproximada por llamada de la tool "web_search" (Responses API),
# adicional al costo de tokens. Ver openai.com/pricing (tool calls).
WEB_SEARCH_CALL_USD = 0.03


class CostTracker:
    """Acumulador thread-safe del costo estimado de una corrida."""

    def __init__(self, limit_usd: float):
        self.limit_usd = limit_usd
        self._lock = threading.Lock()
        self._total = 0.0
        self.breakdown: dict[str, float] = {}

    @property
    def total_usd(self) -> float:
        with self._lock:
            return self._total

    def over_limit(self) -> bool:
        return self.total_usd >= self.limit_usd

    def _add(self, label: str, usd: float) -> None:
        with self._lock:
            self._total += usd
            self.breakdown[label] = self.breakdown.get(label, 0.0) + usd

    def record_tokens(self, label: str, model: str, input_tokens: int, output_tokens: int) -> None:
        price_in, price_out = _MODEL_PRICES_PER_1M.get(model, _DEFAULT_PRICE)
        usd = (input_tokens / 1_000_000) * price_in + (output_tokens / 1_000_000) * price_out
        self._add(label, usd)

    def record_web_search_call(self, label: str = "web_search") -> None:
        self._add(label, WEB_SEARCH_CALL_USD)
