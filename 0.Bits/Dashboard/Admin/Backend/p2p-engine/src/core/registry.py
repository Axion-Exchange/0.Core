"""
CLIENT REGISTRY
===================
Auto-discovery and registration of all clients.
Provides unified access to exchange and bank clients.
"""

from typing import TypeVar

from .clients import (
    ExchangeApiClient,
    ExchangeAppClient,
    BankClient,
    CryptoFiatConverter,
)
from .types import ExchangeId


T = TypeVar("T")


class ClientRegistry:
    """
    Registry for all clients.
    Allows lookup by exchange/bank ID.
    """
    
    def __init__(self):
        self._exchange_api: dict[str, ExchangeApiClient] = {}
        self._exchange_app: dict[str, ExchangeAppClient] = {}
        self._banks: dict[str, BankClient] = {}
        self._converters: dict[str, CryptoFiatConverter] = {}
    
    # -------------------------------------------------------------------------
    # REGISTRATION
    # -------------------------------------------------------------------------
    
    def register_exchange_api(self, client: ExchangeApiClient) -> None:
        """Register an exchange API client."""
        self._exchange_api[client.exchange_id.value] = client
        print(f"✓ Registered exchange API: {client.display_name}")
    
    def register_exchange_app(self, client: ExchangeAppClient) -> None:
        """Register an exchange app client."""
        self._exchange_app[client.exchange_id.value] = client
        print(f"✓ Registered exchange app: {client.display_name}")
    
    def register_bank(self, client: BankClient) -> None:
        """Register a bank client."""
        self._banks[client.provider_id] = client
        print(f"✓ Registered bank: {client.display_name}")
    
    def register_converter(self, name: str, converter: CryptoFiatConverter) -> None:
        """Register a crypto/fiat converter."""
        self._converters[name] = converter
        print(f"✓ Registered converter: {name}")
    
    # -------------------------------------------------------------------------
    # LOOKUP
    # -------------------------------------------------------------------------
    
    def get_exchange_api(self, exchange_id: str | ExchangeId) -> ExchangeApiClient | None:
        """Get exchange API client by ID."""
        key = exchange_id.value if isinstance(exchange_id, ExchangeId) else exchange_id
        return self._exchange_api.get(key)
    
    def get_exchange_app(self, exchange_id: str | ExchangeId) -> ExchangeAppClient | None:
        """Get exchange app client by ID."""
        key = exchange_id.value if isinstance(exchange_id, ExchangeId) else exchange_id
        return self._exchange_app.get(key)
    
    def get_exchange(self, exchange_id: str | ExchangeId) -> ExchangeApiClient | ExchangeAppClient | None:
        """Get any exchange client (prefers API over app)."""
        return self.get_exchange_api(exchange_id) or self.get_exchange_app(exchange_id)
    
    def get_bank(self, provider_id: str) -> BankClient | None:
        """Get bank client by provider ID."""
        return self._banks.get(provider_id)
    
    def get_converter(self, name: str) -> CryptoFiatConverter | None:
        """Get crypto/fiat converter by name."""
        return self._converters.get(name)
    
    # -------------------------------------------------------------------------
    # LISTING
    # -------------------------------------------------------------------------
    
    def all_exchange_apis(self) -> list[ExchangeApiClient]:
        """Get all registered exchange API clients."""
        return list(self._exchange_api.values())
    
    def all_exchange_apps(self) -> list[ExchangeAppClient]:
        """Get all registered exchange app clients."""
        return list(self._exchange_app.values())
    
    def all_banks(self) -> list[BankClient]:
        """Get all registered bank clients."""
        return list(self._banks.values())
    
    def all_converters(self) -> list[CryptoFiatConverter]:
        """Get all registered converters."""
        return list(self._converters.values())
    
    # -------------------------------------------------------------------------
    # METADATA
    # -------------------------------------------------------------------------
    
    def get_supported_exchanges(self) -> list[str]:
        """Get list of all supported exchange IDs."""
        return list(set(self._exchange_api.keys()) | set(self._exchange_app.keys()))
    
    def get_supported_banks(self) -> list[str]:
        """Get list of all supported bank provider IDs."""
        return list(self._banks.keys())
    
    def exchange_has_api(self, exchange_id: str) -> bool:
        """Check if exchange has API client (vs app-only)."""
        return exchange_id in self._exchange_api
    
    def status(self) -> dict[str, int]:
        """Get registry status."""
        return {
            "exchange_apis": len(self._exchange_api),
            "exchange_apps": len(self._exchange_app),
            "banks": len(self._banks),
            "converters": len(self._converters),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global registry instance
registry = ClientRegistry()
