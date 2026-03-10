"""
Tests for the Mergington High School Activities API.

All tests follow the AAA (Arrange-Act-Assert) pattern.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# Snapshot of the original activities state for reset between tests
_original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dict before each test."""
    # Arrange (shared): restore pristine state
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))
    yield
    # Teardown: restore again for safety
    activities.clear()
    activities.update(copy.deepcopy(_original_activities))


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_root_redirects():
    # Arrange
    client = TestClient(app, follow_redirects=False)

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_all():
    # Arrange
    client = TestClient(app)
    expected_activities = {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team",
        "Tennis Club",
        "Art Studio",
        "Drama Club",
        "Debate Team",
        "Science Olympiad",
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == expected_activities


def test_get_activities_structure():
    # Arrange
    client = TestClient(app)
    required_keys = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    for name, details in response.json().items():
        assert required_keys.issubset(details.keys()), (
            f"Activity '{name}' is missing keys: {required_keys - details.keys()}"
        )


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert new_email in response.json()["message"]
    assert new_email in activities[activity_name]["participants"]


def test_signup_activity_not_found():
    # Arrange
    client = TestClient(app)
    fake_activity = "Underwater Basket Weaving"

    # Act
    response = client.post(
        f"/activities/{fake_activity}/signup",
        params={"email": "someone@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_email():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

def test_unregister_success():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 200
    assert existing_email in response.json()["message"]
    assert existing_email not in activities[activity_name]["participants"]


def test_unregister_activity_not_found():
    # Arrange
    client = TestClient(app)
    fake_activity = "Underwater Basket Weaving"

    # Act
    response = client.delete(
        f"/activities/{fake_activity}/unregister",
        params={"email": "someone@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_email_not_registered():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    unregistered_email = "nobody@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": unregistered_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not registered for this activity"
