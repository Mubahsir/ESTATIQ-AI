
"""
Google Places API (New) client with:
- Automatic .env loading
- Pagination
- Retry and exponential backoff
- Request timeouts
- Place Details retrieval
"""

from __future__ import annotations

import os
import time
import logging
from pathlib import Path

import requests
from dotenv import load_dotenv


# --------------------------------------------------
# 1. ENVIRONMENT CONFIGURATION
# --------------------------------------------------

# Find .env in the same folder as this file,
# otherwise look in the project root.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent

ENV_PATH = CURRENT_DIR / ".env"

if not ENV_PATH.exists():
    ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

REQUEST_TIMEOUT = int(
    os.getenv("REQUEST_TIMEOUT_SECONDS", "30")
)

MAX_RETRIES = int(
    os.getenv("MAX_RETRIES", "5")
)


# --------------------------------------------------
# 2. LOGGING
# --------------------------------------------------

log = logging.getLogger(__name__)


# --------------------------------------------------
# 3. GOOGLE PLACES API CONFIGURATION
# --------------------------------------------------

BASE = (
    "https://places.googleapis.com/v1/places:searchText"
)

DETAIL_MASK = (
    "id,displayName,formattedAddress,location,types,"
    "googleMapsUri,nationalPhoneNumber,"
    "internationalPhoneNumber,websiteUri,"
    "rating,userRatingCount,reviews"
)

MASK = (
    "places.id,places.displayName,"
    "places.formattedAddress,places.location,"
    "places.types,places.googleMapsUri,"
    "nextPageToken"
)


# --------------------------------------------------
# 4. CUSTOM API ERROR
# --------------------------------------------------

class PlaceAPIError(RuntimeError):
    """Raised when Google Places API requests fail."""
    pass


# --------------------------------------------------
# 5. GOOGLE PLACES CLIENT
# --------------------------------------------------

class GooglePlacesClient:

    def __init__(
        self,
        api_key=None,
        timeout=None,
        max_retries=None,
        session=None
    ):

        # Load API key from .env automatically
        self.key = api_key or API_KEY

        if not self.key:
            raise ValueError(
                "Google Maps API key is missing. "
                "Add GOOGLE_MAPS_API_KEY to your .env file."
            )

        self.timeout = (
            timeout
            if timeout is not None
            else REQUEST_TIMEOUT
        )

        self.max_retries = (
            max_retries
            if max_retries is not None
            else MAX_RETRIES
        )

        self.session = session or requests.Session()

    # --------------------------------------------------
    # 6. API REQUEST WITH RETRY
    # --------------------------------------------------

    def _request(
        self,
        url,
        body=None,
        mask=None,
        method="POST"
    ):

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.key,
            "X-Goog-FieldMask": mask or DETAIL_MASK
        }

        for attempt in range(self.max_retries + 1):

            try:

                if method.upper() == "GET":

                    response = self.session.get(
                        url,
                        headers=headers,
                        timeout=self.timeout
                    )

                else:

                    response = self.session.post(
                        url,
                        headers=headers,
                        json=body,
                        timeout=self.timeout
                    )

                # Retry rate limits and temporary server errors
                if (
                    response.status_code == 429
                    or response.status_code >= 500
                ):

                    if attempt < self.max_retries:

                        delay = min(60, 2 ** attempt)

                        log.warning(
                            "Google Places HTTP %s. "
                            "Retrying in %s seconds.",
                            response.status_code,
                            delay
                        )

                        time.sleep(delay)
                        continue

                # Handle API errors
                if not response.ok:

                    raise PlaceAPIError(
                        f"Google Places API returned HTTP "
                        f"{response.status_code}: "
                        f"{response.text[:1000]}"
                    )

                return response.json()

            except requests.RequestException as exc:

                if attempt >= self.max_retries:

                    raise PlaceAPIError(
                        "Google Places request failed "
                        f"after retries: {exc}"
                    ) from exc

                delay = min(60, 2 ** attempt)

                log.warning(
                    "Request failed. Retrying in %s seconds: %s",
                    delay,
                    exc
                )

                time.sleep(delay)

        raise PlaceAPIError(
            "Google Places request failed after retries."
        )

    # --------------------------------------------------
    # 7. SEARCH PLACES WITH PAGINATION
    # --------------------------------------------------

    def search_pages(
        self,
        query,
        first_page_token=None
    ):

        if not query or not query.strip():

            raise ValueError(
                "Search query cannot be empty."
            )

        token = first_page_token
        page = 1

        while True:

            body = {
                "textQuery": query,
                "pageSize": 20
            }

            if token:
                body["pageToken"] = token

            # Search request
            data = self._request(
                BASE,
                body,
                MASK
            )

            summary = data.get("places", [])

            detailed = []

            # Retrieve detailed information
            for place in summary:

                place_id = place.get("id")

                if place_id:

                    url = (
                        "https://places.googleapis.com/v1/places/"
                        f"{place_id}"
                    )

                    try:

                        detail = self._request(
                            url,
                            None,
                            DETAIL_MASK,
                            method="GET"
                        )

                        detailed.append(detail)

                    except PlaceAPIError:

                        # Keep original result if details fail
                        detailed.append(place)

                        log.exception(
                            "Place Details unavailable "
                            "for place ID %s",
                            place_id
                        )

                else:

                    detailed.append(place)

            next_token = data.get("nextPageToken")

            # Return page results
            yield page, detailed, next_token

            if not next_token:
                break

            token = next_token
            page += 1
