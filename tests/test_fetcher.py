"""Tests for the caching / conditional-request behavior in fetcher.py."""
import io
import json
import time
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from gobattlekit.data import fetcher


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    """Point the fetcher at a throwaway cache directory."""
    d = tmp_path / "cache"
    monkeypatch.setattr(fetcher, "CACHE_DIR", d)
    return d


def _make_response(payload, headers=None):
    """Build a fake urlopen() context-manager response."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.headers = headers or {}
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


def test_fresh_cache_skips_network(cache_dir):
    """A cache younger than CACHE_TTL is served without any network call."""
    cache_dir.mkdir(parents=True)
    (cache_dir / "great.json").write_text(json.dumps({"cached": True}))

    with patch("urllib.request.urlopen") as urlopen:
        result = fetcher._fetch_json("great")

    assert result == {"cached": True}
    urlopen.assert_not_called()


def test_stale_cache_200_rewrites_and_stores_validators(cache_dir):
    """A stale cache triggers a download; new data and validators are saved."""
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "great.json"
    meta_file = cache_dir / "great.meta.json"
    cache_file.write_text(json.dumps({"old": True}))
    # Make it stale.
    stale = time.time() - fetcher.CACHE_TTL - 10
    import os
    os.utime(cache_file, (stale, stale))

    resp = _make_response(
        {"new": True},
        headers={"ETag": '"abc"', "Last-Modified": "Wed, 21 Oct 2024 07:28:00 GMT"},
    )
    with patch("urllib.request.urlopen", return_value=resp):
        result = fetcher._fetch_json("great")

    assert result == {"new": True}
    assert json.loads(cache_file.read_text()) == {"new": True}
    validators = json.loads(meta_file.read_text())
    assert validators["etag"] == '"abc"'
    assert validators["last_modified"] == "Wed, 21 Oct 2024 07:28:00 GMT"


def test_stale_cache_sends_conditional_headers(cache_dir):
    """Stored validators are sent as If-None-Match / If-Modified-Since."""
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "great.json"
    meta_file = cache_dir / "great.meta.json"
    cache_file.write_text(json.dumps({"old": True}))
    meta_file.write_text(json.dumps({
        "etag": '"abc"',
        "last_modified": "Wed, 21 Oct 2024 07:28:00 GMT",
    }))
    stale = time.time() - fetcher.CACHE_TTL - 10
    import os
    os.utime(cache_file, (stale, stale))

    resp = _make_response({"new": True})
    with patch("urllib.request.urlopen", return_value=resp) as urlopen:
        fetcher._fetch_json("great")

    request = urlopen.call_args.args[0]
    # urllib normalizes header keys to Capitalized form.
    assert request.get_header("If-none-match") == '"abc"'
    assert request.get_header("If-modified-since") == "Wed, 21 Oct 2024 07:28:00 GMT"


def test_304_refreshes_mtime_and_serves_cache(cache_dir):
    """A 304 response resets the cache mtime and returns the existing cache."""
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "great.json"
    cache_file.write_text(json.dumps({"cached": True}))
    stale = time.time() - fetcher.CACHE_TTL - 10
    import os
    os.utime(cache_file, (stale, stale))

    not_modified = urllib.error.HTTPError(
        url="x", code=304, msg="Not Modified", hdrs=None, fp=io.BytesIO(b""),
    )
    with patch("urllib.request.urlopen", side_effect=not_modified):
        result = fetcher._fetch_json("great")

    assert result == {"cached": True}
    # mtime was reset to ~now, so the cache is considered fresh again.
    assert time.time() - cache_file.stat().st_mtime < fetcher.CACHE_TTL


def test_network_failure_falls_back_to_stale_cache(cache_dir):
    """When the fetch fails outright, the stale cache is still served."""
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "great.json"
    cache_file.write_text(json.dumps({"cached": True}))
    stale = time.time() - fetcher.CACHE_TTL - 10
    import os
    os.utime(cache_file, (stale, stale))

    with patch("urllib.request.urlopen", side_effect=OSError("no network")):
        result = fetcher._fetch_json("great")

    assert result == {"cached": True}


def test_no_cache_and_no_network_raises(cache_dir):
    """With neither cache nor network, NoDataError is raised."""
    with patch("urllib.request.urlopen", side_effect=OSError("no network")):
        with pytest.raises(fetcher.NoDataError):
            fetcher._fetch_json("great")
