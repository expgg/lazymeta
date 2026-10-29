from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from lazymeta.api import MetaClient, MetaAuthError, MetaRateLimitError, MetaApiError
from lazymeta.config import Config


@pytest.fixture
def test_config():
    return Config(
        page_id="100998877",
        access_token="EAAFakeTokenTest",
        api_version="v22.0",
        delay_seconds=0.01,
        delay_jitter=0.0,
    )


def test_verify_credentials_success(test_config):
    client = MetaClient(test_config)
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "100998877",
        "name": "My Test Page",
        "can_post": True,
        "tasks": ["MANAGE", "CREATE_CONTENT"],
    }

    with patch.object(client.session, "get", return_value=mock_resp):
        info = client.verify_credentials()
        assert info["page_id"] == "100998877"
        assert info["page_name"] == "My Test Page"
        assert info["can_post"] is True


def test_verify_credentials_revoked_token(test_config):
    client = MetaClient(test_config)
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "error": {
            "message": "Error validating access token: Session has expired",
            "type": "OAuthException",
            "code": 190,
            "error_subcode": 460,
        }
    }

    with patch.object(client.session, "get", return_value=mock_resp):
        with pytest.raises(MetaAuthError) as exc_info:
            client.verify_credentials()
        assert "Session has expired" in str(exc_info.value)


def test_schedule_single_photo_call(test_config, tmp_path: Path):
    client = MetaClient(test_config)
    fake_img = tmp_path / "test.jpg"
    fake_img.write_bytes(b"image data")

    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "photo_999", "post_id": "post_888"}

    with patch.object(client.session, "post", return_value=mock_resp) as mock_post:
        photo_id = client.schedule_single_photo(
            image_path=fake_img,
            caption="Test single caption",
            scheduled_timestamp=1793523600,
        )
        assert photo_id in ("photo_999", "post_888")
        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["data"]["message"] == "Test single caption"
        assert call_kwargs["data"]["published"] == "false"
        assert call_kwargs["data"]["scheduled_publish_time"] == "1793523600"
