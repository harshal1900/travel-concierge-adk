import dataclasses

import pytest
from fastapi.testclient import TestClient

import main
from config import Settings

OK = Settings(google_api_key="k")


def test_valid_defaults():
    assert OK.validate() == []


def test_missing_gemini_key():
    assert any("GOOGLE_API_KEY" in p for p in Settings().validate())


def test_non_gemini_model_skips_google_key():
    assert Settings(llm_model="openai/gpt-x").validate() == []


def test_places_needs_key():
    assert any("PLACES_API_KEY" in p for p in dataclasses.replace(OK, data_provider="google_places").validate())
    assert dataclasses.replace(OK, data_provider="google_places", places_api_key="p").validate() == []


def test_production_needs_service_key():
    assert any("SERVICE_API_KEY" in p for p in dataclasses.replace(OK, app_env="production").validate())
    assert dataclasses.replace(OK, app_env="production", service_api_key="s").validate() == []


def test_unknown_provider():
    assert dataclasses.replace(OK, data_provider="bogus").validate()


def test_app_refuses_to_start_when_invalid(configure):
    configure(app_env="production", service_api_key="", google_api_key="k")
    with pytest.raises(RuntimeError, match="SERVICE_API_KEY"):
        with TestClient(main.app):
            pass


def test_app_starts_when_valid(configure):
    configure(google_api_key="k")
    with TestClient(main.app) as client:
        assert client.get("/health").status_code == 200
