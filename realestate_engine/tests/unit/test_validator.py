"""Unit tests for Validator."""
import pytest
from realestate_engine.etl.validator import Validator


class TestValidator:
    """Test validator functions."""

    def test_validate_valid_listing(self):
        listing = {"preco_pedido": 350000.0, "area_util_m2": 120.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert errors == []

    def test_validate_missing_price(self):
        listing = {"area_util_m2": 120.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert any("Missing required field: preco_pedido" in e for e in errors)

    def test_validate_missing_area(self):
        listing = {"preco_pedido": 350000.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert any("Missing required field: area_util_m2" in e for e in errors)

    def test_validate_missing_rooms(self):
        listing = {"preco_pedido": 350000.0, "area_util_m2": 120.0}
        errors = Validator.validate(listing)
        assert any("Missing required field: quartos" in e for e in errors)

    def test_validate_negative_price(self):
        listing = {"preco_pedido": -1000.0, "area_util_m2": 120.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert any("Invalid value for preco_pedido" in e for e in errors)

    def test_validate_zero_price(self):
        listing = {"preco_pedido": 0, "area_util_m2": 120.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert any("Invalid value for preco_pedido" in e for e in errors)

    def test_validate_price_too_low(self):
        listing = {"preco_pedido": 5000.0, "area_util_m2": 120.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert any("Price too low" in e for e in errors)

    def test_validate_price_too_high(self):
        listing = {"preco_pedido": 100_000_000.0, "area_util_m2": 120.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert any("Price too high" in e for e in errors)

    def test_validate_area_too_small(self):
        listing = {"preco_pedido": 350000.0, "area_util_m2": 5.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert any("Area too small" in e for e in errors)

    def test_validate_area_too_large(self):
        listing = {"preco_pedido": 350000.0, "area_util_m2": 20_000.0, "quartos": 3}
        errors = Validator.validate(listing)
        assert any("Area too large" in e for e in errors)

    def test_validate_negative_rooms(self):
        listing = {"preco_pedido": 350000.0, "area_util_m2": 120.0, "quartos": -1}
        errors = Validator.validate(listing)
        assert any("Invalid rooms" in e for e in errors)

    def test_validate_too_many_rooms(self):
        listing = {"preco_pedido": 350000.0, "area_util_m2": 120.0, "quartos": 100}
        errors = Validator.validate(listing)
        assert any("Invalid rooms" in e for e in errors)

    def test_is_valid_true(self):
        listing = {"preco_pedido": 350000.0, "area_util_m2": 120.0, "quartos": 3}
        assert Validator.is_valid(listing) is True

    def test_is_valid_false(self):
        listing = {"preco_pedido": 5000.0, "area_util_m2": 120.0, "quartos": 3}
        assert Validator.is_valid(listing) is False

    def test_validate_batch(self):
        listings = [
            {"preco_pedido": 350000.0, "area_util_m2": 120.0, "quartos": 3},
            {"preco_pedido": 5000.0, "area_util_m2": 120.0, "quartos": 3},
            {"preco_pedido": 450000.0, "area_util_m2": 150.0, "quartos": 4},
        ]
        valid, invalid = Validator.validate_batch(listings)
        assert len(valid) == 2
        assert len(invalid) == 1
        assert "_validation_errors" in invalid[0]

    def test_validate_batch_empty(self):
        valid, invalid = Validator.validate_batch([])
        assert valid == []
        assert invalid == []
