"""Trace providers."""


def init_providers():
    """Initialize trace providers.

    Register custom TraceProvider implementations here.
    See backend/app/tracing/provider.py for the abstract interface.
    """
    # No built-in providers in the open-source version.
    # Implement and register your own provider:
    #   from ..registry import TraceProviderRegistry
    #   from .my_provider import MyTraceProvider
    #   TraceProviderRegistry.register(MyTraceProvider(...), is_default=True)
