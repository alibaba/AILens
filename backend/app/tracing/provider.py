"""Trace provider abstract interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Trace, TraceSearchResult


class TraceProvider(ABC):
    """Trace data provider abstract interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    async def close(self) -> None:
        """
        Close provider and release resources.

        Default implementation does nothing.
        Providers with resources (HTTP clients, connections, etc.)
        should override this method.
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    @abstractmethod
    async def get_trace(self, trace_id: str) -> Optional[Trace]:
        """
        Get trace details by trace ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace object, or None if not found
        """
        pass

    @abstractmethod
    async def search_traces(
        self,
        start_time: int,
        end_time: int,
        service_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[TraceSearchResult]:
        """
        Search trace list.

        Args:
            start_time: Start time (millisecond timestamp)
            end_time: End time (millisecond timestamp)
            service_name: Service name filter
            operation_name: Operation name filter
            status: Status filter (ok/error)
            limit: Result count limit

        Returns:
            List of trace search results
        """
        pass

    @abstractmethod
    def get_trace_url(self, trace_id: str) -> str:
        """
        Get trace view URL in external system.

        Args:
            trace_id: Trace ID

        Returns:
            External system URL
        """
        pass
