import json
import mimetypes
import random
import time
from pathlib import Path
from typing import Any, Callable
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config


class MetaApiError(Exception):
    """Raised when Meta Graph API returns an error response."""

    def __init__(self, message: str, code: int | None = None, subcode: int | None = None, fbtrace_id: str | None = None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode
        self.fbtrace_id = fbtrace_id


class MetaAuthError(MetaApiError):
    """Raised for authentication, authorization, or token revocation errors."""
    pass


class MetaRateLimitError(MetaApiError):
    """Raised when rate limits (code 4 or 17) or HTTP 429 are encountered."""
    pass


class MetaClient:
    """High-resilience client for Meta Graph API with rate-limiting and retry logic."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = f"https://graph.facebook.com/{config.api_version}"
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _apply_delay(self, progress_callback: Callable[[float], None] | None = None) -> None:
        """Enforces mandatory delay with jitter between API requests to prevent spam flags."""
        jitter = random.uniform(-self.config.delay_jitter, self.config.delay_jitter)
        delay = max(1.0, self.config.delay_seconds + jitter)
        if progress_callback:
            progress_callback(delay)
        time.sleep(delay)

    def _handle_response(self, resp: requests.Response) -> dict[str, Any]:
        """Parses Meta response and maps specific Graph API error codes."""
        try:
            data = resp.json()
        except Exception:
            resp.raise_for_status()
            return {}

        if "error" in data:
            err = data["error"]
            msg = err.get("message", "Unknown Meta Graph API error")
            code = err.get("code")
            subcode = err.get("error_subcode")
            trace = err.get("fbtrace_id")

            # Check for Rate Limit codes: 4, 17, 32, 613, or HTTP 429
            if resp.status_code == 429 or code in {4, 17, 32, 613}:
                raise MetaRateLimitError(f"Meta Rate Limit exceeded ({code}): {msg}", code=code, subcode=subcode, fbtrace_id=trace)

            # Check for Auth / Token Revocation codes: 190, 102, 100 with permissions
            if code in {190, 102} or (code == 100 and "OAuth" in str(err.get("type", ""))):
                raise MetaAuthError(f"Meta Authentication Error ({code}/{subcode}): {msg}", code=code, subcode=subcode, fbtrace_id=trace)

            raise MetaApiError(f"Meta API Error ({code}/{subcode}): {msg}", code=code, subcode=subcode, fbtrace_id=trace)

        if not resp.ok:
            resp.raise_for_status()

        return data

    def _execute_with_backoff(self, action: Callable[[], requests.Response], max_attempts: int = 3) -> dict[str, Any]:
        """Executes a request with automatic exponential backoff on transient rate limits."""
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = action()
                return self._handle_response(resp)
            except MetaRateLimitError as e:
                if attempt >= max_attempts:
                    raise
                backoff = 10 * (2 ** (attempt - 1))
                time.sleep(backoff)

    def verify_credentials(self) -> dict[str, Any]:
        """
        Validates that Page ID and Page Access Token are valid, active, and have sufficient permissions.
        """
        if not self.config.page_id:
            raise MetaAuthError("META_PAGE_ID is missing. Set it in your .env file or environment.")
        if not self.config.access_token:
            raise MetaAuthError("META_PAGE_ACCESS_TOKEN is missing. Set it in your .env file or environment.")

        url = f"{self.base_url}/{self.config.page_id}"
        params = {
            "fields": "id,name",
            "access_token": self.config.access_token,
        }

        resp = self.session.get(url, params=params, timeout=15)
        data = self._handle_response(resp)

        return {
            "page_id": data.get("id"),
            "page_name": data.get("name"),
            "can_post": True,
            "api_version": self.config.api_version,
        }

    def schedule_single_photo(
        self,
        image_path: Path,
        caption: str,
        scheduled_timestamp: int,
        progress_callback: Callable[[float], None] | None = None,
    ) -> str:
        """
        Schedules a single photo post directly using POST /{page-id}/photos.
        Returns the created Meta Photo ID.
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        url = f"{self.base_url}/{self.config.page_id}/photos"
        mime, _ = mimetypes.guess_type(str(image_path))
        mime = mime or "image/jpeg"

        def _call() -> requests.Response:
            with open(image_path, "rb") as f:
                files = {"source": (image_path.name, f, mime)}
                data = {
                    "message": caption,
                    "published": "false",
                    "scheduled_publish_time": str(scheduled_timestamp),
                    "access_token": self.config.access_token,
                }
                return self.session.post(url, files=files, data=data, timeout=60)

        result = self._execute_with_backoff(_call)
        self._apply_delay(progress_callback)
        return str(result.get("id") or result.get("post_id"))

    def schedule_multi_photo(
        self,
        image_paths: list[Path],
        caption: str,
        scheduled_timestamp: int,
        progress_callback: Callable[[float], None] | None = None,
    ) -> str:
        """
        Schedules a carousel/multi-photo post using the two-step unpublished media container flow.
        1. Uploads each photo as unpublished (`published=false`) to /{page-id}/photos.
        2. Publishes a scheduled feed story to /{page-id}/feed referencing `attached_media`.
        Returns the created Feed Post ID.
        """
        if not image_paths:
            raise ValueError("At least one image is required for multi-photo post.")

        media_ids: list[str] = []

        # Step 1: Upload each image as unpublished photo
        for img in image_paths:
            if not img.exists():
                raise FileNotFoundError(f"Image not found: {img}")

            mime, _ = mimetypes.guess_type(str(img))
            mime = mime or "image/jpeg"
            url_photos = f"{self.base_url}/{self.config.page_id}/photos"

            def _call_photo(p=img, m=mime) -> requests.Response:
                with open(p, "rb") as f:
                    files = {"source": (p.name, f, m)}
                    data = {
                        "published": "false",
                        "temporary": "false",
                        "access_token": self.config.access_token,
                    }
                    return self.session.post(url_photos, files=files, data=data, timeout=60)

            photo_res = self._execute_with_backoff(_call_photo)
            media_id = str(photo_res.get("id"))
            media_ids.append(media_id)
            self._apply_delay(progress_callback)

        # Step 2: Publish scheduled feed story referencing attached media
        url_feed = f"{self.base_url}/{self.config.page_id}/feed"
        feed_data: dict[str, Any] = {
            "message": caption,
            "published": "false",
            "unpublished_content_type": "SCHEDULED",
            "scheduled_publish_time": str(scheduled_timestamp),
            "access_token": self.config.access_token,
        }

        for idx, mid in enumerate(media_ids):
            feed_data[f"attached_media[{idx}]"] = json.dumps({"media_fbid": mid})

        def _call_feed() -> requests.Response:
            return self.session.post(url_feed, data=feed_data, timeout=60)

        feed_res = self._execute_with_backoff(_call_feed)
        self._apply_delay(progress_callback)
        return str(feed_res.get("id"))

    def get_scheduled_posts(self, limit: int = 50) -> list[dict[str, Any]]:
        """Queries Meta's servers for posts currently in the scheduled queue."""
        url = f"{self.base_url}/{self.config.page_id}/scheduled_posts"
        params = {
            "fields": "id,message,created_time,scheduled_publish_time,is_published",
            "limit": str(limit),
            "access_token": self.config.access_token,
        }
        resp = self.session.get(url, params=params, timeout=20)
        data = self._handle_response(resp)
        return data.get("data", [])
