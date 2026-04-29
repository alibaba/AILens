"""Trace provider registry."""

from typing import Dict, List, Optional

from .provider import TraceProvider


class TraceProviderRegistry:
    """Trace Provider registry."""

    _providers: Dict[str, TraceProvider] = {}
    _default: Optional[str] = None

    @classmethod
    def register(cls, provider: TraceProvider, is_default: bool = False):
        """Register provider."""
        cls._providers[provider.name] = provider
        if is_default:
            cls._default = provider.name

    @classmethod
    def get(cls, name: Optional[str] = None) -> Optional[TraceProvider]:
        """Get provider."""
        if name:
            return cls._providers.get(name)
        if cls._default:
            return cls._providers.get(cls._default)
        return None

    @classmethod
    def list_providers(cls) -> List[str]:
        """List all providers."""
        return list(cls._providers.keys())


def get_trace_provider(name: Optional[str] = None) -> TraceProvider:
    """Get trace provider (convenience function)."""
    provider = TraceProviderRegistry.get(name)
    if not provider:
        available = TraceProviderRegistry.list_providers()
        if available:
            raise ValueError(f"Trace provider not found: {name or 'default'}. Available: {', '.join(available)}")
        else:
            raise ValueError("No trace providers registered")
    return provider
