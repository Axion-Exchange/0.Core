"""
BRL Multi-Account Integration Tests
====================================
Verify that a second BinanceApiClient instance can coexist
with the primary, using a different exchange_id and API keys.
"""

import pytest
from src.core.types import ExchangeId, EXCHANGE_PREFIXES, make_internal_order_number
from src.core.registry import ClientRegistry
from src.exchanges.binance.api_client import BinanceApiClient


# ---------------------------------------------------------------------------
# ExchangeId & Prefix Tests
# ---------------------------------------------------------------------------

class TestBinanceBrlExchangeId:
    """Verify BINANCE_BRL enum and prefix mapping."""

    def test_binance_brl_enum_exists(self):
        assert ExchangeId.BINANCE_BRL == "binance_brl"

    def test_binance_brl_prefix(self):
        assert EXCHANGE_PREFIXES[ExchangeId.BINANCE_BRL] == "BB"

    def test_binance_primary_prefix_unchanged(self):
        assert EXCHANGE_PREFIXES[ExchangeId.BINANCE] == "BI"

    def test_internal_order_number_brl(self):
        order_id = "12345678901234"
        result = make_internal_order_number(ExchangeId.BINANCE_BRL, order_id)
        assert result == "BB901234"

    def test_internal_order_number_primary_unchanged(self):
        order_id = "12345678901234"
        result = make_internal_order_number(ExchangeId.BINANCE, order_id)
        assert result == "BI901234"


# ---------------------------------------------------------------------------
# BinanceApiClient Override Tests
# ---------------------------------------------------------------------------

class TestBinanceApiClientOverride:
    """Verify exchange_id and totp_secret overrides."""

    def test_default_exchange_id(self):
        client = BinanceApiClient(api_key="key", api_secret="secret")
        assert client.exchange_id == ExchangeId.BINANCE

    def test_override_exchange_id(self):
        client = BinanceApiClient(
            api_key="brl_key",
            api_secret="brl_secret",
            exchange_id_override=ExchangeId.BINANCE_BRL,
        )
        assert client.exchange_id == ExchangeId.BINANCE_BRL

    def test_display_name_override(self):
        client = BinanceApiClient(
            api_key="k",
            api_secret="s",
            exchange_id_override=ExchangeId.BINANCE_BRL,
        )
        assert "brl" in client.display_name.lower()

    def test_totp_secret_stored(self):
        client = BinanceApiClient(
            api_key="k",
            api_secret="s",
            totp_secret="MY_TOTP",
        )
        assert client._totp_secret == "MY_TOTP"

    def test_totp_secret_default_none(self):
        client = BinanceApiClient(api_key="k", api_secret="s")
        assert client._totp_secret is None


# ---------------------------------------------------------------------------
# Registry Coexistence Tests
# ---------------------------------------------------------------------------

class TestRegistryCoexistence:
    """Verify both clients can coexist in the registry."""

    def test_register_both_clients(self):
        reg = ClientRegistry()

        primary = BinanceApiClient(api_key="prim_key", api_secret="prim_sec")
        brl = BinanceApiClient(
            api_key="brl_key",
            api_secret="brl_sec",
            exchange_id_override=ExchangeId.BINANCE_BRL,
        )

        reg.register_exchange_api(primary)
        reg.register_exchange_api(brl)

        assert len(reg.all_exchange_apis()) == 2

    def test_lookup_by_id(self):
        reg = ClientRegistry()

        primary = BinanceApiClient(api_key="prim_key", api_secret="prim_sec")
        brl = BinanceApiClient(
            api_key="brl_key",
            api_secret="brl_sec",
            exchange_id_override=ExchangeId.BINANCE_BRL,
        )

        reg.register_exchange_api(primary)
        reg.register_exchange_api(brl)

        assert reg.get_exchange_api(ExchangeId.BINANCE) is primary
        assert reg.get_exchange_api(ExchangeId.BINANCE_BRL) is brl

    def test_separate_api_keys(self):
        reg = ClientRegistry()

        primary = BinanceApiClient(api_key="AAAA", api_secret="BBBB")
        brl = BinanceApiClient(
            api_key="CCCC",
            api_secret="DDDD",
            exchange_id_override=ExchangeId.BINANCE_BRL,
        )

        reg.register_exchange_api(primary)
        reg.register_exchange_api(brl)

        p = reg.get_exchange_api(ExchangeId.BINANCE)
        b = reg.get_exchange_api(ExchangeId.BINANCE_BRL)

        assert p.api_key == "AAAA"
        assert b.api_key == "CCCC"
        assert p.api_key != b.api_key
