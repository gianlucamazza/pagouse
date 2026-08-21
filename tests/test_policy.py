from __future__ import annotations

import pytest

from pagouse.config import Config
from pagouse.errors import Denied
from pagouse.policy import origin_of, origin_permitted, require_origin, scheme_blocked


def test_scheme_blocks_are_shipped() -> None:
    assert scheme_blocked("chrome://extensions")
    assert scheme_blocked("file:///etc/passwd")
    assert scheme_blocked("about:blank")
    assert scheme_blocked("javascript:alert(1)")
    assert not scheme_blocked("https://example.com/x")
    assert not scheme_blocked("http://localhost:3000/")


def test_empty_allow_list_permits_https() -> None:
    cfg = Config()
    assert origin_permitted("https://example.com/", cfg)


def test_allow_list_is_exact_origin() -> None:
    cfg = Config(allow_origins=("https://example.com",))
    assert origin_permitted("https://example.com/app", cfg)
    assert not origin_permitted("https://other.example.com/", cfg)


def test_deny_list_wins() -> None:
    cfg = Config(deny_origins=("https://my.1password.com",))
    assert not origin_permitted("https://my.1password.com/vault", cfg)
    with pytest.raises(Denied):
        require_origin("https://my.1password.com/vault", cfg)


def test_origin_of_strips_path() -> None:
    assert origin_of("https://example.com:8443/a?b=1") == "https://example.com:8443"
