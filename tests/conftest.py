import dataclasses

import pytest

import main
import security


@pytest.fixture(autouse=True)
def reset_limiter():
    security.limiter.reset()
    yield
    security.limiter.reset()


@pytest.fixture
def configure(monkeypatch):
    """Override settings fields in every module that holds a reference to them."""

    def apply(**changes):
        new = dataclasses.replace(main.settings, **changes)
        monkeypatch.setattr(main, "settings", new)
        monkeypatch.setattr(security, "settings", new)
        return new

    return apply


@pytest.fixture(autouse=True)
def isolated_settings(configure):
    """Tests must not depend on the developer's .env (auth off, generous rate limit, mock data)."""
    configure(service_api_key="", rate_limit="1000/minute", app_env="development", data_provider="mock")
