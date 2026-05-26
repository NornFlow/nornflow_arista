"""Tests for eos_api.helpers."""

import pytest

from nornflow_arista.eos_api.exceptions import EapiConfigError
from nornflow_arista.eos_api.helpers import coerce_port


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        (443, 443),
        ("8080", 8080),
        (1, 1),
        (65535, 65535),
    ],
)
def test_coerce_port_accepts_valid_values(value: object, expected: int | None) -> None:
    assert coerce_port(value) == expected


@pytest.mark.parametrize("value", [0, -1, 65536, 99999])
def test_coerce_port_rejects_out_of_range(value: int) -> None:
    with pytest.raises(EapiConfigError, match="between 1 and 65535"):
        coerce_port(value)


def test_coerce_port_rejects_non_integer() -> None:
    with pytest.raises(EapiConfigError, match="must be an integer"):
        coerce_port("not-a-port")
