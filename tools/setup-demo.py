#!/usr/bin/env python3

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Tuple, Union
from urllib.parse import urljoin

import requests


DEFAULT_BASE_URL = "http://localhost:8001"
DEFAULT_DATA_FILE = str(Path(__file__).resolve().parent / "atis-demo.jsonl")
USERNAME = "admin"
PASSWORD = "password"


class SetupError(Exception):
    pass


def build_url(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    expected_status: Union[int, Tuple[int, ...]],
    **kwargs,
):
    response = session.request(method=method, url=url, timeout=30, **kwargs)
    if isinstance(expected_status, int):
        expected = (expected_status,)
    else:
        expected = expected_status
    if response.status_code not in expected:
        detail = response.text.strip() or "<empty response>"
        raise SetupError(
            f"{method} {url} failed with status {response.status_code}: {detail}"
        )
    try:
        return response.json()
    except ValueError as exc:
        raise SetupError(f"{method} {url} returned non-JSON response") from exc


def login(session: requests.Session, base_url: str) -> str:
    print("1. Logging in...")
    payload = {"username": USERNAME, "password": PASSWORD}
    data = request_json(
        session,
        "POST",
        build_url(base_url, "/v1/auth/login/"),
        200,
        json=payload,
    )
    token = data.get("key")
    if not token:
        raise SetupError("Login succeeded but no auth token was returned")
    session.headers.update({"Authorization": f"Token {token}"})
    # Set CSRF token from cookie for subsequent requests
    csrf_token = session.cookies.get("csrftoken", "")
    if csrf_token:
        session.headers.update({"X-CSRFToken": csrf_token})
    print("   Logged in successfully.")
    return token


def create_project(session: requests.Session, base_url: str) -> int:
    print("2. Creating project...")
    payload = {
        "name": "ATIS Demo",
        "description": "ATIS intent detection and slot filling demo dataset",
        "project_type": "IntentDetectionAndSlotFilling",
        "resourcetype": "IntentDetectionAndSlotFillingProject",
        "guideline": "ATIS dataset: airline travel information system queries with intent and entity labels",
        "random_order": False,
        "collaborative_annotation": False,
        "single_class_classification": False,
    }
    data = request_json(
        session,
        "POST",
        build_url(base_url, "/v1/projects"),
        (200, 201),
        json=payload,
    )
    project_id = data.get("id")
    if not isinstance(project_id, int):
        raise SetupError(f"Project creation returned invalid id: {data!r}")
    print(f"   Project created with id={project_id}.")
    return project_id


def create_label_types(session: requests.Session, base_url: str, project_id: int) -> None:
    print("3. Creating category types (ATIS intents)...")
    # ATIS intent labels with distinct colors
    category_types = [
        {"text": "flight", "color": "#209cee"},
        {"text": "airfare", "color": "#ff3860"},
        {"text": "airline", "color": "#23d160"},
        {"text": "flight_time", "color": "#ffdd57"},
        {"text": "ground_service", "color": "#7957d5"},
        {"text": "airport", "color": "#e74c3c"},
        {"text": "abbreviation", "color": "#3498db"},
        {"text": "aircraft", "color": "#2ecc71"},
        {"text": "distance", "color": "#f39c12"},
        {"text": "ground_fare", "color": "#9b59b6"},
        {"text": "quantity", "color": "#1abc9c"},
    ]
    for item in category_types:
        request_json(
            session,
            "POST",
            build_url(base_url, f"/v1/projects/{project_id}/category-types"),
            (200, 201),
            json=item,
        )
        print(f"   Created category type: {item['text']}")

    print("4. Creating span types (ATIS entities)...")
    # All entity types from the ATIS demo dataset
    span_types = [
        {"text": "fromloc.city_name", "color": "#209cee"},
        {"text": "toloc.city_name", "color": "#ff3860"},
        {"text": "depart_time.time", "color": "#23d160"},
        {"text": "arrive_time.time", "color": "#ffdd57"},
        {"text": "depart_date.day_name", "color": "#7957d5"},
        {"text": "depart_time.period_of_day", "color": "#e74c3c"},
        {"text": "arrive_time.period_of_day", "color": "#3498db"},
        {"text": "airline_name", "color": "#2ecc71"},
        {"text": "airline_code", "color": "#f39c12"},
        {"text": "city_name", "color": "#9b59b6"},
        {"text": "class_type", "color": "#1abc9c"},
        {"text": "cost_relative", "color": "#e67e22"},
        {"text": "fare_amount", "color": "#c0392b"},
        {"text": "round_trip", "color": "#8e44ad"},
        {"text": "flight_mod", "color": "#2c3e50"},
        {"text": "flight_stop", "color": "#16a085"},
        {"text": "flight_time", "color": "#d35400"},
        {"text": "meal", "color": "#27ae60"},
        {"text": "meal_description", "color": "#2980b9"},
        {"text": "mod", "color": "#f1c40f"},
        {"text": "transport_type", "color": "#95a5a6"},
        {"text": "depart_date.date_relative", "color": "#34495e"},
        {"text": "depart_date.day_number", "color": "#7f8c8d"},
        {"text": "depart_date.month_name", "color": "#bdc3c7"},
        {"text": "depart_date.today_relative", "color": "#6c5ce7"},
        {"text": "depart_time.end_time", "color": "#a29bfe"},
        {"text": "depart_time.start_time", "color": "#fd79a8"},
        {"text": "depart_time.time_relative", "color": "#00b894"},
        {"text": "depart_time.period_mod", "color": "#e17055"},
        {"text": "arrive_date.day_number", "color": "#dfe6e9"},
        {"text": "arrive_date.month_name", "color": "#636e72"},
        {"text": "arrive_time.time_relative", "color": "#b2bec3"},
        {"text": "return_date.day_number", "color": "#fab1a0"},
        {"text": "return_date.month_name", "color": "#74b9ff"},
        {"text": "fromloc.airport_name", "color": "#55efc4"},
        {"text": "toloc.airport_code", "color": "#ffeaa7"},
        {"text": "toloc.state_code", "color": "#81ecec"},
        {"text": "toloc.state_name", "color": "#a29bfe"},
        {"text": "stoploc.city_name", "color": "#fdcb6e"},
        {"text": "fare_basis_code", "color": "#e84393"},
    ]
    for item in span_types:
        request_json(
            session,
            "POST",
            build_url(base_url, f"/v1/projects/{project_id}/span-types"),
            (200, 201),
            json=item,
        )
        print(f"   Created span type: {item['text']}")


