from app import total
from report import render_total


def test_total() -> None:
    assert total(1, 2) == 3


def test_render_total() -> None:
    assert render_total(2, 2) == "total=4"
