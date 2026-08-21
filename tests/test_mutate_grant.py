from __future__ import annotations

import pytest

from pagouse.errors import Readonly
from pagouse.mutate import click


def test_click_without_grant_is_readonly() -> None:
    with pytest.raises(Readonly):
        click("ref_1")
