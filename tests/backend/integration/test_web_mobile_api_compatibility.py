"""Integration tests for web and mobile API path compatibility."""

import pytest


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/v1/health/live/", "/api/v1/health/live/"])
def test_health_live_endpoint_available_on_both_prefixes(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert response.json()["status"] == "alive"
    assert response["X-API-Version"] == "v1"


@pytest.mark.django_db
def test_health_live_response_is_consistent_for_web_and_mobile_prefixes(client):
    web_response = client.get("/v1/health/live/")
    mobile_response = client.get("/api/v1/health/live/")

    assert web_response.status_code == 200
    assert mobile_response.status_code == 200
    assert web_response.json() == mobile_response.json()
