import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

# Preserve the initial participants state for each test
INITIAL_PARTICIPANTS = {
    activity_name: details["participants"][:]
    for activity_name, details in activities.items()
}


@pytest.fixture(autouse=True)
def reset_activities():
    for activity_name, participants in INITIAL_PARTICIPANTS.items():
        activities[activity_name]["participants"] = participants.copy()
    yield
    for activity_name, participants in INITIAL_PARTICIPANTS.items():
        activities[activity_name]["participants"] = participants.copy()


def test_get_activities_returns_expected_fields():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()

    assert "Chess Club" in data
    assert "Programming Class" in data
    assert data["Chess Club"]["description"].startswith("Learn strategies")
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_adds_participant():
    email = "tester@mergington.edu"
    response = client.post(
        f"/activities/Chess Club/signup?email={email}"
    )

    assert response.status_code == 200
    assert f"Signed up {email} for Chess Club" in response.json()["message"]
    assert email in activities["Chess Club"]["participants"]


def test_duplicate_signup_returns_400():
    email = "duplicate@mergington.edu"
    first_response = client.post(
        f"/activities/Programming Class/signup?email={email}"
    )
    assert first_response.status_code == 200

    second_response = client.post(
        f"/activities/Programming Class/signup?email={email}"
    )
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up for this activity"
    assert activities["Programming Class"]["participants"].count(email) == 1


def test_unregister_participant_removes_email():
    email = "john@mergington.edu"
    response = client.delete(
        f"/activities/Gym Class/signup?email={email}"
    )

    assert response.status_code == 200
    assert f"Unregistered {email} from Gym Class" in response.json()["message"]
    assert email not in activities["Gym Class"]["participants"]


def test_unregister_nonexistent_participant_returns_400():
    response = client.delete(
        "/activities/Gym Class/signup?email=missing@mergington.edu"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student not signed up for this activity"


def test_signup_unknown_activity_returns_404():
    response = client.post(
        "/activities/Unknown Activity/signup?email=test@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_unknown_activity_returns_404():
    response = client.delete(
        "/activities/Unknown Activity/signup?email=test@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
