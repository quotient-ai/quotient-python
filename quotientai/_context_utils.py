"""Generic context-variable helper used across the Quotient SDK.

This intentionally *does not* import anything from the rest of the codebase so
that it can be imported anywhere (including during import-time of other
modules) without causing circular-import headaches.
"""
from __future__ import annotations

import contextlib
import contextvars
from typing import Generic, Optional, TypeVar

T = TypeVar("T")

class ContextObject(Generic[T]):
    """Small wrapper around :pyclass:`contextvars.ContextVar` with a global default.

    Features
    --------
    1. ``.set_global(value)`` sets a *process-wide* fallback value.
    2. ``.using(value)`` returns a context-manager that temporarily overrides the
       value for the current context (works for threads & asyncio tasks).
    3. ``.get()`` fetches the current value, falling back to the global default
       when no local override exists – and *never* raises ``LookupError``.
    """

    def __init__(self, name: str):
        self._var: contextvars.ContextVar[Optional[T]] = contextvars.ContextVar(name)
        self._global: Optional[T] = None

    def set_global(self, value: T) -> None:
        """Set the process-wide default value."""
        self._global = value

    def get(self) -> Optional[T]:
        """Get the current value or *None* if neither local nor global set."""
        return self._var.get(self._global)

    @contextlib.contextmanager
    def using(self, value: T):
        """Temporarily override the value in the current context.

        Works with both threading and asyncio because it relies on
        :pyclass:`contextvars.ContextVar`.
        """
        token = self._var.set(value)
        try:
            yield
        finally:
            self._var.reset(token)