def upload_dataset(
    session: requests.Session, base_url: str, project_id: int, data_file: Path
) -> None:
    print("5. Uploading dataset via filepond...")
    if not data_file.exists():
        raise SetupError(f"Data file not found: {data_file}")
    if not data_file.is_file():
        raise SetupError(f"Data file is not a regular file: {data_file}")

    # Step 1: Upload file to filepond to get an upload ID
    print("   Step 1: Uploading file to filepond...")
    with data_file.open("rb") as handle:
        files = {"filepond": (data_file.name, handle, "application/octet-stream")}
        # filepond endpoint expects text/plain response, not JSON
        headers = {"Accept": "text/plain"}
        response = session.post(
            build_url(base_url, f"/v1/fp/process/"),
            files=files,
            headers=headers,
            timeout=120,
        )

    if response.status_code not in (200, 201):
        detail = response.text.strip() or "<empty response>"
        raise SetupError(
            f"Filepond upload failed with status {response.status_code}: {detail}"
        )

    upload_id = response.text.strip()
    if not upload_id:
        raise SetupError("Filepond upload returned empty upload ID")
    print(f"   Got upload ID: {upload_id}")

    # Step 2: Trigger the import using the upload ID
    print("   Step 2: Triggering dataset import...")
    import_payload = {
        "uploadIds": [upload_id],
        "format": "JSONL",
        "task": "IntentDetectionAndSlotFilling",
    }
    response = session.post(
        build_url(base_url, f"/v1/projects/{project_id}/upload"),
        json=import_payload,
        timeout=120,
    )

    if response.status_code not in (200, 201, 202):
        detail = response.text.strip() or "<empty response>"
        raise SetupError(
            f"Dataset import failed with status {response.status_code}: {detail}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise SetupError("Dataset import returned non-JSON response") from exc

    task_id = payload.get("task_id")
    print(f"   Import task queued: {task_id}")

    # Wait for the celery task to complete
    print("   Waiting for import to complete...")
    for i in range(30):
        time.sleep(2)
        try:
            examples_resp = session.get(
                build_url(base_url, f"/v1/projects/{project_id}/examples?limit=1"),
                timeout=10,
            )
            if examples_resp.status_code == 200:
                data = examples_resp.json()
                count = data.get("count", 0)
                if count > 0:
                    print(f"   Import complete. {count} examples loaded.")
                    return
        except Exception:
            pass
        print(f"   Still waiting... ({(i+1)*2}s)")

    print("   WARNING: Import may still be in progress. Check manually.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set up a doccano ATIS demo project via the REST API."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL for doccano (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--data-file",
        default=DEFAULT_DATA_FILE,
        help=f"Path to JSONL dataset file (default: {DEFAULT_DATA_FILE})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    try:
        login(session, args.base_url)
        project_id = create_project(session, args.base_url)
        create_label_types(session, args.base_url, project_id)
        upload_dataset(session, args.base_url, project_id, Path(args.data_file))
    except (requests.RequestException, SetupError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("\nSetup completed successfully.")
    print(f"Project URL: {args.base_url.replace('/v1','')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
